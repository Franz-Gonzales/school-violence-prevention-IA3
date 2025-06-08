import cv2
import numpy as np
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import threading
import queue
import time
import traceback
import concurrent.futures

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

logger = obtener_logger(__name__)

class FrameBuffer:
    """Buffer inteligente para frames con timestamps precisos"""
    def __init__(self, max_duration_seconds=30):
        self.frames = deque()
        self.max_duration = max_duration_seconds
        
    def add_frame(self, frame, timestamp, detecciones=None, violencia_info=None):
        """Agrega un frame con timestamp preciso y información de violencia"""
        frame_data = {
            'frame': frame.copy(),
            'timestamp': timestamp,
            'detecciones': detecciones or [],
            'violencia_info': violencia_info,
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

class ViolenceFrameBuffer:
    """Buffer dedicado EXCLUSIVAMENTE para frames con violencia detectada - MEJORADO"""
    def __init__(self, max_frames=2000):  # Aumentar capacidad
        self.violence_frames = deque(maxlen=max_frames)
        self.violence_sequences = []
        self.current_sequence = None
        self.sequence_id = 0
        self.last_violence_state = False
        
        # MEJORADO: Control de duplicación inteligente
        self.frame_duplication_factor = 8  # Duplicar cada frame de violencia 8 veces
        self.violence_frame_counter = 0
        
    def start_violence_sequence(self, start_time):
        """Inicia una nueva secuencia de violencia"""
        if self.current_sequence is not None:
            return
            
        self.sequence_id += 1
        self.current_sequence = {
            'id': self.sequence_id,
            'start_time': start_time,
            'end_time': None,
            'frames': [],
            'max_probability': 0.0,
            'total_frames': 0,
            'duplicated_frames': 0  # NUEVO: Contador de frames duplicados
        }
        self.last_violence_state = True
        print(f"🔴 NUEVA SECUENCIA DE VIOLENCIA INICIADA: #{self.sequence_id}")
        print(f"🚨 INICIO DE VIOLENCIA DETECTADA: {start_time}")
    
    def add_violence_frame(self, frame, timestamp, detecciones, violencia_info):
        """MEJORADO: Agrega frame con MÁXIMA duplicación para video robusto"""
        if not violencia_info or not violencia_info.get('detectada'):
            return
        
        probability = violencia_info.get('probabilidad', 0.0)
        self.violence_frame_counter += 1
        
        # Crear overlay de violencia en el frame
        frame_with_overlay = self._add_violence_overlay(frame.copy(), violencia_info, detecciones)
        
        # FRAME ORIGINAL con overlay
        violence_frame_data = {
            'frame': frame_with_overlay,
            'original_frame': frame.copy(),
            'timestamp': timestamp,
            'detecciones': detecciones,
            'violencia_info': violencia_info,
            'probability': probability,
            'sequence_id': self.sequence_id if self.current_sequence else 0,
            'is_violence': True,
            'frame_type': 'original',
            'duplicate_id': 0
        }
        
        # Agregar frame original
        self.violence_frames.append(violence_frame_data)
        
        # DUPLICACIÓN MASIVA para garantizar presencia en el video
        for i in range(self.frame_duplication_factor):
            duplicate_frame = {
                'frame': frame_with_overlay.copy(),
                'original_frame': frame.copy(),
                'timestamp': timestamp + timedelta(microseconds=i*1000),  # Micro-offset para orden
                'detecciones': detecciones,
                'violencia_info': violencia_info,
                'probability': probability,
                'sequence_id': self.sequence_id if self.current_sequence else 0,
                'is_violence': True,
                'frame_type': 'duplicate',
                'duplicate_id': i + 1,
                'parent_frame': self.violence_frame_counter
            }
            self.violence_frames.append(duplicate_frame)
        
        # Agregar a la secuencia actual
        if self.current_sequence:
            self.current_sequence['frames'].append(violence_frame_data)
            self.current_sequence['total_frames'] += 1
            self.current_sequence['duplicated_frames'] += self.frame_duplication_factor
            self.current_sequence['end_time'] = timestamp
            if probability > self.current_sequence['max_probability']:
                self.current_sequence['max_probability'] = probability
        
        # Log cada frame de violencia para verificación
        total_frames_added = 1 + self.frame_duplication_factor
        print(f"🔥 Frame de VIOLENCIA capturado - Prob: {probability:.3f} - Frame #{self.violence_frame_counter}")
        print(f"   ↳ {total_frames_added} frames agregados al buffer (1 original + {self.frame_duplication_factor} duplicados)")
    
    def end_violence_sequence(self, end_time):
        """Finaliza la secuencia actual de violencia - SOLO UNA VEZ"""
        if self.current_sequence is None or not self.last_violence_state:
            return
            
        self.current_sequence['end_time'] = end_time
        duration = (end_time - self.current_sequence['start_time']).total_seconds()
        
        print(f"🔴 SECUENCIA #{self.current_sequence['id']} FINALIZADA:")
        print(f"   - Duración: {duration:.2f}s")
        print(f"   - Frames originales: {self.current_sequence['total_frames']}")
        print(f"   - Frames duplicados: {self.current_sequence['duplicated_frames']}")
        print(f"   - Total en buffer: {self.current_sequence['total_frames'] + self.current_sequence['duplicated_frames']}")
        print(f"   - Probabilidad máxima: {self.current_sequence['max_probability']:.3f}")
        
        self.violence_sequences.append(self.current_sequence)
        self.current_sequence = None
        self.last_violence_state = False
    
    def get_violence_frames_in_range(self, start_time, end_time):
        """MEJORADO: Obtiene TODOS los frames de violencia (originales + duplicados)"""
        violence_frames = [
            f for f in self.violence_frames
            if start_time <= f['timestamp'] <= end_time and f.get('is_violence', False)
        ]
        
        # Contar originales vs duplicados
        original_count = len([f for f in violence_frames if f.get('frame_type') == 'original'])
        duplicate_count = len([f for f in violence_frames if f.get('frame_type') == 'duplicate'])
        
        print(f"🔍 Frames de violencia extraídos: {len(violence_frames)} total")
        print(f"   ↳ {original_count} originales + {duplicate_count} duplicados")
        
        return violence_frames
    
    def get_recent_violence_frames(self, duration_seconds):
        """Obtiene frames de violencia recientes"""
        if not self.violence_frames:
            return []
        
        latest_time = self.violence_frames[-1]['timestamp']
        start_time = latest_time - timedelta(seconds=duration_seconds)
        return self.get_violence_frames_in_range(start_time, latest_time)
    
    def _add_violence_overlay(self, frame, violencia_info, detecciones):
        """Agrega overlay rojo intenso para frames de violencia"""
        height, width = frame.shape[:2]
        probability = violencia_info.get('probabilidad', 0.0)
        
        # Overlay rojo semitransparente MÁS INTENSO
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 120), (0, 0, 255), -1)
        frame = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)
        
        # Texto principal GRANDE Y VISIBLE
        cv2.putText(
            frame, 
            "VIOLENCIA DETECTADA", 
            (20, 40), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.2, 
            (255, 255, 255), 
            4,
            cv2.LINE_AA
        )
        
        # Probabilidad en ROJO BRILLANTE
        cv2.putText(
            frame, 
            f"PROBABILIDAD: {probability:.1%}", 
            (20, 80), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.0, 
            (0, 255, 255), 
            3,
            cv2.LINE_AA
        )
        
        # Timestamp
        timestamp_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        cv2.putText(
            frame, 
            f"TIEMPO: {timestamp_str}", 
            (20, 110), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            (255, 255, 255), 
            2,
            cv2.LINE_AA
        )
        
        # Dibujar detecciones de personas CON BORDE ROJO
        for detection in detecciones:
            bbox = detection.get('bbox', [])
            if len(bbox) >= 4:
                x, y, w, h = map(int, bbox)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                cv2.putText(
                    frame, 
                    f"PERSONA EN VIOLENCIA", 
                    (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (0, 0, 255), 
                    2
                )
        
        return frame
    
    def get_stats(self):
        """Obtiene estadísticas del buffer de violencia"""
        return {
            'total_violence_frames': len(self.violence_frames),
            'violence_sequences': len(self.violence_sequences),
            'current_sequence_active': self.current_sequence is not None,
            'current_sequence_frames': len(self.current_sequence['frames']) if self.current_sequence else 0,
            'duplication_factor': self.frame_duplication_factor,
            'violence_frame_counter': self.violence_frame_counter
        }

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
        
        # Buffer inteligente para evidencia NORMAL
        self.buffer_evidencia = FrameBuffer(max_duration_seconds=30)
        
        # Buffer dedicado EXCLUSIVAMENTE para violencia - MEJORADO
        self.violence_buffer = ViolenceFrameBuffer(max_frames=2000)
        
        # Control de grabación de evidencia MEJORADO
        self.grabando_evidencia = False
        self.tiempo_inicio_violencia = None
        self.tiempo_fin_violencia = None
        self.duracion_evidencia_pre = 6
        self.duracion_evidencia_post = 8
        
        # NUEVO: Control de estado de violencia para evitar repeticiones
        self.violencia_estado_anterior = False
        self.secuencia_violencia_activa = False
        self.ultimo_frame_violencia = 0
        
        # Cola para guardar videos de forma asíncrona
        self.cola_guardado = queue.Queue()
        self.hilo_guardado = threading.Thread(target=self._procesar_cola_guardado, daemon=True)
        self.hilo_guardado.start()
        
        # Pool de hilos para updates de DB
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="db_update")
        
        # Estadísticas
        self.frames_procesados = 0
        self.incidentes_detectados = 0
        
        # Control de tiempo para evitar spam
        self.ultimo_incidente = 0
        self.cooldown_incidente = 10
        
        # FPS target para evidencia
        self.target_fps_evidencia = 15
        
        # Control para evidencia
        self.frame_feed_interval = 1.0 / 25
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
            violencia_detectada_ahora = False

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
                    violencia_detectada_ahora = deteccion['violencia_detectada']

                    if violencia_detectada_ahora:
                        current_time = timestamp_actual.timestamp()
                        
                        # Preparar información de violencia para el frame
                        violencia_info = {
                            'detectada': True,
                            'probabilidad': deteccion.get('probabilidad', 0.0),
                            'timestamp': timestamp_actual
                        }
                        
                        # CONTROL MEJORADO: Solo actuar si es una nueva detección o se reanuda
                        if not self.violencia_estado_anterior:
                            print(f"¡ALERTA! Violencia detectada")
                            
                            # Marcar inicio de violencia SOLO LA PRIMERA VEZ
                            if not self.secuencia_violencia_activa:
                                self.tiempo_inicio_violencia = timestamp_actual
                                self.secuencia_violencia_activa = True
                                self.grabando_evidencia = True
                                
                                # INICIAR SECUENCIA DE VIOLENCIA
                                self.violence_buffer.start_violence_sequence(timestamp_actual)
                                print(f"🚨 Activando alarma por 5 segundos")
                                
                                # Activar alarma SOLO una vez
                                asyncio.create_task(self._activar_alarma())
                                
                                # Crear incidente SOLO una vez
                                if current_time - self.ultimo_incidente > self.cooldown_incidente:
                                    asyncio.create_task(self._crear_incidente(detecciones, deteccion.get('probabilidad', 0.0)))
                                    self.ultimo_incidente = current_time
                        
                        # Agregar alerta al frame CON PROBABILIDAD CORRECTA
                        probabilidad_texto = f"Probabilidad: {deteccion.get('probabilidad', 0.0):.1%}"
                        frame_procesado = await asyncio.get_event_loop().run_in_executor(
                            None,
                            self.procesador_video.agregar_texto_alerta,
                            frame_procesado,
                            probabilidad_texto,
                            (0, 0, 255),
                            1.2
                        )
                        
                        resultado['frame_procesado'] = frame_procesado
                        
                        # MEJORADO: SIEMPRE agregar frames de violencia al buffer especializado
                        self.violence_buffer.add_violence_frame(
                            frame_original, 
                            timestamp_actual, 
                            detecciones, 
                            violencia_info
                        )
                        
                        # Actualizar tiempo de fin de violencia
                        self.tiempo_fin_violencia = timestamp_actual
                        self.ultimo_frame_violencia = self.frames_procesados
                        
                        # Actualizar estado
                        self.violencia_estado_anterior = True
                        
                    else:
                        # NO hay violencia en este frame
                        if self.violencia_estado_anterior:
                            # FIN de secuencia de violencia
                            if self.secuencia_violencia_activa and self.tiempo_fin_violencia:
                                tiempo_transcurrido = (timestamp_actual - self.tiempo_fin_violencia).total_seconds()
                                
                                # Esperar un poco más antes de finalizar la secuencia
                                if tiempo_transcurrido >= (self.duracion_evidencia_post + 2):
                                    # FINALIZAR SECUENCIA SOLO UNA VEZ
                                    self.violence_buffer.end_violence_sequence(timestamp_actual)
                                    await self._finalizar_grabacion_evidencia()
                                    
                                    # Reset estado
                                    self.secuencia_violencia_activa = False
                                    self.violencia_estado_anterior = False

            # Agregar frame al buffer NORMAL (SIEMPRE)
            current_time = time.time()
            if current_time - self.last_evidence_feed >= self.frame_feed_interval:
                self.buffer_evidencia.add_frame(
                    frame_procesado, 
                    timestamp_actual, 
                    detecciones,
                    violencia_info
                )
                
                # EVIDENCIA: Priorizar frames de violencia
                evidence_recorder.add_frame(
                    frame_original, 
                    detecciones, 
                    violencia_info
                )
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
        """MEJORADO: Finaliza la grabación MAXIMIZANDO frames de violencia"""
        if not self.tiempo_inicio_violencia:
            return
            
        print(f"📹 Finalizando grabación de evidencia...")
        
        # Calcular tiempos para el clip de evidencia
        tiempo_inicio_clip = self.tiempo_inicio_violencia - timedelta(seconds=self.duracion_evidencia_pre)
        tiempo_fin_clip = self.tiempo_fin_violencia + timedelta(seconds=self.duracion_evidencia_post)
        
        # PRIORIDAD 1: Obtener TODOS los frames de violencia detectada (incluye duplicados)
        frames_violencia = self.violence_buffer.get_violence_frames_in_range(
            tiempo_inicio_clip, 
            tiempo_fin_clip
        )
        
        # PRIORIDAD 2: Obtener frames normales para contexto
        frames_contexto = self.buffer_evidencia.get_frames_in_range(
            tiempo_inicio_clip, 
            tiempo_fin_clip
        )
        
        print(f"📹 Frames de VIOLENCIA extraídos: {len(frames_violencia)}")
        print(f"📹 Frames de CONTEXTO extraídos: {len(frames_contexto)}")
        
        # MEJORADO: Si hay pocos frames de violencia, agregar más copias
        if len(frames_violencia) < 50:  # Menos de ~3 segundos a 15fps
            print(f"⚠️ Agregando más frames de violencia para garantizar contenido...")
            
            # Duplicar frames de violencia existentes
            frames_adicionales_violencia = []
            for _ in range(3):  # 3 rondas adicionales de duplicación
                for frame_v in frames_violencia[:10]:  # Solo los primeros 10 para evitar spam
                    frame_copy = frame_v.copy()
                    frame_copy['timestamp'] = frame_copy['timestamp'] + timedelta(microseconds=len(frames_adicionales_violencia)*100)
                    frame_copy['duplicate_round'] = _
                    frames_adicionales_violencia.append(frame_copy)
            
            frames_violencia.extend(frames_adicionales_violencia)
            print(f"📹 Frames adicionales de violencia: {len(frames_adicionales_violencia)}")
        
        # COMBINAR frames priorizando los de violencia
        frames_evidencia = self._combinar_frames_con_prioridad_mejorada(frames_violencia, frames_contexto)
        
        if frames_evidencia:
            duracion_total = (tiempo_fin_clip - tiempo_inicio_clip).total_seconds()
            print(f"📹 TOTAL frames para evidencia: {len(frames_evidencia)}")
            print(f"📹 Duración del clip: {duracion_total:.2f} segundos")
            
            # GARANTIZAR MÍNIMO 5 SEGUNDOS CON CONTENIDO DE VIOLENCIA
            if len(frames_evidencia) < (5 * self.target_fps_evidencia):
                print(f"⚠️ Expandiendo frames para garantizar 5+ segundos...")
                frames_evidencia = self._expandir_frames_para_duracion(frames_evidencia, 5 * self.target_fps_evidencia)
                print(f"📹 Frames expandidos a: {len(frames_evidencia)}")
            
            # Enviar a cola de guardado asíncrono
            datos_guardado = {
                'frames': frames_evidencia,
                'camara_id': self.camara_id,
                'tiempo_inicio': tiempo_inicio_clip,
                'tiempo_fin': tiempo_fin_clip,
                'incidente_id': getattr(self, 'incidente_actual_id', None),
                'fps_target': self.target_fps_evidencia,
                'violence_frames_count': len(frames_violencia)
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

    def _combinar_frames_con_prioridad_mejorada(self, frames_violencia, frames_contexto):
        """MEJORADO: Combina frames garantizando presencia masiva de violencia"""
        frames_combinados = []
        
        # Crear diccionario de frames de violencia por timestamp
        violence_by_time = {}
        for f in frames_violencia:
            timestamp_key = f['timestamp'].isoformat()
            if timestamp_key not in violence_by_time:
                violence_by_time[timestamp_key] = []
            violence_by_time[timestamp_key].append(f)
        
        # Crear lista de todos los timestamps ordenados
        all_timestamps = set()
        for f in frames_violencia:
            all_timestamps.add(f['timestamp'])
        for f in frames_contexto:
            all_timestamps.add(f['timestamp'])
        
        # Ordenar timestamps
        sorted_timestamps = sorted(all_timestamps)
        
        # MEJORADO: Combinar priorizando MASIVAMENTE la violencia
        for timestamp in sorted_timestamps:
            timestamp_key = timestamp.isoformat()
            
            # Si hay frames de violencia para este timestamp, usar TODOS
            if timestamp_key in violence_by_time:
                for violence_frame in violence_by_time[timestamp_key]:
                    frames_combinados.append(violence_frame)
            else:
                # Usar frame de contexto solo si no hay violencia
                context_frame = next((f for f in frames_contexto if f['timestamp'] == timestamp), None)
                if context_frame:
                    frames_combinados.append(context_frame)
        
        violence_count = len([f for f in frames_combinados if f.get('violencia_info', {}).get('detectada', False)])
        print(f"🔄 Frames combinados: {len(frames_combinados)} (Violencia efectiva: {violence_count}, Contexto: {len(frames_contexto)})")
        
        return frames_combinados

    def _expandir_frames_para_duracion(self, frames_data: List[Dict], frames_objetivo: int) -> List[Dict]:
        """MEJORADO: Expande frames priorizando duplicación de violencia"""
        if len(frames_data) >= frames_objetivo:
            return frames_data
        
        frames_expandidos = list(frames_data)  # Copiar lista original
        
        # Identificar frames de violencia para duplicación preferencial
        frames_violencia = [f for f in frames_data if f.get('violencia_info', {}).get('detectada', False)]
        frames_normales = [f for f in frames_data if not f.get('violencia_info', {}).get('detectada', False)]
        
        # Mientras no lleguemos al objetivo, duplicar frames
        while len(frames_expandidos) < frames_objetivo:
            # Priorizar duplicación de frames de violencia
            if frames_violencia:
                for frame_v in frames_violencia:
                    if len(frames_expandidos) >= frames_objetivo:
                        break
                    
                    frame_copia = frame_v.copy()
                    frame_copia['timestamp'] = frame_copia['timestamp'] + timedelta(microseconds=len(frames_expandidos)*50)
                    frame_copia['expanded'] = True
                    frames_expandidos.append(frame_copia)
            
            # Si aún necesitamos más frames, duplicar frames normales
            if len(frames_expandidos) < frames_objetivo and frames_normales:
                for frame_n in frames_normales:
                    if len(frames_expandidos) >= frames_objetivo:
                        break
                    
                    frame_copia = frame_n.copy()
                    frame_copia['timestamp'] = frame_copia['timestamp'] + timedelta(microseconds=len(frames_expandidos)*50)
                    frame_copia['expanded'] = True
                    frames_expandidos.append(frame_copia)
            
            # Evitar bucle infinito si no hay frames para duplicar
            if not frames_violencia and not frames_normales:
                break
        
        return frames_expandidos[:frames_objetivo]

    def _procesar_cola_guardado(self):
        """Procesa la cola de guardado en hilo separado"""
        while True:
            try:
                datos = self.cola_guardado.get(timeout=1)
                self._guardar_evidencia_mejorado(datos)
                self.cola_guardado.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error en hilo de guardado: {e}")

    def _guardar_evidencia_mejorado(self, datos: Dict[str, Any]):
        """MEJORADO: Guarda evidencia maximizando frames de violencia"""
        try:
            frames_data = datos['frames']
            camara_id = datos['camara_id']
            tiempo_inicio = datos['tiempo_inicio']
            fps_target = datos['fps_target']
            incidente_id = datos.get('incidente_id')
            violence_frames_count = datos.get('violence_frames_count', 0)
            
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
            print(f"📹 Frames disponibles: {len(frames_data)}")
            print(f"🔥 Frames de VIOLENCIA: {violence_frames_count}")
            
            # CONTAR frames de violencia reales en los datos
            violence_frames_reales = len([f for f in frames_data if f.get('violencia_info', {}).get('detectada', False)])
            
            # DUPLICAR/INTERPOLAR FRAMES PARA GARANTIZAR 5+ SEGUNDOS
            frames_minimos = int(5.0 * fps_target)
            if len(frames_data) < frames_minimos:
                frames_expandidos = self._expandir_frames_para_duracion(frames_data, frames_minimos)
                print(f"📹 Frames expandidos de {len(frames_data)} a {len(frames_expandidos)} para 5+ segundos")
                frames_data = frames_expandidos
            
            # USAR MP4V COMO CODEC PRINCIPAL
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

            # ESCRIBIR FRAMES (ya tienen overlay si son de violencia)
            frames_escritos = 0
            frames_violencia_escritos = 0
            
            for i, frame_data in enumerate(frames_data):
                try:
                    frame = frame_data['frame'].copy()
                    
                    # Contar frames de violencia escritos
                    if frame_data.get('violencia_info', {}).get('detectada', False):
                        frames_violencia_escritos += 1
                    
                    # Asegurar dimensiones consistentes
                    if frame.shape[:2] != (height, width):
                        frame = cv2.resize(frame, (width, height))
                    
                    video_writer.write(frame)
                    frames_escritos += 1
                    
                except Exception as e:
                    print(f"❌ Error escribiendo frame {i}: {e}")
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
                print(f"🔥 Contenido de violencia: {frames_violencia_escritos} frames")
                
                # ACTUALIZAR INCIDENTE SIN CREAR CONFLICTOS DE LOOP
                if incidente_id:
                    self._actualizar_incidente_thread_safe(incidente_id, str(ruta_evidencia))
            else:
                print(f"❌ Error: No se pudo crear el archivo de video o no hay frames")

        except Exception as e:
            print(f"❌ Error al guardar evidencia: {e}")
            import traceback
            traceback.print_exc()

    def _actualizar_incidente_thread_safe(self, incidente_id: int, ruta_video: str):
        """Actualiza incidente usando ThreadPoolExecutor para evitar conflictos de loop"""
        try:
            def update_sync():
                """Función síncrona que se ejecuta en el pool de hilos"""
                try:
                    import requests
                    import json
                    
                    # URL del endpoint de actualización INTERNO
                    api_url = "http://localhost:8000/api/v1/incidents"
                    update_url = f"{api_url}/{incidente_id}/internal"
                    
                    # Datos de actualización
                    update_data = {
                        "video_evidencia_path": ruta_video
                    }
                    
                    # Headers básicos
                    headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                    
                    # Realizar petición HTTP PATCH
                    response = requests.patch(
                        update_url,
                        json=update_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Incidente {incidente_id} actualizado con video: {ruta_video}")
                    else:
                        print(f"⚠️ Respuesta HTTP {response.status_code} al actualizar incidente {incidente_id}")
                        print(f"📝 MANUAL UPDATE NEEDED: Incidente {incidente_id} -> {ruta_video}")
                        
                except Exception as e:
                    print(f"❌ Error en update_sync: {e}")
                    print(f"📝 MANUAL UPDATE NEEDED: Incidente {incidente_id} -> {ruta_video}")
            
            # Ejecutar en pool de hilos dedicado SIN crear nuevos loops
            future = self.executor.submit(update_sync)
            
            # Opcional: agregar callback para manejar resultado
            def handle_result(fut):
                try:
                    fut.result(timeout=5)
                except Exception as e:
                    print(f"❌ Error en future result: {e}")
            
            future.add_done_callback(handle_result)
            
        except Exception as e:
            print(f"❌ Error en actualización thread-safe: {e}")
            print(f"📝 MANUAL UPDATE NEEDED: Incidente {incidente_id} -> {ruta_video}")

    async def _activar_alarma(self):
        """Activa la alarma de forma asíncrona"""
        try:
            await self.servicio_alarma.activar_alarma(5)
        except Exception as e:
            print(f"Error activando alarma: {e}")

    async def _crear_incidente(self, personas_involucradas: List[Dict[str, Any]], probabilidad: float):
        """Crea un incidente de forma asíncrona"""
        try:
            datos_incidente = {
                'camara_id': self.camara_id,
                'tipo_incidente': TipoIncidente.VIOLENCIA_FISICA,
                'severidad': self._calcular_severidad(probabilidad),
                'probabilidad_violencia': probabilidad,
                'fecha_hora_inicio': self.tiempo_inicio_violencia,
                'ubicacion': self.ubicacion,
                'numero_personas_involucradas': len(personas_involucradas),
                'ids_personas_detectadas': [],
                'estado': EstadoIncidente.NUEVO,
                'descripcion': f"Violencia detectada con probabilidad {probabilidad:.2%}"
            }
            
            incidente = await self.servicio_incidentes.crear_incidente(datos_incidente)
            self.incidente_actual_id = incidente.id
            self.incidentes_detectados += 1
            
            print(f"📊 Nuevo incidente registrado ID: {incidente.id}")
            
        except Exception as e:
            print(f"Error creando incidente: {e}")
            import traceback
            traceback.print_exc()

    def _calcular_severidad(self, probabilidad: float) -> SeveridadIncidente:
        """Calcula la severidad basada en la probabilidad"""
        if probabilidad >= 0.9:
            return SeveridadIncidente.CRITICA
        elif probabilidad >= 0.8:
            return SeveridadIncidente.ALTA
        elif probabilidad >= 0.6:
            return SeveridadIncidente.MEDIA
        else:
            return SeveridadIncidente.BAJA

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del pipeline MEJORADAS"""
        violence_stats = self.violence_buffer.get_stats()
        
        return {
            'frames_procesados': self.frames_procesados,
            'incidentes_detectados': self.incidentes_detectados,
            'activo': self.activo,
            'grabando_evidencia': self.grabando_evidencia,
            'buffer_size': len(self.buffer_evidencia.frames),
            'violence_buffer_size': violence_stats['total_violence_frames'],
            'violence_sequences': violence_stats['violence_sequences'],
            'current_sequence_active': violence_stats['current_sequence_active'],
            'duplication_factor': violence_stats['duplication_factor'],
            'violence_frame_counter': violence_stats['violence_frame_counter']
        }

    def reiniciar(self):
        """Reinicia el pipeline"""
        self.detector_violencia.reiniciar()
        self.frames_procesados = 0
        self.activo = False
        self.grabando_evidencia = False
        self.tiempo_inicio_violencia = None
        self.tiempo_fin_violencia = None
        
        # Reset estados de violencia
        self.violencia_estado_anterior = False
        self.secuencia_violencia_activa = False
        self.ultimo_frame_violencia = 0
        
        # Limpiar buffer de violencia
        self.violence_buffer = ViolenceFrameBuffer(max_frames=2000)
        print("🔄 Pipeline reiniciado")

    def __del__(self):
        """Limpieza al destruir el objeto"""
        try:
            if hasattr(self, 'hilo_guardado') and self.hilo_guardado.is_alive():
                self.cola_guardado.put(None)
            
            # Cerrar pool de hilos
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
        except:
            pass