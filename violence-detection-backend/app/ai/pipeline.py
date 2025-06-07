import cv2
import numpy as np
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
from app.ai.yolo_detector import DetectorPersonas
from app.ai.violence_detector import DetectorViolencia
from app.services.alarm_service import ServicioAlarma
from app.services.notification_service import ServicioNotificaciones
from app.services.incident_service import ServicioIncidentes
from app.models.incident import TipoIncidente, SeveridadIncidente, EstadoIncidente
from app.utils.video_utils import ProcesadorVideo
from app.utils.logger import obtener_logger
from app.config import configuracion
from app.tasks.video_recorder import evidence_recorder
from sqlalchemy.ext.asyncio import AsyncSession
import os
import threading
import queue
import time

logger = obtener_logger(__name__)

class FrameBuffer:
    """Buffer inteligente para frames con timestamps precisos"""
    def __init__(self, max_duration_seconds=10):
        self.frames = deque()
        self.max_duration = max_duration_seconds
        
    def add_frame(self, frame, timestamp, detecciones=None, violencia_info=None):
        """Agrega un frame con timestamp preciso y información de violencia"""
        frame_data = {
            'frame': frame.copy(),
            'timestamp': timestamp,
            'detecciones': detecciones or [],
            'violencia_info': violencia_info,  # Nueva información de violencia
            'processed': False
        }
        self.frames.append(frame_data)
        
        # Limpiar frames antiguos
        current_time = timestamp
        while self.frames and (current_time - self.frames[0]['timestamp']).total_seconds() > self.max_duration:
            self.frames.popleft()
    
    def get_frames_in_range(self, start_time, end_time):
        """Obtiene frames en un rango de tiempo específico"""
        return [f for f in self.frames 
                if start_time <= f['timestamp'] <= end_time]
    
    def get_recent_frames(self, duration_seconds):
        """Obtiene frames recientes basado en duración"""
        if not self.frames:
            return []
        
        latest_time = self.frames[-1]['timestamp']
        start_time = latest_time - timedelta(seconds=duration_seconds)
        return self.get_frames_in_range(start_time, latest_time)

class PipelineDeteccion:
    def __init__(
        self,
        detector_personas: DetectorPersonas,
        detector_violencia: DetectorViolencia,
        servicio_alarma: ServicioAlarma,
        servicio_notificaciones: ServicioNotificaciones,
        servicio_incidentes: ServicioIncidentes,
        session: AsyncSession
    ):
        self.detector_personas = detector_personas
        self.detector_violencia = detector_violencia
        self.servicio_alarma = servicio_alarma
        self.servicio_notificaciones = servicio_notificaciones
        self.servicio_incidentes = servicio_incidentes
        self.session = session
        
        self.procesador_video = ProcesadorVideo()
        self.activo = False
        self.camara_id = None
        self.ubicacion = None
        
        # Buffer inteligente para evidencia
        self.buffer_evidencia = FrameBuffer(max_duration_seconds=15)
        
        # Control de grabación de evidencia mejorado
        self.grabando_evidencia = False
        self.tiempo_inicio_violencia = None
        self.tiempo_fin_violencia = None
        self.duracion_evidencia_pre = 3  # 3 segundos antes del incidente
        self.duracion_evidencia_post = 5  # 5 segundos después del incidente
        
        # Cola para guardar videos de forma asíncrona
        self.cola_guardado = queue.Queue()
        self.hilo_guardado = threading.Thread(target=self._procesar_cola_guardado, daemon=True)
        self.hilo_guardado.start()
        
        # Estadísticas
        self.frames_procesados = 0
        self.incidentes_detectados = 0
        
        # Control de tiempo para evitar spam
        self.ultimo_incidente = 0
        self.cooldown_incidente = 5  # 5 segundos entre incidentes
        
        # FPS target para evidencia - CORREGIDO PARA VIDEO FLUIDO
        self.target_fps_evidencia = 15

        # Control mejorado para evidencia
        self.frame_feed_interval = 1.0 / 25  # Alimentar buffer a 20 FPS
        self.last_evidence_feed = 0

        # Inicializar recorder de evidencia
        evidence_recorder.start_processing()

    async def procesar_frame(self, frame: np.ndarray, camara_id: int, ubicacion: str) -> Dict[str, Any]:
        try:
            self.camara_id = camara_id
            self.ubicacion = ubicacion
            self.frames_procesados += 1
            
            # Timestamp preciso para este frame
            timestamp_actual = datetime.now()
            
            # Crear copia del frame original con dimensiones consistentes
            frame_original = frame.copy()
            altura_original, ancho_original = frame_original.shape[:2]
            
            # Detección de personas con YOLO (asíncrona)
            detecciones = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.detector_personas.detectar, 
                frame_original
            )
            
            # Crear frame procesado para display
            frame_procesado = frame_original.copy()
            
            # Dibujar bounding boxes de forma asíncrona
            if detecciones:
                frame_procesado = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._dibujar_detecciones,
                    frame_procesado,
                    detecciones
                )

            resultado = {
                'frame_procesado': frame_procesado,
                'personas_detectadas': detecciones,
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0,
                'timestamp': timestamp_actual
            }

            # Variable para información de violencia
            violencia_info = None

            # Solo procesar con TimesFormer si hay personas detectadas
            if detecciones:
                # Agregar frame para detección de violencia
                self.detector_violencia.agregar_frame(frame_original.copy())
                
                # Procesar cada N frames
                if self.frames_procesados % configuracion.TIMESFORMER_CONFIG["num_frames"] == 0:
                    # Detección de violencia de forma asíncrona
                    deteccion = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.detector_violencia.detectar
                    )
                    
                    resultado.update(deteccion)

                    if deteccion['violencia_detectada']:
                        current_time = timestamp_actual.timestamp()
                        
                        # Preparar información de violencia para el frame
                        violencia_info = {
                            'detectada': True,
                            'probabilidad': deteccion.get('probabilidad', 0.0),
                            'timestamp': timestamp_actual
                        }
                        
                        # Control de cooldown para evitar múltiples incidentes
                        if current_time - self.ultimo_incidente > self.cooldown_incidente:
                            # Marcar inicio de violencia
                            if not self.grabando_evidencia:
                                self.tiempo_inicio_violencia = timestamp_actual
                                self.grabando_evidencia = True
                                print(f"🚨 INICIO DE VIOLENCIA DETECTADA: {self.tiempo_inicio_violencia}")
                            
                            # Activar alarma de forma asíncrona
                            asyncio.create_task(self._activar_alarma())
                            
                            # Agregar alerta al frame CON PROBABILIDAD CORRECTA
                            probabilidad_texto = f"¡ALERTA! Violencia detectada ({deteccion.get('probabilidad', 0.0):.1%})"
                            frame_procesado = await asyncio.get_event_loop().run_in_executor(
                                None,
                                self.procesador_video.agregar_texto_alerta,
                                frame_procesado,
                                probabilidad_texto,
                                (0, 0, 255),
                                1.2
                            )
                            
                            resultado['frame_procesado'] = frame_procesado
                            
                            # Crear incidente si es el primer frame de violencia
                            if not hasattr(self, 'incidente_actual_id'):
                                asyncio.create_task(self._crear_incidente(detecciones, deteccion.get('probabilidad', 0.0)))
                                self.ultimo_incidente = current_time
                            
                            # Actualizar tiempo de fin de violencia
                            self.tiempo_fin_violencia = timestamp_actual
                    else:
                        # Si no hay violencia y estábamos grabando, finalizar después de un delay
                        if self.grabando_evidencia and self.tiempo_fin_violencia:
                            tiempo_transcurrido = (timestamp_actual - self.tiempo_fin_violencia).total_seconds()
                            if tiempo_transcurrido >= self.duracion_evidencia_post:
                                await self._finalizar_grabacion_evidencia()

            # Agregar frame al buffer de evidencia (SIEMPRE con timestamp preciso)
            # INCLUIR INFORMACIÓN DE VIOLENCIA EN EL BUFFER
            self.buffer_evidencia.add_frame(
                frame_procesado, 
                timestamp_actual, 
                detecciones,
                violencia_info  # Información de violencia para overlay en video
            )

            # ALIMENTAR EL BUFFER DE EVIDENCIA MÁS FRECUENTEMENTE
            current_time = time.time()
            if current_time - self.last_evidence_feed >= self.frame_feed_interval:
                evidence_recorder.add_frame(frame_original, detecciones, violencia_info)
                self.last_evidence_feed = current_time
            
            return resultado

        except Exception as e:
            print(f"Error en pipeline: {str(e)}")
            return {
                'frame_procesado': frame,
                'personas_detectadas': [],
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0,
                'timestamp': datetime.now()
            }

    def _dibujar_detecciones(self, frame: np.ndarray, detecciones: List[Dict]) -> np.ndarray:
        """Dibuja las detecciones en el frame"""
        for deteccion in detecciones:
            frame = self.procesador_video.dibujar_bounding_box(
                frame,
                deteccion['bbox'],
                label=f"Persona ({deteccion['confianza']:.2f})"
            )
        return frame

    async def _finalizar_grabacion_evidencia(self):
        """Finaliza la grabación y envía a la cola de guardado con timestamps precisos"""
        if not self.tiempo_inicio_violencia:
            return
            
        print(f"📹 Finalizando grabación de evidencia...")
        
        # Calcular tiempos para el clip de evidencia
        tiempo_inicio_clip = self.tiempo_inicio_violencia - timedelta(seconds=self.duracion_evidencia_pre)
        tiempo_fin_clip = self.tiempo_fin_violencia + timedelta(seconds=self.duracion_evidencia_post)
        
        # Obtener frames del rango de tiempo específico
        frames_evidencia = self.buffer_evidencia.get_frames_in_range(
            tiempo_inicio_clip, 
            tiempo_fin_clip
        )
        
        if frames_evidencia:
            print(f"📹 Extraídos {len(frames_evidencia)} frames para evidencia")
            print(f"📹 Duración del clip: {(tiempo_fin_clip - tiempo_inicio_clip).total_seconds():.2f} segundos")
            
            # Enviar a cola de guardado asíncrono
            datos_guardado = {
                'frames': frames_evidencia,
                'camara_id': self.camara_id,
                'tiempo_inicio': tiempo_inicio_clip,
                'tiempo_fin': tiempo_fin_clip,
                'incidente_id': getattr(self, 'incidente_actual_id', None),
                'fps_target': self.target_fps_evidencia
            }
            
            try:
                self.cola_guardado.put_nowait(datos_guardado)
                print("📹 Evidencia enviada a cola de guardado")
            except queue.Full:
                print("❌ Cola de guardado llena, descartando video")
        
        # Limpiar estado
        self.grabando_evidencia = False
        self.tiempo_inicio_violencia = None
        self.tiempo_fin_violencia = None
        if hasattr(self, 'incidente_actual_id'):
            delattr(self, 'incidente_actual_id')

    def _procesar_cola_guardado(self):
        """Procesa la cola de guardado en hilo separado"""
        while True:
            try:
                datos = self.cola_guardado.get(timeout=1)
                self._guardar_evidencia_con_fps_correcto(datos)
                self.cola_guardado.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error en hilo de guardado: {e}")

    def _guardar_evidencia_con_fps_correcto(self, datos: Dict[str, Any]):
        """Guarda evidencia con FPS correcto basado en timestamps reales - MEJORADO"""
        try:
            frames_data = datos['frames']
            camara_id = datos['camara_id']
            tiempo_inicio = datos['tiempo_inicio']
            fps_target = datos['fps_target']
            incidente_id = datos.get('incidente_id')
            
            if not frames_data:
                print("❌ No hay frames para guardar evidencia")
                return

            # Crear directorio
            ruta_base = configuracion.VIDEO_EVIDENCE_PATH / "clips"
            ruta_base.mkdir(parents=True, exist_ok=True)

            # Generar nombre de archivo con timestamp
            timestamp_str = tiempo_inicio.strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"evidencia_camara{camara_id}_{timestamp_str}.mp4"
            ruta_evidencia = ruta_base / nombre_archivo

            # Obtener dimensiones del primer frame
            primer_frame = frames_data[0]['frame']
            height, width = primer_frame.shape[:2]
            
            print(f"📹 Guardando video: {nombre_archivo}")
            print(f"📹 Dimensiones: {width}x{height}")
            print(f"📹 FPS objetivo: {fps_target}")
            
            # USAR CODEC H264 PARA MEJOR COMPATIBILIDAD Y FLUIDEZ
            fourcc = cv2.VideoWriter_fourcc(*'H264')
            video_writer = cv2.VideoWriter(
                str(ruta_evidencia),
                fourcc,
                fps_target,
                (width, height)
            )

            if not video_writer.isOpened():
                # Fallback a mp4v si H264 no está disponible
                print("H264 no disponible, usando mp4v...")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(
                    str(ruta_evidencia),
                    fourcc,
                    fps_target,
                    (width, height)
                )

            if not video_writer.isOpened():
                print(f"❌ Error: No se pudo crear VideoWriter para {ruta_evidencia}")
                return

            # GENERAR FRAMES CON INTERVALOS REGULARES PARA VIDEO FLUIDO
            frames_regulares = self._generar_frames_regulares(frames_data, fps_target)
            
            # Escribir frames regulares
            frames_escritos = 0
            for frame_data in frames_regulares:
                try:
                    frame = frame_data['frame'].copy()
                    
                    # Asegurar dimensiones consistentes
                    if frame.shape[:2] != (height, width):
                        frame = cv2.resize(frame, (width, height))
                    
                    # AGREGAR OVERLAY DE VIOLENCIA SI ESTÁ PRESENTE
                    violencia_info = frame_data.get('violencia_info')
                    if violencia_info and violencia_info.get('detectada'):
                        # Agregar texto de VIOLENCIA DETECTADA
                        probabilidad = violencia_info.get('probabilidad', 0.0)
                        texto_violencia = f"VIOLENCIA DETECTADA - {probabilidad:.1%}"
                        
                        # Fondo rojo para el texto
                        cv2.rectangle(frame, (10, 10), (width-10, 80), (0, 0, 255), -1)
                        
                        # Texto en blanco
                        cv2.putText(
                            frame, 
                            texto_violencia, 
                            (20, 45), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            1.0, 
                            (255, 255, 255), 
                            2,
                            cv2.LINE_AA
                        )
                        
                        # Tiempo del incidente
                        timestamp_str = frame_data['timestamp'].strftime("%H:%M:%S")
                        cv2.putText(
                            frame, 
                            timestamp_str, 
                            (20, 70), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.6, 
                            (255, 255, 255), 
                            1,
                            cv2.LINE_AA
                        )
                    else:
                        # Solo timestamp normal
                        timestamp_str = frame_data['timestamp'].strftime("%H:%M:%S.%f")[:-3]
                        cv2.putText(
                            frame, 
                            timestamp_str, 
                            (10, height - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.5, 
                            (255, 255, 255), 
                            1
                        )
                    
                    video_writer.write(frame)
                    frames_escritos += 1
                    
                except Exception as e:
                    print(f"❌ Error escribiendo frame {frames_escritos}: {e}")
                    continue

            video_writer.release()

            # Verificar que el archivo se creó correctamente
            if ruta_evidencia.exists() and frames_escritos > 0:
                tamano_archivo = ruta_evidencia.stat().st_size / (1024 * 1024)
                duracion_real = frames_escritos / fps_target
                print(f"✅ Video guardado: {ruta_evidencia}")
                print(f"📹 Tamaño: {tamano_archivo:.2f} MB")
                print(f"📹 Frames: {frames_escritos}")
                print(f"📹 Duración: {duracion_real:.2f} segundos")
                
                # Actualizar incidente si existe
                if incidente_id:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(
                            self._actualizar_incidente_con_video(incidente_id, str(ruta_evidencia))
                        )
                    finally:
                        loop.close()
            else:
                print(f"❌ Error: No se pudo crear el archivo de video o no hay frames")

        except Exception as e:
            print(f"❌ Error al guardar evidencia: {e}")
            import traceback
            traceback.print_exc()

    def _generar_frames_regulares(self, frames_data: List[Dict], fps_target: int) -> List[Dict]:
        """Genera frames con intervalos regulares para video fluido - MEJORADO"""
        if not frames_data:
            return []
        
        # Ordenar frames por timestamp
        frames_ordenados = sorted(frames_data, key=lambda x: x['timestamp'])
        
        # Calcular duración total
        tiempo_inicio = frames_ordenados[0]['timestamp']
        tiempo_fin = frames_ordenados[-1]['timestamp']
        duracion_total = (tiempo_fin - tiempo_inicio).total_seconds()
        
        if duracion_total <= 0:
            return frames_ordenados
        
        # Calcular intervalos de tiempo para FPS objetivo
        intervalo_frame = 1.0 / fps_target
        frames_regulares = []
        
        tiempo_actual = 0
        while tiempo_actual <= duracion_total:
            timestamp_objetivo = tiempo_inicio + timedelta(seconds=tiempo_actual)
            
            # Encontrar el frame más cercano a este timestamp
            frame_mas_cercano = min(
                frames_ordenados,
                key=lambda x: abs((x['timestamp'] - timestamp_objetivo).total_seconds())
            )
            
            # Crear nuevo frame regular manteniendo toda la información
            frame_regular = {
                'frame': frame_mas_cercano['frame'].copy(),
                'timestamp': timestamp_objetivo,
                'detecciones': frame_mas_cercano['detecciones'],
                'violencia_info': frame_mas_cercano.get('violencia_info')  # Mantener info de violencia
            }
            
            frames_regulares.append(frame_regular)
            tiempo_actual += intervalo_frame
        
        print(f"📹 Generación regular: {len(frames_data)} frames originales -> {len(frames_regulares)} frames regulares")
        return frames_regulares

    async def _actualizar_incidente_con_video(self, incidente_id: int, ruta_video: str):
        """Actualiza el incidente con la ruta del video"""
        try:
            await self.servicio_incidentes.actualizar_incidente(
                incidente_id,
                {
                    'video_evidencia_path': ruta_video,
                    'fecha_hora_fin': datetime.now()
                }
            )
            print(f"✅ Incidente {incidente_id} actualizado con video: {ruta_video}")
        except Exception as e:
            print(f"❌ Error actualizando incidente con video: {e}")

    async def _activar_alarma(self):
        """Activa la alarma de forma asíncrona"""
        try:
            await self.servicio_alarma.activar_alarma(duracion=5)
        except Exception as e:
            print(f"❌ Error al activar alarma: {e}")

    async def _crear_incidente(self, personas_involucradas: List[Dict[str, Any]], probabilidad: float):
        """Crea un incidente de forma asíncrona"""
        try:
            if not self.servicio_incidentes:
                print("❌ Servicio de incidentes no inicializado")
                return
                
            incidente_data = {
                'camara_id': self.camara_id,
                'tipo_incidente': TipoIncidente.VIOLENCIA_FISICA,
                'severidad': self._calcular_severidad(probabilidad),
                'probabilidad_violencia': probabilidad,
                'fecha_hora_inicio': self.tiempo_inicio_violencia or datetime.now(),
                'ubicacion': self.ubicacion,
                'numero_personas_involucradas': len(personas_involucradas),
                'ids_personas_detectadas': [],
                'estado': EstadoIncidente.NUEVO,
                'descripcion': f"Violencia detectada con probabilidad {probabilidad:.2%}"
            }
            
            print("⏳ Creando incidente con datos:", incidente_data)
            
            # Crear incidente
            print("⏳ Ejecutando commit...")
            incidente = await self.servicio_incidentes.crear_incidente(incidente_data)
            
            if incidente and hasattr(incidente, 'id'):
                self.incidente_actual_id = incidente.id
                self.incidentes_detectados += 1
                print(f"✅ Incidente creado exitosamente: ID {incidente.id}")
                print(f"📊 Nuevo incidente registrado ID: {incidente.id}")

        except Exception as e:
            print(f"❌ Error al crear incidente: {str(e)}")
            import traceback
            traceback.print_exc()

    def _calcular_severidad(self, probabilidad: float) -> SeveridadIncidente:
        """Calcula la severidad basada en la probabilidad"""
        if probabilidad >= 0.9:
            return SeveridadIncidente.CRITICA
        elif probabilidad >= 0.8:
            return SeveridadIncidente.ALTA
        elif probabilidad >= 0.7:
            return SeveridadIncidente.MEDIA
        else:
            return SeveridadIncidente.BAJA

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del pipeline"""
        return {
            'frames_procesados': self.frames_procesados,
            'incidentes_detectados': self.incidentes_detectados,
            'violencia_activa': self.detector_violencia.violencia_detectada,
            'probabilidad_actual': self.detector_violencia.probabilidad_violencia,
            'grabando_evidencia': self.grabando_evidencia,
            'frames_en_buffer': len(self.buffer_evidencia.frames),
            'tiempo_inicio_violencia': self.tiempo_inicio_violencia.isoformat() if self.tiempo_inicio_violencia else None
        }

    def reiniciar(self):
        """Reinicia el estado del pipeline"""
        # Finalizar grabación si está activa
        if self.grabando_evidencia:
            asyncio.create_task(self._finalizar_grabacion_evidencia())
        
        # Reiniciar detector de violencia
        self.detector_violencia.reiniciar()
        
        # Limpiar buffers
        self.buffer_evidencia = FrameBuffer(max_duration_seconds=15)
        self.grabando_evidencia = False
        self.tiempo_inicio_violencia = None
        self.tiempo_fin_violencia = None
        
        # Reiniciar contadores
        self.frames_procesados = 0
        self.ultimo_incidente = 0
        
        if hasattr(self, 'incidente_actual_id'):
            delattr(self, 'incidente_actual_id')
        
        print("🔄 Pipeline reiniciado")

    def __del__(self):
        """Destructor para limpiar recursos"""
        try:
            if self.grabando_evidencia:
                # No podemos usar asyncio aquí, así que solo marcamos para limpieza
                self.grabando_evidencia = False
        except:
            pass
