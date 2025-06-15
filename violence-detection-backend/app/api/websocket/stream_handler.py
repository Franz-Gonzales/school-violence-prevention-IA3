import cv2
import asyncio
from typing import Optional, Dict, Any
import av
from app.ai.model_loader import cargador_modelos
from app.ai.pipeline import PipelineDeteccion
from app.config import configuracion
from app.utils.logger import obtener_logger
from app.api.websocket.common import ManejadorWebRTC, manejador_webrtc
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer
from app.ai.yolo_detector import DetectorPersonas
from app.ai.violence_detector import DetectorViolencia
from app.services.alarm_service import ServicioAlarma
from app.services.notification_service import ServicioNotificaciones
from app.services.incident_service import ServicioIncidentes
import numpy as np
import socket
from asyncio import Queue
import time
import threading
from datetime import datetime

logger = obtener_logger(__name__)

class VideoTrackProcesado(VideoStreamTrack):
    def __init__(self, source, pipeline, manejador_webrtc, cliente_id, camara_id, deteccion_activada=False):
        super().__init__()
        self.source = source
        self.pipeline = pipeline
        self.manejador_webrtc = manejador_webrtc
        self.cliente_id = cliente_id
        self.camara_id = camara_id
        self.deteccion_activada = deteccion_activada
        self.frame_count = 0
        
        # Colas separadas para streaming y procesamiento MEJORADAS
        self.stream_queue = asyncio.Queue(maxsize=5)  # Cola para streaming (más pequeña)
        self.processing_queue = asyncio.Queue(maxsize=50)  # Cola más grande para procesamiento
        
        # Control de tiempo
        self.last_frame_time = time.time()
        self.target_fps = configuracion.CAMERA_FPS
        self.frame_interval = 1.0 / self.target_fps
        
        # Dimensiones fijas para consistencia
        self.stream_width = configuracion.DISPLAY_WIDTH
        self.stream_height = configuracion.DISPLAY_HEIGHT
        
        self.cap = None
        self.capture_thread = None
        self.processing_task = None
        self.running = True
        
        # NUEVO: Estado de violencia para captura intensiva
        self.violence_mode = False
        self.last_violence_detection = 0
        
        self._start()
        
        # Iniciar procesamiento si está activado
        if deteccion_activada:
            self.start_processing()
        
    def _start(self):
        """Inicializa la captura de video con DirectShow"""
        print(f"Iniciando cámara {self.source} con DirectShow...")
        self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara {self.source} con DirectShow")
        
        # Configurar cámara con resolución fija
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.stream_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.stream_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimizar buffer
        
        print(f"Cámara {self.source} configurada: {self.stream_width}x{self.stream_height}@{self.target_fps}FPS")
        
        # Iniciar hilo de captura
        self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        self.capture_thread.start()

    def _capture_frames(self):
        """Hilo dedicado para captura de frames OPTIMIZADO PARA VIOLENCIA"""
        last_capture_time = time.time()
        
        # CAPTURA ADAPTATIVA SEGÚN MODO DE VIOLENCIA
        base_capture_interval = 1.0 / 30  # 30 FPS base
        violence_capture_interval = 1.0 / 40  # 40 FPS durante violencia
        
        while self.running and self.cap and self.cap.isOpened():
            current_time = time.time()
            
            # AJUSTAR FRECUENCIA SEGÚN MODO DE VIOLENCIA
            if self.violence_mode:
                capture_interval = violence_capture_interval
            else:
                capture_interval = base_capture_interval
            
            if current_time - last_capture_time < capture_interval:
                time.sleep(0.001)
                continue
                
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            
            # Asegurar dimensiones consistentes
            if frame.shape[:2] != (self.stream_height, self.stream_width):
                frame = cv2.resize(frame, (self.stream_width, self.stream_height))
            
            frame_data = {
                'frame': frame.copy(),
                'timestamp': current_time,
                'frame_id': self.frame_count,
                'violence_mode': self.violence_mode
            }
            
            # PRIORIDAD MÁXIMA PARA FRAMES DURANTE VIOLENCIA
            if self.deteccion_activada:
                try:
                    # Durante violencia: forzar agregar frames
                    if self.violence_mode:
                        # Limpiar cola si está llena y agregar frame importante
                        if self.processing_queue.full():
                            try:
                                self.processing_queue.get_nowait()
                            except:
                                pass
                        self.processing_queue.put_nowait(frame_data)
                    else:
                        # Modo normal
                        self.processing_queue.put_nowait(frame_data)
                except asyncio.QueueFull:
                    # Solo en modo normal, descartar frames si la cola está llena
                    if not self.violence_mode:
                        try:
                            self.processing_queue.get_nowait()
                            self.processing_queue.put_nowait(frame_data)
                        except:
                            pass
            
            # Cola de streaming (menor prioridad)
            try:
                self.stream_queue.put_nowait(frame_data)
            except asyncio.QueueFull:
                try:
                    self.stream_queue.get_nowait()
                    self.stream_queue.put_nowait(frame_data)
                except:
                    pass
            
            self.frame_count += 1
            last_capture_time = current_time
    
    # *** NUEVO MÉTODO PARA OBTENER UBICACIÓN DE LA CÁMARA ***
    async def _obtener_ubicacion_camara(self, camara_id: int) -> str:
        """Obtiene la ubicación de la cámara desde la base de datos"""
        try:
            from app.core.database import SesionAsincrona
            from app.models.camera import Camara
            from sqlalchemy import select
            
            async with SesionAsincrona() as session:
                resultado = await session.execute(
                    select(Camara.ubicacion).where(Camara.id == camara_id)
                )
                ubicacion = resultado.scalar()
                
                return ubicacion or f"Cámara {camara_id}"
                
        except Exception as e:
            print(f"Error obteniendo ubicación de cámara {camara_id}: {e}")
            return f"Cámara {camara_id}"

    async def process_frames(self):
        """CORREGIDO: Procesamiento que preserva TODA la secuencia de violencia"""
        try:
            print(f"Iniciando procesamiento MEJORADO de frames para cliente {self.cliente_id}")
            last_process_time = time.time()
            frames_sin_violencia = 0
            limpieza_programada = False
            
            # *** NUEVO: Control de secuencia activa ***
            secuencia_violencia_activa = False
            frames_secuencia_procesados = 0
            
            while self.deteccion_activada and self.running:
                try:
                    frame_data = await asyncio.wait_for(
                        self.processing_queue.get(), 
                        timeout=0.1
                    )
                    
                    frame = frame_data['frame']
                    frame_id = frame_data['frame_id']
                    current_time = time.time()
                    
                    # *** CORRECCIÓN: Procesamiento adaptativo MEJORADO ***
                    should_process = False
                    
                    if self.violence_mode or secuencia_violencia_activa:
                        should_process = (frame_id % 1 == 0)  # *** CADA frame durante violencia ***
                    else:
                        should_process = (frame_id % configuracion.PROCESS_EVERY_N_FRAMES == 0)
                    
                    if should_process and (current_time - last_process_time >= 0.05):  # *** REDUCIDO tiempo mínimo ***
                        try:
                            frame_proc = await asyncio.get_event_loop().run_in_executor(
                                None, 
                                lambda: cv2.resize(
                                    frame.copy(), 
                                    (configuracion.YOLO_RESOLUTION_WIDTH, configuracion.YOLO_RESOLUTION_HEIGHT)
                                )
                            )
                            
                            print(f"Procesando frame {frame_id} para cliente {self.cliente_id}")
                            
                            ubicacion_camara = await self._obtener_ubicacion_camara(self.camara_id)
                            
                            # *** PROCESAR FRAME CON PIPELINE CORREGIDO ***
                            resultado = await self.pipeline.procesar_frame(
                                frame_proc,
                                camara_id=self.camara_id,
                                ubicacion=ubicacion_camara
                            )
                            
                            if resultado and resultado.get("violencia_detectada"):
                                print(f"✅ Violencia detectada para cliente {self.cliente_id}")
                                
                                # *** ACTIVAR MODO VIOLENCIA Y SECUENCIA ***
                                self.violence_mode = True
                                secuencia_violencia_activa = True
                                self.last_violence_detection = current_time
                                frames_sin_violencia = 0
                                frames_secuencia_procesados = 0
                                limpieza_programada = False
                                
                                probabilidad_real = (
                                    resultado.get("probabilidad_violencia") or
                                    resultado.get("probabilidad") or 
                                    0.0
                                )
                                
                                personas_detectadas = len(resultado.get("personas_detectadas", []))
                                
                                # *** MENSAJE CORREGIDO con información de secuencia ***
                                mensaje_notificacion = {
                                    "tipo": "deteccion_violencia",
                                    "probabilidad": float(probabilidad_real),
                                    "probability": float(probabilidad_real),
                                    "probabilidad_violencia": float(probabilidad_real),
                                    "mensaje": f"¡ALERTA! Violencia detectada - {probabilidad_real:.1%}",
                                    "personas_detectadas": int(personas_detectadas),
                                    "peopleCount": int(personas_detectadas),
                                    "ubicacion": str(ubicacion_camara),
                                    "location": str(ubicacion_camara),
                                    "timestamp": datetime.now().isoformat(),
                                    "camara_id": self.camara_id,
                                    "violencia_detectada": True,
                                    "frames_analizados": resultado.get("frames_analizados", 8),  # *** NUEVO ***
                                    "secuencia_activa": True  # *** NUEVO ***
                                }
                                
                                print(f"📤 ENVIANDO MENSAJE CORREGIDO: {mensaje_notificacion}")
                                
                                await self.manejador_webrtc.enviar_a_cliente(
                                    self.cliente_id,
                                    mensaje_notificacion
                                )
                                
                            else:
                                # *** CORRECCIÓN: Manejo de frames de secuencia sin violencia confirmada ***
                                frames_sin_violencia += 1
                                frames_secuencia_procesados += 1
                                
                                # *** ENVIAR ACTUALIZACIÓN DE SECUENCIA EN ANÁLISIS ***
                                if secuencia_violencia_activa and frames_secuencia_procesados < 15:  # Mantener secuencia por más tiempo
                                    mensaje_secuencia = {
                                        "tipo": "secuencia_analisis",
                                        "probabilidad": resultado.get("probabilidad_violencia", 0.0),
                                        "probability": resultado.get("probabilidad_violencia", 0.0),
                                        "mensaje": f"Analizando secuencia... ({frames_secuencia_procesados}/15)",
                                        "personas_detectadas": len(resultado.get("personas_detectadas", [])),
                                        "ubicacion": str(ubicacion_camara),
                                        "timestamp": datetime.now().isoformat(),
                                        "camara_id": self.camara_id,
                                        "violencia_detectada": False,
                                        "secuencia_activa": True,
                                        "frames_procesados": frames_secuencia_procesados
                                    }
                                    
                                    await self.manejador_webrtc.enviar_a_cliente(
                                        self.cliente_id,
                                        mensaje_secuencia
                                    )
                                
                                # *** FINALIZAR SECUENCIA después de más frames ***
                                if secuencia_violencia_activa and frames_secuencia_procesados >= 15:
                                    secuencia_violencia_activa = False
                                    print(f"🔄 Secuencia de análisis finalizada para cliente {self.cliente_id}")
                                
                                # *** PROGRAMAR LIMPIEZA después de suficiente tiempo ***
                                if self.violence_mode and frames_sin_violencia > 25 and not limpieza_programada:  # *** AUMENTADO: ~2 segundos ***
                                    print(f"⏰ Programando limpieza de alerta para cliente {self.cliente_id}")
                                    asyncio.create_task(self._limpiar_alerta_violencia(6))  # *** AUMENTADO: 6 segundos ***
                                    limpieza_programada = True
                                
                                # *** DESACTIVAR MODO VIOLENCIA después de más tiempo ***
                                if self.violence_mode and frames_sin_violencia > 60:  # *** AUMENTADO: ~4 segundos ***
                                    self.violence_mode = False
                                    print(f"🔄 Modo violencia desactivado para cliente {self.cliente_id}")
                            
                            last_process_time = current_time
                            
                        except Exception as e:
                            print(f"❌ Error procesando frame {frame_id}: {e}")
                            import traceback
                            print(traceback.format_exc())
                    
                    # *** PAUSA ADAPTATIVA CORREGIDA ***
                    if self.violence_mode or secuencia_violencia_activa:
                        await asyncio.sleep(0.001)  # Procesamiento muy rápido durante análisis
                    else:
                        await asyncio.sleep(0.008)  # Procesamiento normal
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"❌ Error en process_frames: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Error en process_frames: {e}")
            import traceback
            print(traceback.format_exc())
        finally:
            print(f"Tarea de procesamiento MEJORADO finalizada para cliente {self.cliente_id}")

    # *** NUEVO MÉTODO PARA OBTENER UBICACIÓN DE LA CÁMARA ***
    async def _obtener_ubicacion_camara(self, camara_id: int) -> str:
        """Obtiene la ubicación de la cámara desde la base de datos"""
        try:
            from app.core.database import SesionAsincrona
            from app.models.camera import Camara
            from sqlalchemy import select
            
            async with SesionAsincrona() as session:
                resultado = await session.execute(
                    select(Camara.ubicacion).where(Camara.id == camara_id)
                )
                ubicacion = resultado.scalar()
                
                return ubicacion or f"Cámara {camara_id}"
                
        except Exception as e:
            print(f"Error obteniendo ubicación de cámara {camara_id}: {e}")
            return f"Cámara {camara_id}"
    
    def start_processing(self):
        """Inicia la tarea de procesamiento en segundo plano"""
        if not self.processing_task or self.processing_task.done():
            self.deteccion_activada = True
            self.processing_task = asyncio.create_task(self.process_frames())
            print("Tarea de procesamiento iniciada")
            
    def stop_processing(self):
        """Detiene la tarea de procesamiento"""
        self.deteccion_activada = False
        self.violence_mode = False
        if self.processing_task:
            self.processing_task.cancel()
        print("Tarea de procesamiento detenida")
    
    async def recv(self):
        """Recibe frames para streaming WebRTC"""
        try:
            pts, time_base = await self.next_timestamp()

            if not self.running or not self.cap or not self.cap.isOpened():
                return None

            # Control de timing para FPS consistente
            current_time = time.time()
            time_since_last = current_time - self.last_frame_time
            
            if time_since_last < self.frame_interval:
                await asyncio.sleep(self.frame_interval - time_since_last)

            # Obtener frame de la cola de streaming
            try:
                frame_data = await asyncio.wait_for(
                    self.stream_queue.get(), 
                    timeout=self.frame_interval * 2
                )
                frame = frame_data['frame']
            except asyncio.TimeoutError:
                # Si no hay frame, usar frame negro
                print("Timeout obteniendo frame para streaming")
                frame = np.zeros((self.stream_height, self.stream_width, 3), dtype=np.uint8)

            # Asegurar dimensiones consistentes
            if frame.shape[:2] != (self.stream_height, self.stream_width):
                frame = cv2.resize(frame, (self.stream_width, self.stream_height))

            # Convertir a RGB para WebRTC
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Crear video frame con timestamps consistentes
            video_frame = av.VideoFrame.from_ndarray(frame_rgb, format="rgb24")
            video_frame.pts = pts
            video_frame.time_base = time_base

            self.last_frame_time = time.time()
            return video_frame

        except Exception as e:
            print(f"Error en recv: {e}")
            return None
    
    async def _limpiar_alerta_violencia(self, delay_seconds: int = 5):
        """Limpia la alerta de violencia después de un delay"""
        await asyncio.sleep(delay_seconds)
        
        # Verificar si aún no hay violencia después del delay
        current_time = time.time()
        if not self.violence_mode or (current_time - self.last_violence_detection) > delay_seconds:
            try:
                # Enviar mensaje de limpieza de violencia
                mensaje_limpieza = {
                    "tipo": "deteccion_violencia_fin",
                    "violencia_detectada": False,
                    "probabilidad": 0.0,
                    "probability": 0.0,
                    "probabilidad_violencia": 0.0,
                    "mensaje": "Alerta de violencia finalizada",
                    "personas_detectadas": 0,
                    "peopleCount": 0,
                    "ubicacion": await self._obtener_ubicacion_camara(self.camara_id),
                    "location": await self._obtener_ubicacion_camara(self.camara_id),
                    "timestamp": datetime.now().isoformat(),
                    "camara_id": self.camara_id,
                    "limpiar_alerta": True
                }
                
                print(f"🧹 Limpiando alerta de violencia para cliente {self.cliente_id}")
                await self.manejador_webrtc.enviar_a_cliente(
                    self.cliente_id,
                    mensaje_limpieza
                )
                
            except Exception as e:
                print(f"❌ Error limpiando alerta de violencia: {e}")

    def stop(self):
        """Detiene todos los procesos"""
        self.running = False
        self.violence_mode = False
        self.stop_processing()
        
        # Esperar a que termine el hilo de captura
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)
        
        if self.cap:
            self.cap.release()
            self.cap = None
            
        print("Recursos de captura liberados")


class ManejadorStreaming:
    def __init__(self):
        self.conexiones_peer: Dict[str, RTCPeerConnection] = {}
        self.pipelines: Dict[str, PipelineDeteccion] = {}
        self.deteccion_activada: Dict[str, bool] = {}
        self.servicio_alarma = ServicioAlarma()

    def get_valid_ip_addresses(self):
        """Obtiene direcciones IP válidas, excluyendo 169.254.x.x"""
        valid_ips = []
        for interface in socket.getaddrinfo(socket.gethostname(), None):
            ip = interface[4][0]
            if not ip.startswith('169.254.') and ip not in ('127.0.0.1', '::1'):
                valid_ips.append(ip)
        return valid_ips

    async def crear_conexion_peer(
        self,
        cliente_id: str,
        camara_id: int,
        manejador_webrtc: ManejadorWebRTC,
        deteccion_activada: bool = False
    ) -> RTCPeerConnection:
        try:
            if cliente_id in self.conexiones_peer:
                await self.cerrar_conexion(cliente_id)

            valid_ips = self.get_valid_ip_addresses()
            config = RTCConfiguration(
                iceServers=[RTCIceServer(urls=[configuracion.STUN_SERVER])]
            )

            pc = RTCPeerConnection(configuration=config)
            self.conexiones_peer[cliente_id] = pc
            self.deteccion_activada[cliente_id] = deteccion_activada

            if cliente_id not in self.pipelines:
                self.pipelines[cliente_id] = await self.crear_pipeline(cliente_id)

            video_track = VideoTrackProcesado(
                source=configuracion.CAMERA_INDEX,
                pipeline=self.pipelines[cliente_id],
                manejador_webrtc=manejador_webrtc,
                cliente_id=cliente_id,
                camara_id=camara_id,
                deteccion_activada=deteccion_activada
            )
            pc.addTrack(video_track)

            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                print(f"Estado de conexión {cliente_id}: {pc.connectionState}")
                if pc.connectionState == "failed":
                    await self.cerrar_conexion(cliente_id)

            return pc

        except Exception as e:
            print(f"Error al crear conexión peer: {str(e)}")
            await self.cerrar_conexion(cliente_id)
            raise

    async def manejar_offer(
        self,
        cliente_id: str,
        sdp: str, 
        camara_id: int,
        manejador_webrtc: ManejadorWebRTC,
        deteccion_activada: bool = False
    ) -> str:
        try:
            if not sdp:
                raise ValueError("SDP no puede estar vacío")

            pc = await self.crear_conexion_peer(
                cliente_id, 
                camara_id, 
                manejador_webrtc, 
                deteccion_activada
            )

            offer = RTCSessionDescription(sdp=sdp, type="offer")
            await pc.setRemoteDescription(offer)

            answer = await pc.createAnswer()
            if not answer:
                raise ValueError("No se pudo crear respuesta")

            await pc.setLocalDescription(answer)

            if not pc.localDescription or not pc.localDescription.sdp:
                raise ValueError("SDP de respuesta vacío")

            print(f"Respuesta SDP creada para cliente {cliente_id}")
            return pc.localDescription.sdp

        except Exception as e:
            print(f"Error en manejar_offer: {str(e)}")
            await self.cerrar_conexion(cliente_id)
            raise

    async def cerrar_conexion(self, cliente_id: str):
        try:
            if cliente_id in self.conexiones_peer:
                pc = self.conexiones_peer[cliente_id]
                
                # Detener tracks antes de cerrar
                for sender in pc.getSenders():
                    if sender.track and hasattr(sender.track, 'stop'):
                        sender.track.stop()
                
                await pc.close()
                del self.conexiones_peer[cliente_id]
            
            if cliente_id in self.pipelines:
                self.pipelines[cliente_id].reiniciar()
                del self.pipelines[cliente_id]
            
            if cliente_id in self.deteccion_activada:
                del self.deteccion_activada[cliente_id]
            
            print(f"Conexión cerrada para cliente {cliente_id}")
            
        except Exception as e:
            print(f"Error al cerrar conexión: {e}")

    async def crear_pipeline(self, cliente_id: str) -> PipelineDeteccion:
        try:
            from app.core.database import SesionAsincrona
            db = SesionAsincrona()
            
            detector_personas = DetectorPersonas(cargador_modelos.obtener_modelo('yolo'))
            detector_violencia = DetectorViolencia()
            servicio_incidentes = ServicioIncidentes(db)
            servicio_notificaciones = ServicioNotificaciones(db)

            pipeline = PipelineDeteccion(
                detector_personas=detector_personas,
                detector_violencia=detector_violencia,
                servicio_alarma=self.servicio_alarma,
                servicio_notificaciones=servicio_notificaciones,
                servicio_incidentes=servicio_incidentes,
                session=db
            )

            print(f"Pipeline creado para cliente {cliente_id}")
            return pipeline

        except Exception as e:
            print(f"Error creando pipeline: {e}")
            raise

    async def activar_deteccion(self, cliente_id: str, camara_id: int):
        try:
            if cliente_id in self.deteccion_activada:
                self.deteccion_activada[cliente_id] = True
                print(f"Detección activada para cliente {cliente_id}")

                if cliente_id in self.pipelines:
                    self.pipelines[cliente_id].reiniciar()
                
                if cliente_id in self.conexiones_peer:
                    for sender in self.conexiones_peer[cliente_id].getSenders():
                        if isinstance(sender.track, VideoTrackProcesado):
                            sender.track.start_processing()

        except Exception as e:
            print(f"Error al activar detección: {e}")

    async def desactivar_deteccion(self, cliente_id: str, camara_id: int):
        try:
            if cliente_id in self.deteccion_activada:
                self.deteccion_activada[cliente_id] = False
                print(f"Detección desactivada para cliente {cliente_id}")
                
                if cliente_id in self.pipelines:
                    self.pipelines[cliente_id].reiniciar()
                
                if cliente_id in self.conexiones_peer:
                    for sender in self.conexiones_peer[cliente_id].getSenders():
                        if isinstance(sender.track, VideoTrackProcesado):
                            sender.track.stop_processing()

        except Exception as e:
            print(f"Error al desactivar detección: {e}")

manejador_streaming = ManejadorStreaming()