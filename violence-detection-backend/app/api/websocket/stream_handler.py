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
        self.frame_queue = asyncio.Queue(maxsize=10)
        self.latest_frame = None
        self.processing_task = None
        self.cap = None
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
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, configuracion.DISPLAY_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, configuracion.DISPLAY_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, configuracion.CAMERA_FPS)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        print(f"Cámara {self.source} iniciada: {configuracion.DISPLAY_WIDTH}x{configuracion.DISPLAY_HEIGHT}@{configuracion.CAMERA_FPS}FPS")


    async def process_frames(self):
        """Procesa frames en segundo plano"""
        try:
            print(f"Iniciando procesamiento de frames para cliente {self.cliente_id}")
            while self.deteccion_activada and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    print("No se pudo leer el frame")
                    await asyncio.sleep(0.1)
                    continue

                self.frame_count += 1
                
                # Procesar cada N frames según configuración
                if self.frame_count % configuracion.PROCESS_EVERY_N_FRAMES == 0:
                    try:
                        # Redimensionar para procesamiento
                        frame_proc = cv2.resize(frame.copy(), 
                            (configuracion.YOLO_RESOLUTION_WIDTH, configuracion.YOLO_RESOLUTION_HEIGHT))
                        
                        print(f"Procesando frame {self.frame_count} para cliente {self.cliente_id}")
                        
                        # Procesar frame
                        resultado = await self.pipeline.procesar_frame(
                            frame_proc,
                            camara_id=self.camara_id,
                            ubicacion="Principal"
                        )
                        
                        if resultado:
                            frame_procesado = resultado.get("frame_procesado", frame.copy())
                            self.latest_frame = frame_procesado
                            
                            # Notificar detección
                            if resultado.get("violencia_detectada"):
                                print(f"Violencia detectada para cliente {self.cliente_id}")
                                await self.manejador_webrtc.enviar_a_cliente(
                                    self.cliente_id,
                                    {
                                        "tipo": "deteccion_violencia",
                                        "probabilidad": resultado.get("probabilidad_violencia", 0.0),
                                        "mensaje": "¡ALERTA! Violencia detectada",
                                        "personas_detectadas": len(resultado.get("personas_detectadas", []))
                                    }
                                )
                            
                            # Agregar frame a la cola
                            try:
                                await self.frame_queue.put(frame_procesado)
                            except asyncio.QueueFull:
                                _ = await self.frame_queue.get()
                                await self.frame_queue.put(frame_procesado)
                        
                    except Exception as e:
                        print(f"Error procesando frame {self.frame_count}: {e}")
                    
                await asyncio.sleep(1/configuracion.CAMERA_FPS)
                    
        except Exception as e:
            print(f"Error en process_frames: {e}")
            import traceback
            print(traceback.format_exc())
        finally:
            print(f"Tarea de procesamiento finalizada para cliente {self.cliente_id}")
    
    def start_processing(self):
        """Inicia la tarea de procesamiento en segundo plano"""
        if not self.processing_task or self.processing_task.done():
            self.deteccion_activada = True
            self.processing_task = asyncio.create_task(self.process_frames())
            print("Tarea de procesamiento iniciada")
            
    def stop_processing(self):
        """Detiene la tarea de procesamiento"""
        self.deteccion_activada = False
        if self.processing_task:
            self.processing_task.cancel()
        print("Tarea de procesamiento detenida")
    
    async def recv(self):
        try:
            pts, time_base = await self.next_timestamp()

            if self.cap is None or not self.cap.isOpened():
                self._start()

            frame_procesado = None
            
            # Intentar obtener frame procesado de la cola
            if self.deteccion_activada:
                try:
                    frame_procesado = await asyncio.wait_for(
                        self.frame_queue.get(), 
                        timeout=1/configuracion.CAMERA_FPS
                    )
                except (asyncio.TimeoutError, asyncio.QueueEmpty):
                    pass

            # Si no hay frame procesado, usar frame directo
            if frame_procesado is None:
                ret, frame = self.cap.read()
                if not ret:
                    print("No se pudo leer el frame")
                    return None
                frame_procesado = frame

            # Convertir y retornar frame
            frame_rgb = cv2.cvtColor(frame_procesado, cv2.COLOR_BGR2RGB)
            video_frame = av.VideoFrame.from_ndarray(frame_rgb, format="rgb24")
            video_frame.pts = pts
            video_frame.time_base = time_base

            return video_frame

        except Exception as e:
            print(f"Error en recv: {e}")
            return None

    def stop(self):
        self.stop_processing()
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

            @pc.on("negotiationneeded")
            async def on_negotiationneeded():
                print(f"Negociación necesaria para cliente {cliente_id}")

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
