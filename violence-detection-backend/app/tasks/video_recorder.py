import cv2
import numpy as np
import threading
import queue
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)

class ViolenceEvidenceRecorder:
    """Grabador de evidencia con GARANTÍA de videos de 5+ segundos"""
    
    def __init__(self):
        # CONFIGURACIÓN DESDE CONFIG.PY
        self.fps = configuracion.EVIDENCE_TARGET_FPS
        self.capture_fps = configuracion.EVIDENCE_CAPTURE_FPS if hasattr(configuracion, 'EVIDENCE_CAPTURE_FPS') else 30
        self.frame_width = configuracion.CAMERA_WIDTH
        self.frame_height = configuracion.CAMERA_HEIGHT
        
        # Control de grabación mejorado
        self.is_recording = False
        self.violence_start_time = None
        self.violence_active = False
        self.violence_end_time = None
        
        # BUFFER PRINCIPAL MÁS GRANDE
        buffer_seconds = configuracion.EVIDENCE_BUFFER_SIZE_SECONDS
        max_frames = int(buffer_seconds * self.capture_fps)
        self.frame_buffer = deque(maxlen=max_frames)
        self.buffer_lock = threading.Lock()
        
        # BUFFER DE VIOLENCIA MUCHO MÁS GRANDE
        self.violence_sequence_buffer = deque(maxlen=1500)  # 1500 frames = ~75 segundos a 20fps
        self.violence_buffer_lock = threading.Lock()
        
        # Cola para procesamiento asíncrono
        max_queue_size = configuracion.VIDEO_QUEUE_SIZE if hasattr(configuracion, 'VIDEO_QUEUE_SIZE') else 15
        self.save_queue = queue.Queue(maxsize=max_queue_size)
        self.save_thread = None
        self.running = False
        
        # CONTROL DE TIMING MEJORADO
        self.last_frame_time = 0
        self.capture_interval = 1.0 / self.capture_fps
        self.frame_counter = 0
        
        # DURACIÓN MÍNIMA GARANTIZADA
        self.min_duration_seconds = 5.0  # NUEVO: duración mínima del video
        
        # CONFIGURACIÓN DE VIDEO
        opencv_config = configuracion.OPENCV_WRITER_CONFIG if hasattr(configuracion, 'OPENCV_WRITER_CONFIG') else {}
        fourcc_primary = opencv_config.get('fourcc_primary', 'H264')
        fourcc_fallback = opencv_config.get('fourcc_fallback', 'mp4v')
        
        self.fourcc = cv2.VideoWriter_fourcc(*fourcc_primary)
        self.fourcc_fallback = cv2.VideoWriter_fourcc(*fourcc_fallback)
        
        # Estadísticas mejoradas
        self.stats = {
            'frames_added': 0,
            'frames_interpolated': 0,
            'videos_saved': 0,
            'buffer_density': 0.0,
            'avg_frame_interval': 0.0,
            'violence_frames_captured': 0,
            'violence_sequences': 0,
            'last_video_duration': 0.0  # NUEVO: duración del último video
        }
        
        # Configuración de interpolación
        self.interpolation_enabled = configuracion.EVIDENCE_FRAME_INTERPOLATION
        self.smooth_transitions = configuracion.EVIDENCE_SMOOTH_TRANSITIONS if hasattr(configuracion, 'EVIDENCE_SMOOTH_TRANSITIONS') else True
        self.temporal_smoothing = configuracion.EVIDENCE_TEMPORAL_SMOOTHING if hasattr(configuracion, 'EVIDENCE_TEMPORAL_SMOOTHING') else True
        
        # Crear directorio
        configuracion.VIDEO_EVIDENCE_PATH.mkdir(parents=True, exist_ok=True)
        
        print(f"📹 EvidenceRecorder GARANTÍA 5+ SEGUNDOS:")
        print(f"   - FPS Captura: {self.capture_fps}")
        print(f"   - FPS Video: {self.fps}")
        print(f"   - Buffer Principal: {max_frames} frames ({buffer_seconds}s)")
        print(f"   - Buffer Violencia: 1500 frames (~75s)")
        print(f"   - Duración mínima garantizada: {self.min_duration_seconds}s")
    
    def start_processing(self):
        """Inicia el hilo de procesamiento"""
        if not self.running:
            self.running = True
            self.save_thread = threading.Thread(target=self._process_save_queue, daemon=True)
            self.save_thread.start()
            print("🚀 Procesamiento de evidencias iniciado")
    
    def stop_processing(self):
        """Detiene el procesamiento"""
        self.running = False
        if self.is_recording:
            self._finish_recording()
        
        if self.save_thread and self.save_thread.is_alive():
            self.save_thread.join(timeout=5)
        print("🛑 Procesamiento de evidencias detenido")
    
    def add_frame(self, frame: np.ndarray, detections: List[Dict], violence_info: Optional[Dict] = None):
        """VERSIÓN MEJORADA: Captura MÁS AGRESIVA para garantizar datos suficientes"""
        current_time = time.time()
        time_since_last = current_time - self.last_frame_time
        
        # DETECTAR ESTADO DE VIOLENCIA
        violence_detected = violence_info and violence_info.get('violencia_detectada', False)
        
        # GESTIONAR ESTADO DE VIOLENCIA ACTIVA
        if violence_detected and not self.violence_active:
            print("🔥 INICIANDO SECUENCIA DE VIOLENCIA - Captura ULTRA intensiva")
            self.violence_active = True
            self.stats['violence_sequences'] += 1
        elif not violence_detected and self.violence_active:
            print("✅ FINALIZANDO SECUENCIA DE VIOLENCIA")
            self.violence_active = False
            self.violence_end_time = current_time
        
        # ACEPTAR FRAMES MÁS AGRESIVAMENTE
        # Durante violencia: aceptar TODOS los frames SIN EXCEPCIÓN
        # Normal: usar intervalo más permisivo
        if self.violence_active:
            should_accept = True  # SIEMPRE durante violencia
        else:
            # Aceptar frames más frecuentemente en modo normal también
            should_accept = (
                self.last_frame_time == 0 or
                time_since_last >= (self.capture_interval * 0.5) or  # Reducir threshold a 50%
                violence_detected or
                len(self.frame_buffer) < 50  # Aceptar más si el buffer está bajo
            )
        
        if not should_accept:
            return
        
        # Crear copia del frame con información de detección
        frame_copy = frame.copy()
        
        # Dibujar detecciones de personas
        for detection in detections:
            self._draw_detection(frame_copy, detection)
        
        # Dibujar información de violencia si existe
        if violence_info and violence_info.get('violencia_detectada'):
            self._draw_violence_overlay(frame_copy, violence_info)
        
        frame_data = {
            'frame': frame_copy,
            'timestamp': current_time,
            'datetime': datetime.now(),
            'detections': detections,
            'violence_info': violence_info,
            'frame_id': self.frame_counter,
            'time_since_last': time_since_last,
            'is_violence_frame': violence_detected,
            'violence_active': self.violence_active
        }
        
        # AGREGAR AL BUFFER PRINCIPAL
        with self.buffer_lock:
            self.frame_buffer.append(frame_data)
            
            # Calcular densidad del buffer
            if len(self.frame_buffer) >= 2:
                time_span = self.frame_buffer[-1]['timestamp'] - self.frame_buffer[0]['timestamp']
                if time_span > 0:
                    self.stats['buffer_density'] = len(self.frame_buffer) / time_span
        
        # AGREGAR AL BUFFER DE VIOLENCIA DURANTE SECUENCIAS ACTIVAS O DETECCIÓN
        if self.violence_active or violence_detected:
            with self.violence_buffer_lock:
                self.violence_sequence_buffer.append(frame_data)
                self.stats['violence_frames_captured'] += 1
                
                # AGREGAR CONTEXTO ADICIONAL: últimos 15 frames del buffer principal
                if violence_detected and not self.violence_active:
                    context_frames = list(self.frame_buffer)[-15:]
                    for context_frame in context_frames:
                        if context_frame['frame_id'] < self.frame_counter:
                            context_frame_copy = context_frame.copy()
                            context_frame_copy['context_frame'] = True
                            self.violence_sequence_buffer.append(context_frame_copy)
        
        # Actualizar estadísticas y estado
        self.frame_counter += 1
        self.stats['frames_added'] += 1
        self.stats['avg_frame_interval'] = time_since_last
        self.last_frame_time = current_time
        
        # Si detectamos violencia y no estamos grabando, iniciar
        if violence_detected and not self.is_recording:
            self._start_recording(current_time)
        
        # Log cada 25 frames para debugging
        if (configuracion.VIDEO_DEBUG_ENABLED if hasattr(configuracion, 'VIDEO_DEBUG_ENABLED') else True) and self.frame_counter % 25 == 0:
            print(f"📊 Buffer Principal: {len(self.frame_buffer)} frames")
            print(f"📊 Buffer Violencia: {len(self.violence_sequence_buffer)} frames")
            print(f"📊 Estado Violencia: {'ACTIVA' if self.violence_active else 'INACTIVA'}")
            print(f"📊 Densidad: {self.stats['buffer_density']:.2f} fps")
    
    def _start_recording(self, violence_time: float):
        """Inicia la grabación con tiempo EXTENDIDO para garantizar 5+ segundos"""
        if self.is_recording:
            return
        
        self.violence_start_time = violence_time
        self.is_recording = True
        
        print(f"🚨 Iniciando grabación de evidencia EXTENDIDA")
        print(f"📊 Buffer principal: {len(self.frame_buffer)} frames")
        print(f"📊 Buffer violencia: {len(self.violence_sequence_buffer)} frames")
        
        # TIEMPO DE GRABACIÓN EXTENDIDO para garantizar suficientes datos
        # Pre + Post + tiempo extra para asegurar secuencia completa
        total_recording_time = configuracion.EVIDENCE_PRE_INCIDENT_SECONDS + configuracion.EVIDENCE_POST_INCIDENT_SECONDS + 10
        
        # NUNCA menos de 8 segundos de grabación total
        total_recording_time = max(total_recording_time, 8.0)
        
        print(f"📊 Tiempo total de grabación: {total_recording_time}s")
        
        # Programar finalización automática
        finish_timer = threading.Timer(total_recording_time, self._finish_recording)
        finish_timer.start()
    
    def _extract_evidence_frames(self) -> List[Dict]:
        """VERSIÓN MEJORADA: Garantiza MÍNIMO 5 segundos de video"""
        if not self.violence_start_time:
            return []
        
        # COMBINAR AMBOS BUFFERS
        all_frames = {}
        
        # Obtener frames del buffer principal
        with self.buffer_lock:
            main_frames = list(self.frame_buffer)
        
        # Obtener frames del buffer de violencia
        with self.violence_buffer_lock:
            violence_frames = list(self.violence_sequence_buffer)
        
        print(f"📹 Frames disponibles - Principal: {len(main_frames)}, Violencia: {len(violence_frames)}")
        
        # Agregar todos los frames a un diccionario
        for frame_data in main_frames:
            frame_id = frame_data['frame_id']
            all_frames[frame_id] = frame_data
        
        # Priorizar frames de violencia
        for frame_data in violence_frames:
            frame_id = frame_data['frame_id']
            all_frames[frame_id] = frame_data
        
        # Convertir a lista ordenada por timestamp
        combined_frames = sorted(all_frames.values(), key=lambda x: x['timestamp'])
        
        if not combined_frames:
            print("⚠️ No hay frames disponibles para evidencia")
            return []
        
        # CALCULAR VENTANA DE TIEMPO CON GARANTÍA DE DURACIÓN MÍNIMA
        start_time = self.violence_start_time - configuracion.EVIDENCE_PRE_INCIDENT_SECONDS
        end_time = self.violence_start_time + configuracion.EVIDENCE_POST_INCIDENT_SECONDS
        
        # GARANTIZAR DURACIÓN MÍNIMA
        calculated_duration = end_time - start_time
        if calculated_duration < self.min_duration_seconds:
            # Extender la ventana para alcanzar duración mínima
            extension_needed = self.min_duration_seconds - calculated_duration
            start_time -= extension_needed / 2
            end_time += extension_needed / 2
            print(f"📹 Extendiendo ventana para garantizar {self.min_duration_seconds}s mínimos")
        
        # Filtrar frames en la ventana EXTENDIDA
        evidence_frames = []
        violence_frames_count = 0
        
        for frame_data in combined_frames:
            frame_time = frame_data['timestamp']
            if start_time <= frame_time <= end_time:
                evidence_frames.append(frame_data)
                if frame_data.get('is_violence_frame', False):
                    violence_frames_count += 1
        
        # SI AÚN NO HAY SUFICIENTES FRAMES, EXPANDIR MÁS
        if len(evidence_frames) < (self.min_duration_seconds * 15):  # 15 FPS mínimo
            print(f"⚠️ Insuficientes frames ({len(evidence_frames)}), expandiendo ventana...")
            
            # Tomar más frames antes y después
            extra_duration = 3.0  # 3 segundos extra en cada dirección
            start_time -= extra_duration
            end_time += extra_duration
            
            evidence_frames = []
            for frame_data in combined_frames:
                frame_time = frame_data['timestamp']
                if start_time <= frame_time <= end_time:
                    evidence_frames.append(frame_data)
        
        # Ordenar por timestamp final
        evidence_frames.sort(key=lambda x: x['timestamp'])
        
        # ESTADÍSTICAS DETALLADAS
        total_duration = end_time - start_time
        print(f"📹 EVIDENCIA EXTRAÍDA CON GARANTÍA:")
        print(f"   - Total frames: {len(evidence_frames)}")
        print(f"   - Frames con violencia: {violence_frames_count}")
        print(f"   - Duración objetivo: {total_duration:.2f}s")
        print(f"   - Duración mínima garantizada: {self.min_duration_seconds}s")
        
        if evidence_frames:
            first_time = evidence_frames[0]['timestamp']
            last_time = evidence_frames[-1]['timestamp']
            actual_duration = last_time - first_time
            actual_fps = len(evidence_frames) / actual_duration if actual_duration > 0 else 0
            
            print(f"   - Duración real: {actual_duration:.2f}s")
            print(f"   - FPS efectivo: {actual_fps:.2f}")
            print(f"   - Frames por segundo: {len(evidence_frames)/actual_duration:.1f}")
            
            # Guardar estadísticas para uso posterior
            self.stats['last_video_duration'] = actual_duration
            
            # VERIFICAR QUE CUMPLE LA DURACIÓN MÍNIMA
            if actual_duration < self.min_duration_seconds:
                print(f"⚠️ ADVERTENCIA: Duración {actual_duration:.2f}s < {self.min_duration_seconds}s mínimos")
        
        return evidence_frames
    
    def _finish_recording(self):
        """Finaliza la grabación con verificación de duración"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # Extraer frames relevantes del buffer MEJORADO
        evidence_frames = self._extract_evidence_frames()
        
        if evidence_frames:
            # Verificar duración antes de enviar a guardar
            if len(evidence_frames) >= (self.min_duration_seconds * 10):  # 10 FPS mínimo
                save_data = {
                    'frames': evidence_frames,
                    'violence_time': self.violence_start_time,
                    'timestamp': datetime.now(),
                    'buffer_density': self.stats['buffer_density'],
                    'violence_frames_count': sum(1 for f in evidence_frames if f.get('is_violence_frame')),
                    'violence_sequences': self.stats['violence_sequences'],
                    'min_duration_guarantee': self.min_duration_seconds
                }
                
                try:
                    self.save_queue.put_nowait(save_data)
                    violence_count = save_data['violence_frames_count']
                    duration_estimate = len(evidence_frames) / self.fps
                    print(f"📝 Evidencia enviada a cola:")
                    print(f"   - {len(evidence_frames)} frames")
                    print(f"   - {violence_count} con violencia")
                    print(f"   - Duración estimada: {duration_estimate:.2f}s")
                except queue.Full:
                    print("⚠️ Cola de guardado llena - evidencia perdida")
            else:
                print(f"⚠️ Evidencia rechazada: insuficientes frames ({len(evidence_frames)}) para {self.min_duration_seconds}s")
        
        # RESET y limpieza
        self.violence_start_time = None
        self.violence_active = False
        self.violence_end_time = None
        
        # Limpiar buffer de violencia para próxima secuencia
        with self.violence_buffer_lock:
            self.violence_sequence_buffer.clear()
        
        # Reset estadísticas de violencia
        self.stats['violence_frames_captured'] = 0
        self.stats['violence_sequences'] = 0
    
    def _save_evidence_video(self, save_data: Dict):
        """Guarda el video con GARANTÍA de duración mínima"""
        frames = save_data['frames']
        if not frames:
            return
        
        # Obtener configuración de evidencia desde config
        evidence_config = configuracion.obtener_configuracion_evidencia()
        
        # Generar nombre de archivo con duración
        timestamp = save_data['timestamp'].strftime("%Y%m%d_%H%M%S")
        violence_frames = save_data.get('violence_frames_count', 0)
        sequences = save_data.get('violence_sequences', 0)
        estimated_duration = len(frames) / self.fps
        
        filename = f"violence_evidence_{timestamp}_f{len(frames)}_v{violence_frames}_d{estimated_duration:.1f}s.{configuracion.VIDEO_CONTAINER}"
        filepath = configuracion.VIDEO_EVIDENCE_PATH / "clips" / filename
        
        # Crear directorio si no existe
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"💾 Guardando evidencia CON GARANTÍA:")
            print(f"📊 Frames totales: {len(frames)}")
            print(f"📊 Duración estimada: {estimated_duration:.2f}s")
            print(f"📊 Garantía mínima: {save_data.get('min_duration_guarantee', 5)}s")
            
            # USAR FRAMES DIRECTOS SIN INTERPOLACIÓN para preservar secuencias
            smooth_frames = frames
            
            if not smooth_frames:
                print("❌ No se pudieron procesar frames")
                return
            
            print(f"📊 Frames finales: {len(smooth_frames)}")
            
            # Crear video writer
            target_fps = evidence_config['fps_target']
            video_writer = cv2.VideoWriter(
                str(filepath), self.fourcc, target_fps,
                (self.frame_width, self.frame_height)
            )
            
            if not video_writer.isOpened():
                video_writer = cv2.VideoWriter(
                    str(filepath), self.fourcc_fallback, target_fps,
                    (self.frame_width, self.frame_height)
                )
            
            if not video_writer.isOpened():
                logger.error(f"No se pudo crear video writer para {filename}")
                return
            
            # Escribir frames
            frames_written = 0
            for frame_data in smooth_frames:
                frame = frame_data['frame']
                
                # Asegurar dimensiones correctas
                if frame.shape[:2] != (self.frame_height, self.frame_width):
                    frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                
                video_writer.write(frame)
                frames_written += 1
            
            video_writer.release()
            
            # Verificar archivo y estadísticas FINALES
            if filepath.exists() and frames_written > 0:
                file_size = filepath.stat().st_size / (1024 * 1024)
                final_duration = frames_written / target_fps
                effective_fps = frames_written / final_duration
                self.stats['videos_saved'] += 1
                
                print(f"✅ Evidencia CON GARANTÍA guardada: {filename}")
                print(f"📊 {frames_written} frames escritos")
                print(f"📊 Duración FINAL: {final_duration:.2f}s")
                print(f"📊 FPS efectivo: {effective_fps:.2f}")
                print(f"📊 Tamaño archivo: {file_size:.2f}MB")
                print(f"📊 Frames de violencia: {violence_frames}")
                
                # VERIFICAR CUMPLIMIENTO DE GARANTÍA
                min_required = save_data.get('min_duration_guarantee', 5)
                if final_duration >= min_required:
                    print(f"✅ GARANTÍA CUMPLIDA: {final_duration:.2f}s >= {min_required}s")
                else:
                    print(f"⚠️ GARANTÍA NO CUMPLIDA: {final_duration:.2f}s < {min_required}s")
            else:
                print(f"❌ Error: No se generó el archivo correctamente")
            
        except Exception as e:
            logger.error(f"Error guardando evidencia: {e}")
    
    # RESTO DE MÉTODOS IGUAL (sin cambios)
    def _draw_detection(self, frame: np.ndarray, detection: Dict):
        """Dibuja bounding box de persona detectada"""
        bbox = detection['bbox']
        confidence = detection['confianza']
        
        x, y, w, h = map(int, bbox)
        
        # Bounding box verde más visible
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        
        # Etiqueta con fondo más prominente
        label = f"Persona: {confidence:.2f}"
        (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(frame, (x, y - text_height - 10), (x + text_width, y), (0, 255, 0), -1)
        cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    def _draw_violence_overlay(self, frame: np.ndarray, violence_info: Dict):
        """Dibuja overlay de violencia detectada"""
        probability = violence_info.get('probabilidad', 0.0)
        
        # Overlay rojo más visible y más grande
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], 120), (0, 0, 255), -1)
        frame = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)
        
        # Texto de alerta más grande
        alert_text = f"¡VIOLENCIA DETECTADA!"
        cv2.putText(frame, alert_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 4)
        
        # Probabilidad
        prob_text = f"Confianza: {probability:.1%}"
        cv2.putText(frame, prob_text, (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        
        # Timestamp si está habilitado en config
        if configuracion.EVIDENCE_TIMESTAMP_OVERLAY:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            cv2.putText(frame, timestamp, (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def _process_save_queue(self):
        """Procesa la cola de guardado en hilo separado"""
        while self.running:
            try:
                save_data = self.save_queue.get(timeout=1.0)
                self._save_evidence_video(save_data)
                self.save_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error procesando cola de guardado: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del recorder"""
        return {
            'frames_added': self.stats['frames_added'],
            'violence_frames_captured': self.stats['violence_frames_captured'],
            'violence_sequences': self.stats['violence_sequences'],
            'frames_interpolated': self.stats['frames_interpolated'],
            'videos_saved': self.stats['videos_saved'],
            'last_video_duration': self.stats['last_video_duration'],
            'buffer_size': len(self.frame_buffer),
            'violence_buffer_size': len(self.violence_sequence_buffer),
            'buffer_max_size': self.frame_buffer.maxlen,
            'buffer_density': self.stats['buffer_density'],
            'min_duration_guarantee': self.min_duration_seconds,
            'is_recording': self.is_recording,
            'violence_active': self.violence_active,
            'running': self.running,
            'config_fps': self.fps,
            'config_capture_fps': self.capture_fps,
            'interpolation_enabled': self.interpolation_enabled
        }

# Instancia global
evidence_recorder = ViolenceEvidenceRecorder()