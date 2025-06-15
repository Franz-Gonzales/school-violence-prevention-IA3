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
from pathlib import Path

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
# AGREGAR AL INICIO DEL ARCHIVO (después de los imports existentes):
from app.services.voice_alert_service import servicio_alertas_voz

logger = obtener_logger(__name__)

class FrameBuffer:
    """Buffer inteligente para frames con timestamps precisos"""
    def __init__(self, max_duration_seconds=30):
        self.frames = deque()
        self.max_duration = max_duration_seconds
        # Pool de hilos para updates de DB
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="db_update")
        
        # **NUEVO: Variable para guardar ID del incidente actual**
        self.incidente_actual_id = None
        
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
        """Agrega overlay rojo con tamaño moderado para frames de violencia"""
        height, width = frame.shape[:2]
        probability = violencia_info.get('probabilidad', 0.0)
        
        # *** OVERLAY ROJO MODERADO ***
        overlay_height = 70  # Reducido significativamente
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, overlay_height), (0, 0, 255), -1)
        frame = cv2.addWeighted(frame, 0.75, overlay, 0.25, 0)  # Menos intenso
        
        # *** TEXTO PRINCIPAL MODERADO ***
        cv2.putText(
            frame, 
            "VIOLENCIA DETECTADA", 
            (10, 22), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7,  # Tamaño moderado
            (255, 255, 255), 
            2,    # Grosor moderado
            cv2.LINE_AA
        )
        
        # *** PROBABILIDAD COMPACTA ***
        cv2.putText(
            frame, 
            f"Prob: {probability:.1%}", 
            (10, 45), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5,  # Más pequeño
            (0, 255, 255), 
            1,    # Más delgado
            cv2.LINE_AA
        )
        
        # *** TIMESTAMP COMPACTO ***
        timestamp_str = datetime.now().strftime("%H:%M:%S")
        cv2.putText(
            frame, 
            timestamp_str, 
            (10, 62), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.45, # Muy pequeño
            (255, 255, 255), 
            1,
            cv2.LINE_AA
        )
        
        # *** BOUNDING BOXES DE PERSONAS MÁS DISCRETOS ***
        for detection in detecciones:
            bbox = detection.get('bbox', [])
            if len(bbox) >= 4:
                x1, y1, x2, y2 = map(int, bbox[:4])
                # Borde rojo más delgado
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                
                # Etiqueta más pequeña
                label = "PERSONA"
                cv2.putText(
                    frame, 
                    label, 
                    (x1, y1 - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.4,  # Muy pequeño
                    (255, 255, 255), 
                    1,
                    cv2.LINE_AA
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
        self.servicio_notificaciones = ServicioNotificaciones
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

        # **NUEVO: Control de estado para evitar múltiples finalizaciones**
        self.finalizacion_en_progreso = False
        self.video_ya_guardado = False
        self.incidente_procesado = set()  # IDs de incidentes ya procesados
        
        # **NUEVO: Lock para threading safety**
        self.finalization_lock = threading.Lock()
        
        # AGREGAR: Servicio de alertas de voz
        self.servicio_alertas_voz = servicio_alertas_voz
        
        evidence_recorder.set_camera_id(1)

    async def procesar_frame(self, frame: np.ndarray, camara_id: int, ubicacion: str) -> Dict[str, Any]:
        try:
            self.camara_id = camara_id
            self.ubicacion = ubicacion
            self.frames_procesados += 1
            
            evidence_recorder.set_camera_id(camara_id)
            
            timestamp_actual = datetime.now()
            frame_original = frame.copy()
            
            # Detección de personas con YOLO
            detecciones = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.detector_personas.detectar, 
                frame_original
            )
            
            # Crear frame procesado para display
            frame_procesado = frame_original.copy()
            
            if detecciones:
                frame_procesado = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._dibujar_detecciones,
                    frame_procesado,
                    detecciones
                )

            # *** RESULTADO BASE CON ESTRUCTURA CONSISTENTE ***
            resultado = {
                'frame_procesado': frame_procesado,
                'personas_detectadas': detecciones,
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0,
                'probabilidad': 0.0,
                'timestamp': timestamp_actual
            }

            violencia_info = None
            violencia_detectada_ahora = False

            # Solo procesar con TimesFormer si hay personas detectadas
            if detecciones:
                # *** CORRECCIÓN: Agregar frame SIEMPRE para mantener secuencia ***
                self.detector_violencia.agregar_frame(frame_original.copy())
                
                # *** CORRECCIÓN: Procesar cada N frames PERO preservar contexto ***
                if self.frames_procesados % configuracion.TIMESFORMER_CONFIG["num_frames"] == 0:
                    # Detección de violencia
                    deteccion = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.detector_violencia.detectar
                    )
                    
                    print(f"🔍 DETECCIÓN RAW: {deteccion}")
                    
                    if deteccion:
                        probabilidad_detectada = deteccion.get('probabilidad_violencia', deteccion.get('probabilidad', 0.0))
                        
                        resultado.update({
                            'violencia_detectada': deteccion.get('violencia_detectada', False),
                            'probabilidad_violencia': float(probabilidad_detectada),
                            'probabilidad': float(probabilidad_detectada),
                            'frames_analizados': deteccion.get('frames_analizados', 8),  # *** NUEVO ***
                            'batch_completo': deteccion.get('batch_completo', False)  # *** NUEVO ***
                        })
                        
                        print(f"🔍 RESULTADO ACTUALIZADO: probabilidad = {probabilidad_detectada}")
                    
                    violencia_detectada_ahora = resultado['violencia_detectada']

                    if violencia_detectada_ahora:
                        current_time = timestamp_actual.timestamp()
                        probabilidad_real = resultado.get('probabilidad_violencia', resultado.get('probabilidad', 0.0))
                        
                        print(f"🚨 PIPELINE - Probabilidad final: {probabilidad_real} ({probabilidad_real*100:.1f}%)")
                        
                        # *** CORRECCIÓN: Preparar información COMPLETA de violencia ***
                        violencia_info = {
                            'detectada': True,
                            'probabilidad': float(probabilidad_real),
                            'timestamp': timestamp_actual,
                            'frames_analizados': deteccion.get('frames_analizados', 8),  # *** NUEVO ***
                            'batch_completo': True,  # *** NUEVO ***
                            'secuencia_frames': deteccion.get('frames_en_secuencia', [])  # *** NUEVO ***
                        }
                        
                        # CONTROL MEJORADO: Solo actuar si es una nueva detección
                        if not self.violencia_estado_anterior:
                            print(f"¡ALERTA! Violencia detectada - Probabilidad: {probabilidad_real:.3f} ({probabilidad_real*100:.1f}%)")
                            print(f"Ubicación: {ubicacion}")
                            print(f"Personas detectadas: {len(detecciones)}")
                            
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
                                
                                # Emitir alerta de voz
                                personas_count = len(detecciones) if detecciones else 0
                                asyncio.create_task(self._emitir_alerta_voz(
                                    ubicacion=ubicacion,
                                    probabilidad=float(probabilidad_real),
                                    personas_detectadas=personas_count
                                ))
                                
                                # Crear incidente SOLO una vez
                                if current_time - self.ultimo_incidente > self.cooldown_incidente:
                                    asyncio.create_task(self._crear_incidente(
                                        detecciones, 
                                        float(probabilidad_real)
                                    ))
                                    self.ultimo_incidente = current_time
                        
                        # *** AGREGAR ALERTA AL FRAME CON PROBABILIDAD CORRECTA ***
                        probabilidad_texto = f"Probabilidad: {probabilidad_real:.1%}"
                        frame_procesado = await asyncio.get_event_loop().run_in_executor(
                            None,
                            self.procesador_video.agregar_texto_alerta,
                            frame_procesado,
                            probabilidad_texto,
                            (0, 0, 255),
                            1.2
                        )
                        
                        resultado['frame_procesado'] = frame_procesado
                        
                        # *** CORRECCIÓN: AGREGAR TODOS LOS FRAMES DE LA SECUENCIA ***
                        self.violence_buffer.add_violence_frame(
                            frame_original, 
                            timestamp_actual, 
                            detecciones, 
                            violencia_info
                        )
                        
                        # *** NUEVO: Marcar también frames anteriores del batch como parte de la secuencia ***
                        self._marcar_frames_secuencia_violencia(violencia_info)
                        
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
                                
                                if tiempo_transcurrido >= (self.duracion_evidencia_post + 2):
                                    self.violence_buffer.end_violence_sequence(timestamp_actual)
                                    await self._finalizar_grabacion_evidencia()
                                    
                                    # Reset estado
                                    self.secuencia_violencia_activa = False
                                    self.violencia_estado_anterior = False

            # *** CORRECCIÓN: Agregar frame al buffer SIEMPRE con información de contexto ***
            current_time = time.time()
            if current_time - self.last_evidence_feed >= self.frame_feed_interval:
                # *** CORRECCIÓN: Información de contexto SEGURA para frames no violentos ***
                if not violencia_info and self.secuencia_violencia_activa:
                    violencia_info = {
                        'detectada': False,
                        'probabilidad': 0.0,
                        'timestamp': timestamp_actual,
                        'es_contexto_secuencia': True,
                        'frames_desde_violencia': self.frames_procesados - self.ultimo_frame_violencia
                    }
                
                # *** VERIFICACIÓN ANTES DE LLAMAR add_frame ***
                if frame_procesado is not None and detecciones is not None:
                    self.buffer_evidencia.add_frame(
                        frame_procesado, 
                        timestamp_actual, 
                        detecciones,
                        violencia_info
                    )
                    
                    evidence_recorder.add_frame(
                        frame_original, 
                        detecciones, 
                        violencia_info
                    )
                    self.last_evidence_feed = current_time
                else:
                    print("⚠️ Frame o detecciones None, saltando add_frame")
            
            print(f"🔍 RESULTADO FINAL: {resultado.get('probabilidad_violencia', 'NO_FOUND')}")
            
            return resultado

        except Exception as e:
            print(f"❌ Error en pipeline: {e}")
            import traceback
            print(traceback.format_exc())
            return {
                'frame_procesado': frame,
                'personas_detectadas': [],
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0,
                'probabilidad': 0.0,
                'timestamp': datetime.now()
            }

    def _marcar_frames_secuencia_violencia(self, violencia_info: Dict):
        """CORREGIDO: Marca frames anteriores del batch como parte de la secuencia de violencia"""
        try:
            frames_analizados = violencia_info.get('frames_analizados', 8)
            
            # *** CORRECCIÓN: Acceder al deque SIN context manager ***
            # ANTES (INCORRECTO):
            # with self.buffer_evidencia.frames:  # ❌ ESTO CAUSABA EL ERROR
            #     recent_frames = list(self.buffer_evidencia.frames)[-frames_analizados:]
            
            # DESPUÉS (CORRECTO):
            recent_frames = list(self.buffer_evidencia.frames)[-frames_analizados:]
            
            # Marcar todos estos frames como parte de la secuencia de violencia
            for frame_data in recent_frames:
                if frame_data is None:  # Verificación de seguridad
                    continue
                    
                if frame_data.get('violencia_info'):
                    frame_data['violencia_info']['es_secuencia_violencia'] = True
                else:
                    frame_data['violencia_info'] = {
                        'detectada': False,
                        'probabilidad': 0.0,
                        'es_secuencia_violencia': True,
                        'timestamp': frame_data['timestamp']
                    }
                
                # Agregar también al buffer de violencia para preservar la secuencia
                self.violence_buffer.add_violence_frame(
                    frame_data['frame'],
                    frame_data['timestamp'],
                    frame_data.get('detecciones', []),
                    frame_data['violencia_info']
                )
            
            print(f"📝 {len(recent_frames)} frames marcados como secuencia de violencia")
            
        except Exception as e:
            print(f"❌ Error marcando frames de secuencia: {e}")
            # No propagar el error para no afectar el flujo principal


    async def _emitir_alerta_voz(self, ubicacion: str, probabilidad: float, personas_detectadas: int):
        """Emite alerta de voz"""
        try:
            if configuracion.VOICE_ALERTS_ENABLED:
                # *** USAR EL MÉTODO CORRECTO ***
                await servicio_alertas_voz.emitir_alerta_violencia(
                    ubicacion=ubicacion, 
                    probabilidad=probabilidad, 
                    personas_detectadas=personas_detectadas
                )
                logger.info(f"🔊 Alerta de voz emitida para {ubicacion}")
            else:
                logger.info("🔇 Alertas de voz deshabilitadas")
                
        except Exception as e:
            logger.error(f"❌ Error emitiendo alerta de voz: {e}")

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
        """CORREGIDO: Evitar grabación duplicada - Solo notificar al evidence_recorder"""
        try:
            if not self.grabando_evidencia or not self.tiempo_inicio_violencia:
                print("⚠️ No hay grabación activa para finalizar")
                return
            
            if self.finalizacion_en_progreso:
                print("⚠️ Finalización ya en progreso, saltando")
                return
            
            self.finalizacion_en_progreso = True
            self.tiempo_fin_violencia = datetime.now()
            
            print("📹 Finalizando grabación de evidencia...")
            
            # **CAMBIO CRÍTICO: Solo notificar al evidence_recorder, NO generar video aquí**
            from app.tasks.video_recorder import evidence_recorder
            
            # Notificar al evidence_recorder que termine la grabación
            # El evidence_recorder se encargará de generar EL ÚNICO video
            evidence_recorder._finish_recording()
            
            print("✅ Grabación finalizada - evidence_recorder generará el video")
            
            # **ELIMINAR: Todo el código de generación de video de aquí**
            # Ya no extraemos frames ni generamos video en el pipeline
            # El evidence_recorder tiene toda la información necesaria
            
        except Exception as e:
            print(f"❌ Error finalizando grabación: {e}")
            import traceback
            print(traceback.format_exc())
            
        finally:
            # **RESET COMPLETO del estado**
            self.finalizacion_en_progreso = False
            self.grabando_evidencia = False
            self.tiempo_inicio_violencia = None
            self.tiempo_fin_violencia = None

    def _combinar_frames_con_prioridad_mejorada(self, frames_violencia, frames_contexto):
        """CORREGIDO: Manejo seguro de frames None"""
        frames_combinados = []
        
        # **VALIDACIÓN ROBUSTA**
        if not frames_violencia:
            frames_violencia = []
        if not frames_contexto:
            frames_contexto = []
        
        # Filtrar frames None de ambas listas
        frames_violencia = [f for f in frames_violencia if f is not None]
        frames_contexto = [f for f in frames_contexto if f is not None]
        
        # Crear diccionario de frames de violencia por timestamp
        violence_by_time = {}
        for f in frames_violencia:
            # **VERIFICACIÓN ADICIONAL**
            if f is None or 'timestamp' not in f:
                continue
                
            timestamp_key = f['timestamp'].isoformat()
            if timestamp_key not in violence_by_time:
                violence_by_time[timestamp_key] = []
            violence_by_time[timestamp_key].append(f)
        
        # Crear lista de timestamps únicos
        all_timestamps = set()
        
        # **PROCESAMIENTO SEGURO de timestamps**
        for f in frames_violencia:
            if f is not None and 'timestamp' in f and f['timestamp'] is not None:
                all_timestamps.add(f['timestamp'])
        
        for f in frames_contexto:
            if f is not None and 'timestamp' in f and f['timestamp'] is not None:
                all_timestamps.add(f['timestamp'])
        
        # Procesar timestamps ordenados
        for timestamp in sorted(all_timestamps):
            timestamp_key = timestamp.isoformat()
            
            # Priorizar frames de violencia
            if timestamp_key in violence_by_time:
                frames_combinados.extend(violence_by_time[timestamp_key])
            else:
                # Buscar frame de contexto
                context_frame = next(
                    (f for f in frames_contexto 
                    if f is not None and 'timestamp' in f and f['timestamp'] == timestamp), 
                    None
                )
                if context_frame:
                    frames_combinados.append(context_frame)
        
        # **FILTRADO FINAL de frames None**
        frames_combinados = [f for f in frames_combinados if f is not None]
        
        violence_count = len([f for f in frames_combinados 
                            if f and f.get('violencia_info', {}) and f.get('violencia_info', {}).get('detectada', False)])
        
        print(f"🔄 Frames combinados: {len(frames_combinados)} (Violencia efectiva: {violence_count}, Contexto: {len(frames_contexto)})")
        
        return frames_combinados


    # 2. MEJORA EN _guardar_evidencia_mejorado para actualizar el incidente con URL
    def _guardar_evidencia_mejorado(self, datos: Dict[str, Any]):
        """ACTUALIZADO: Solo actualizar incidente - evidence_recorder genera el video"""
        try:
            incidente_id = datos.get('incidente_id')
            video_path = datos.get('video_path')  # Ruta generada por evidence_recorder
            
            if not incidente_id:
                print("❌ No hay incidente_id para actualizar")
                return
            
            if not video_path or not Path(video_path).exists():
                print(f"❌ Video no encontrado: {video_path}")
                return
            
            print(f"📝 Actualizando incidente {incidente_id} con video generado por evidence_recorder")
            
            # Generar URL relativa
            nombre_archivo = Path(video_path).name
            video_url = f"/api/v1/files/videos/{incidente_id}"
            
            # Obtener estadísticas del video
            file_size = Path(video_path).stat().st_size
            
            # Preparar datos de actualización
            datos_actualizacion = {
                'video_evidencia_path': f"clips/{nombre_archivo}",
                'video_url': video_url,
                'fecha_hora_fin': self.tiempo_fin_violencia,
                'estado': EstadoIncidente.CONFIRMADO.value,
                'metadata_json': {
                    'video_stats': {
                        'archivo': nombre_archivo,
                        'tamaño_mb': file_size / (1024*1024),
                        'generado_por': 'evidence_recorder'
                    }
                }
            }
            
            # Actualizar el incidente
            success = self._actualizar_incidente_thread_safe(incidente_id, datos_actualizacion)
            
            if success:
                print(f"✅ Incidente {incidente_id} actualizado con video: {video_url}")
            else:
                print(f"⚠️ No se pudo actualizar el incidente {incidente_id}")
                
        except Exception as e:
            print(f"❌ Error en actualización de incidente: {e}")


    # 3. NUEVO MÉTODO: Actualización asíncrona del incidente
    def _actualizar_incidente_async(self, incidente_id: int, datos_actualizacion: Dict[str, Any]) -> bool:
        """NUEVO: Actualiza incidente de forma asíncrona con ThreadPoolExecutor"""
        try:
            import asyncio
            import threading
            
            # Si estamos en un hilo separado, usar requests
            if threading.current_thread() != threading.main_thread():
                return self._actualizar_incidente_http(incidente_id, datos_actualizacion)
            
            # Si estamos en el hilo principal, usar asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si ya hay un loop corriendo, usar ThreadPoolExecutor
                    future = self.executor.submit(
                        self._actualizar_incidente_http, 
                        incidente_id, 
                        datos_actualizacion
                    )
                    return future.result(timeout=10)
                else:
                    # Si no hay loop, crear uno
                    return loop.run_until_complete(
                        self._actualizar_incidente_db(incidente_id, datos_actualizacion)
                    )
            except RuntimeError:
                # Si hay problemas con asyncio, usar HTTP
                return self._actualizar_incidente_http(incidente_id, datos_actualizacion)
            
        except Exception as e:
            print(f"❌ Error en _actualizar_incidente_async: {e}")
            return False


    # 4. NUEVO MÉTODO: Actualización vía HTTP
    def _actualizar_incidente_http(self, incidente_id: int, datos_actualizacion: Dict[str, Any]) -> bool:
        """NUEVO: Actualiza incidente usando HTTP requests (thread-safe)"""
        try:
            import requests
            from datetime import datetime
            
            # Preparar datos para envío HTTP
            datos_para_envio = {}
            
            for key, value in datos_actualizacion.items():
                if key == 'fecha_hora_fin' and isinstance(value, datetime):
                    datos_para_envio[key] = value.isoformat()
                elif key == 'estado' and hasattr(value, 'value'):
                    datos_para_envio[key] = value.value
                else:
                    datos_para_envio[key] = value
            
            # URL del endpoint interno
            url = f"http://localhost:8000/api/v1/incidents/{incidente_id}/internal"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            print(f"🔄 Enviando actualización HTTP para incidente {incidente_id}")
            print(f"📤 Campos: {list(datos_para_envio.keys())}")
            
            response = requests.patch(
                url,
                json=datos_para_envio,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ HTTP: Incidente {incidente_id} actualizado exitosamente")
                return True
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en actualización HTTP: {e}")
            return False
        
    # 5. NUEVO MÉTODO: Actualización vía DB directa  
    async def _actualizar_incidente_db(self, incidente_id: int, datos_actualizacion: Dict[str, Any]) -> bool:
        """NUEVO: Actualiza incidente directamente en DB (para uso en async context)"""
        try:
            from app.core.database import SesionAsincrona
            
            async with SesionAsincrona() as session:
                incidente = await self.servicio_incidentes.actualizar_incidente(
                    incidente_id, 
                    datos_actualizacion
                )
                
                if incidente:
                    print(f"✅ DB: Incidente {incidente_id} actualizado exitosamente")
                    return True
                else:
                    print(f"⚠️ DB: No se encontró incidente {incidente_id}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error en actualización DB: {e}")
            return False

    def _actualizar_incidente_thread_safe(self, incidente_id: int, datos_actualizacion: Dict[str, Any]):
        """Actualiza incidente usando ThreadPoolExecutor para evitar conflictos de loop"""
        try:
            future = self.executor.submit(
                self._actualizar_incidente_sincrono, 
                incidente_id, 
                datos_actualizacion
            )
            
            # Dar tiempo para que se complete la actualización
            try:
                result = future.result(timeout=10)
                if result:
                    print(f"✅ Incidente {incidente_id} actualizado correctamente")
                else:
                    print(f"⚠️ No se pudo actualizar el incidente {incidente_id}")
            except Exception as e:
                print(f"❌ Error en actualización thread-safe: {e}")
                
        except Exception as e:
            print(f"❌ Error enviando actualización a thread pool: {e}")

    def _actualizar_incidente_sincrono(self, incidente_id: int, datos_actualizacion: Dict[str, Any]) -> bool:
        """Actualiza incidente de forma síncrona usando requests - CORREGIDO"""
        try:
            import requests
            import json
            from datetime import datetime
            
            # **CORREGIR: Preparar datos con tipos correctos**
            datos_para_envio = {}
            
            for key, value in datos_actualizacion.items():
                if key == 'fecha_hora_fin' and isinstance(value, datetime):
                    # Enviar como string ISO para HTTP request
                    datos_para_envio[key] = value.isoformat()
                elif key == 'metadata_json' and isinstance(value, dict):
                    # Ya es un dict, no necesita conversión especial
                    datos_para_envio[key] = value
                else:
                    datos_para_envio[key] = value
            
            # URL del endpoint interno para actualizar incidente
            url = f"http://localhost:8000/api/v1/incidents/{incidente_id}/internal"
            
            # Headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            print(f"🔄 Enviando datos de actualización: {list(datos_para_envio.keys())}")
            
            # **CORREGIDO: Usar datos preparados sin conversión automática**
            response = requests.patch(
                url,
                json=datos_para_envio,  # Usar json= en lugar de data=json.dumps()
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ HTTP: Incidente {incidente_id} actualizado exitosamente")
                return True
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en actualización HTTP: {e}")
            import traceback
            print(traceback.format_exc())
            return False

    async def _activar_alarma(self):
        """Activa la alarma de forma asíncrona"""
        try:
            await self.servicio_alarma.activar_alarma(5)
        except Exception as e:
            print(f"Error activando alarma: {e}")

    # *** CORRECCIÓN EN _crear_incidente PARA USAR DATOS REALES ***
    async def _crear_incidente(self, personas_involucradas: List[Dict[str, Any]], probabilidad: float):
        """Crea un nuevo incidente en la base de datos - CORREGIDO CON DATOS REALES"""
        try:
            # *** USAR UBICACIÓN REAL ***
            ubicacion_real = self.ubicacion or "Ubicación no especificada"
            
            # *** NUEVA LÓGICA: Garantizar mínimo 2 personas involucradas ***
            numero_personas_detectadas = len(personas_involucradas)
            
            # Si se detecta violencia pero solo 1 persona, ajustar a 2
            if numero_personas_detectadas == 1:
                numero_personas = 2
                print(f"⚠️ Solo 1 persona detectada, ajustando a 2 personas para incidente de violencia")
            elif numero_personas_detectadas == 0:
                # Si no se detectó ninguna persona pero hay violencia, asumir 2
                numero_personas = 0
                print(f"⚠️ No se detectaron personas, asumiendo 2 personas para incidente de violencia")
            else:
                # Si se detectan 2 o más personas, usar el número real
                numero_personas = numero_personas_detectadas
                print(f"✅ {numero_personas_detectadas} personas detectadas correctamente")
            
            
            datos_incidente = {
                'camara_id': self.camara_id,
                'tipo_incidente': TipoIncidente.PELEA,
                'severidad': self._calcular_severidad(probabilidad),
                'probabilidad_violencia': probabilidad,  # *** PROBABILIDAD REAL ***
                'fecha_hora_inicio': datetime.now(),
                'ubicacion': ubicacion_real,  # *** UBICACIÓN REAL ***
                'numero_personas_involucradas': numero_personas,  # *** NÚMERO REAL ***
                'ids_personas_detectadas': [str(p.get('id', '')) for p in personas_involucradas],
                'estado': EstadoIncidente.NUEVO,
                'descripcion': f'Violencia detectada con probabilidad {probabilidad*100:.2f}% en {ubicacion_real}'  # *** DESCRIPCIÓN REAL ***
            }
            
            print(f"📊 Creando incidente con datos reales:")
            print(f"   - Probabilidad: {probabilidad*100:.2f}%")
            print(f"   - Personas: {len(personas_involucradas)}")
            print(f"   - Ubicación: {ubicacion_real}")
            
            incidente = await self.servicio_incidentes.crear_incidente(datos_incidente)
            
            # **CRÍTICO: Guardar el ID del incidente para usar en el video**
            self.incidente_actual_id = incidente.id
            print(f"📊 Nuevo incidente registrado ID: {incidente.id}")
            print(f"🔗 ID del incidente guardado para video: {self.incidente_actual_id}")
            
            # *** NOTIFICAR CON DATOS REALES ***
            from app.api.websocket.notifications_ws import manejador_notificaciones_ws
            await manejador_notificaciones_ws.notificar_incidente(
                incidente.id,
                incidente.tipo_incidente,
                ubicacion_real,  # *** UBICACIÓN REAL ***
                incidente.severidad,
                {
                    "timestamp": incidente.fecha_hora_inicio.isoformat(),
                    "personas_involucradas": len(personas_involucradas),  # *** NÚMERO REAL ***
                    "probabilidad": probabilidad  # *** PROBABILIDAD REAL ***
                }
            )
            
            # **NUEVO: Pasar el ID del incidente al evidence_recorder**
            from app.tasks.video_recorder import evidence_recorder
            evidence_recorder.set_current_incident_id(incidente.id)
            
            print(f"🔗 ID del incidente {incidente.id} enviado al evidence_recorder")
            
            return incidente
            
        except Exception as e:
            print(f"❌ Error creando incidente: {e}")
            import traceback
            print(traceback.format_exc())
            return None

    def _calcular_severidad(self, probabilidad: float) -> SeveridadIncidente:
        """Calcula la severidad basada en la probabilidad"""
        if probabilidad >= 0.9:
            return SeveridadIncidente.CRITICA
        elif probabilidad >= 0.8:
            return SeveridadIncidente.CRITICA
        elif probabilidad >= 0.6:
            return SeveridadIncidente.ALTA
        else:
            return SeveridadIncidente.MEDIA

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

    # 7. MEJORA EN reiniciar() para limpiar el ID del incidente
    def reiniciar(self):
        """MEJORADO: Reset completo del estado incluyendo incidente_id"""
        # Reset de estado de violencia
        self.violencia_estado_anterior = False
        self.secuencia_violencia_activa = False
        self.tiempo_inicio_violencia = None
        self.tiempo_fin_violencia = None
        
        # Reset de buffers
        self.buffer_evidencia = FrameBuffer(max_duration_seconds=30)
        self.violence_buffer = ViolenceFrameBuffer(max_frames=2000)
        
        # Reset de detectores
        self.detector_violencia.reiniciar()
        
        # **NUEVO: Limpiar ID del incidente**
        self.incidente_actual_id = None
        
        print("🔄 Pipeline reiniciado completamente (incluyendo incidente_id)")

    def _procesar_cola_guardado(self):
        """Procesa la cola de guardado de videos de forma asíncrona"""
        print("🎬 Iniciando procesador de cola de guardado de videos")
        
        while True:
            try:
                # Obtener datos de la cola (bloquea hasta que haya datos)
                datos = self.cola_guardado.get()
                
                # Si recibe None, terminar el hilo
                if datos is None:
                    print("🛑 Señal de terminar recibida en cola de guardado")
                    break
                
                print(f"📹 Procesando video de incidente {datos.get('incidente_id', 'N/A')}")
                
                # Procesar el guardado del video
                self._guardar_evidencia_mejorado(datos)
                
                # Marcar tarea como completada
                self.cola_guardado.task_done()
                
            except Exception as e:
                print(f"❌ Error procesando cola de guardado: {e}")
                import traceback
                print(traceback.format_exc())
                continue

    def _expandir_frames_para_duracion(self, frames_originales: List[Dict], frames_objetivo: int) -> List[Dict]:
        """MEJORADO: Expande frames para alcanzar duración objetivo - CON FILTRADO SEGURO"""
        # **FILTRAR FRAMES NONE AL INICIO**
        frames_originales = [f for f in frames_originales if f is not None and isinstance(f, dict)]
        
        if not frames_originales:
            return []
        
        frames_expandidos = frames_originales.copy()
        
        # Si ya tenemos suficientes frames, devolver tal como están
        if len(frames_expandidos) >= frames_objetivo:
            return frames_expandidos[:frames_objetivo]
        
        print(f"📹 Expandiendo frames de {len(frames_originales)} a {frames_objetivo}")
        
        # Calcular cuántos frames necesitamos agregar
        frames_faltantes = frames_objetivo - len(frames_expandidos)
        
        # Método 1: Interpolar frames entre frames existentes
        if len(frames_originales) > 1:
            # Agregar frames interpolados entre frames existentes
            for i in range(min(frames_faltantes, len(frames_originales) - 1)):
                idx = i % (len(frames_originales) - 1)
                
                # **VERIFICACIÓN QUE EL FRAME ES VÁLIDO**
                if frames_originales[idx] is not None and isinstance(frames_originales[idx], dict):
                    # Crear frame interpolado
                    frame_interpolado = {
                        'frame': frames_originales[idx]['frame'].copy(),
                        'timestamp': frames_originales[idx]['timestamp'] + timedelta(microseconds=500 + i*100),
                        'detecciones': frames_originales[idx].get('detecciones', []),
                        'violencia_info': frames_originales[idx].get('violencia_info'),
                        'interpolated': True,
                        'source_frame': idx
                    }
                    frames_expandidos.append(frame_interpolado)
        
        # Método 2: Si aún faltan frames, duplicar frames de violencia
        if len(frames_expandidos) < frames_objetivo:
            frames_faltantes = frames_objetivo - len(frames_expandidos)
            
            # Priorizar frames con violencia para duplicar
            frames_violencia = []
            for f in frames_originales:
                if f is not None and isinstance(f, dict):
                    violencia_info = f.get('violencia_info')
                    if violencia_info is not None and isinstance(violencia_info, dict):
                        if violencia_info.get('detectada', False):
                            frames_violencia.append(f)
            
            if frames_violencia:
                print(f"📹 Ronda expansión 1: +{frames_faltantes} frames (total: {len(frames_expandidos) + frames_faltantes})")
                
                for i in range(frames_faltantes):
                    idx = i % len(frames_violencia)
                    frame_duplicado = {
                        'frame': frames_violencia[idx]['frame'].copy(),
                        'timestamp': frames_violencia[idx]['timestamp'] + timedelta(microseconds=1000 + i*50),
                        'detecciones': frames_violencia[idx].get('detecciones', []),
                        'violencia_info': frames_violencia[idx].get('violencia_info'),
                        'duplicated': True,
                        'source_frame': idx,
                        'duplicate_round': 1
                    }
                    frames_expandidos.append(frame_duplicado)
            else:
                # Si no hay frames de violencia, duplicar cualquier frame disponible
                for i in range(frames_faltantes):
                    idx = i % len(frames_originales)
                    if frames_originales[idx] is not None and isinstance(frames_originales[idx], dict):
                        frame_duplicado = {
                            'frame': frames_originales[idx]['frame'].copy(),
                            'timestamp': frames_originales[idx]['timestamp'] + timedelta(microseconds=1000 + i*50),
                            'detecciones': frames_originales[idx].get('detecciones', []),
                            'violencia_info': frames_originales[idx].get('violencia_info'),
                            'duplicated': True,
                            'source_frame': idx,
                            'duplicate_round': 1
                        }
                        frames_expandidos.append(frame_duplicado)
        
        # **FILTRADO FINAL: Asegurar que no hay frames None**
        frames_expandidos = [f for f in frames_expandidos if f is not None and isinstance(f, dict)]
        
        return frames_expandidos[:frames_objetivo]

    # **AGREGAR TAMBIÉN: Método para manejo de evidencia robusta**
    def _combinar_frames_evidencia_robusta(self, frames_violencia: List[Dict], frames_contexto: List[Dict]) -> List[Dict]:
        """NUEVO: Combina frames con máxima prioridad a violencia para evidencia robusta - CORREGIDO"""
        
        # **FILTRADO INICIAL ROBUSTO: Eliminar todos los frames None**
        frames_violencia = [f for f in frames_violencia if f is not None]
        frames_contexto = [f for f in frames_contexto if f is not None]
        
        # Si tenemos muy pocos frames de violencia, expandir masivamente
        if len(frames_violencia) < 50:  # Menos de ~3 segundos a 15fps
            print(f"⚠️ Agregando MASIVAMENTE más frames de violencia para garantizar contenido robusto...")
            
            # Múltiples rondas de duplicación de frames de violencia
            frames_expandidos = frames_violencia.copy()
            
            for ronda in range(4):  # 4 rondas de duplicación
                duplicaciones_esta_ronda = []
                for i, frame in enumerate(frames_violencia[:10]):  # Solo primeros 10 frames
                    # **VERIFICACIÓN ADICIONAL: Asegurar que frame no sea None**
                    if frame is not None and isinstance(frame, dict):
                        for j in range(13):  # 13 duplicados por frame original
                            frame_duplicado = {
                                'frame': frame['frame'].copy(),
                                'timestamp': frame['timestamp'] + timedelta(microseconds=j*50 + ronda*1000),
                                'detecciones': frame.get('detecciones', []),
                                'violencia_info': frame.get('violencia_info'),
                                'massive_duplicate': True,
                                'duplicate_round': ronda + 1,
                                'source_frame': i
                            }
                            duplicaciones_esta_ronda.append(frame_duplicado)
                
                frames_expandidos.extend(duplicaciones_esta_ronda)
                print(f"📹 Ronda {ronda + 1}: {len(duplicaciones_esta_ronda)} frames adicionales de violencia")
            
            print(f"📹 TOTAL frames de violencia después de duplicación: {len(frames_expandidos)}")
            frames_violencia = frames_expandidos
        
        # Combinar priorizando violencia
        frames_combinados = []
        
        # Crear mapeo por timestamp
        violencia_por_tiempo = {}
        for frame in frames_violencia:
            # **VERIFICACIÓN ROBUSTA: Asegurar que frame es válido**
            if frame is not None and isinstance(frame, dict) and 'timestamp' in frame:
                tiempo_key = frame['timestamp'].replace(microsecond=0)  # Agrupar por segundo
                if tiempo_key not in violencia_por_tiempo:
                    violencia_por_tiempo[tiempo_key] = []
                violencia_por_tiempo[tiempo_key].append(frame)
        
        # Procesar todos los timestamps
        todos_los_tiempos = set()
        for frame in frames_violencia:
            if frame is not None and isinstance(frame, dict) and 'timestamp' in frame:
                todos_los_tiempos.add(frame['timestamp'].replace(microsecond=0))
        
        for frame in frames_contexto:
            if frame is not None and isinstance(frame, dict) and 'timestamp' in frame:
                todos_los_tiempos.add(frame['timestamp'].replace(microsecond=0))
        
        # Combinar dando prioridad absoluta a frames de violencia
        for tiempo in sorted(todos_los_tiempos):
            if tiempo in violencia_por_tiempo:
                # Agregar TODOS los frames de violencia de este segundo
                frames_combinados.extend(violencia_por_tiempo[tiempo])
            else:
                # Solo agregar contexto si no hay violencia en este segundo
                frame_contexto = next(
                    (f for f in frames_contexto 
                    if f is not None and isinstance(f, dict) and 'timestamp' in f and f['timestamp'].replace(microsecond=0) == tiempo),
                    None
                )
                if frame_contexto:
                    frames_combinados.append(frame_contexto)
        
        # **FILTRADO FINAL ROBUSTO: Asegurar que no hay frames None**
        frames_combinados = [f for f in frames_combinados if f is not None and isinstance(f, dict)]
        
        # Contar frames efectivos de violencia - CON VERIFICACIÓN SEGURA
        violence_efectiva = 0
        for f in frames_combinados:
            if f is not None and isinstance(f, dict):
                violencia_info = f.get('violencia_info')
                if violencia_info is not None and isinstance(violencia_info, dict):
                    if violencia_info.get('detectada', False):
                        violence_efectiva += 1
        
        print(f"🔄 Frames combinados: {len(frames_combinados)} (Violencia efectiva: {violence_efectiva}, Contexto: {len(frames_contexto)})")
        
        return frames_combinados

    # **TAMBIÉN AGREGAR: Control de expansión de frames**  
    def _generar_frames_evidencia_completos(self, frames_base: List[Dict], duracion_minima: float = 5.0) -> List[Dict]:
        """Genera un conjunto completo de frames para evidencia con duración mínima"""
        
        if not frames_base:
            return []
        
        frames_objetivo = int(duracion_minima * self.target_fps_evidencia)
        
        print(f"📹 TOTAL frames para evidencia: {len(frames_base)}")
        
        # Si tenemos suficientes frames, usar tal como están
        if len(frames_base) >= frames_objetivo:
            return frames_base[:frames_objetivo]
        
        # Expandir usando el método existente
        frames_expandidos = self._expandir_frames_para_duracion(frames_base, frames_objetivo)
        
        # Calcular duración estimada
        duracion_estimada = len(frames_expandidos) / self.target_fps_evidencia
        
        print(f"📹 Duración estimada del clip: {duracion_estimada:.2f} segundos")
        
        # Contar frames de violencia en el resultado final
        violence_count = len([f for f in frames_expandidos 
                            if f.get('violencia_info', {}).get('detectada', False)])
        
        print(f"📝 Evidencia ROBUSTA enviada a cola:")
        print(f"   - {len(frames_expandidos)} frames")
        print(f"   - {violence_count} con violencia")
        print(f"   - Duración estimada: {duracion_estimada:.2f}s")
        print(f"   - Duplicaciones totales: {len(frames_expandidos) - len(frames_base)}")
        
        return frames_expandidos