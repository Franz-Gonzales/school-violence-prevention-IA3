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
    """Grabador de evidencia con MÁXIMA captura de frames de violencia"""
    
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
        
        # NUEVO: Control de estado de violencia para evitar repeticiones
        self.last_violence_state = False
        self.violence_sequence_count = 0
        
        # BUFFER PRINCIPAL MÁS GRANDE
        buffer_seconds = configuracion.EVIDENCE_BUFFER_SIZE_SECONDS
        max_frames = int(buffer_seconds * self.capture_fps)
        self.frame_buffer = deque(maxlen=max_frames)
        self.buffer_lock = threading.Lock()
        
        # BUFFER DE VIOLENCIA GIGANTE PARA MÁXIMA CAPTURA
        self.violence_sequence_buffer = deque(maxlen=2000)  # 2000 frames = ~100 segundos a 20fps
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
        self.min_duration_seconds = 5.0
        
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
            'last_video_duration': 0.0
        }
        
        # Configuración de interpolación
        self.interpolation_enabled = configuracion.EVIDENCE_FRAME_INTERPOLATION
        self.smooth_transitions = configuracion.EVIDENCE_SMOOTH_TRANSITIONS if hasattr(configuracion, 'EVIDENCE_SMOOTH_TRANSITIONS') else True
        self.temporal_smoothing = configuracion.EVIDENCE_TEMPORAL_SMOOTHING if hasattr(configuracion, 'EVIDENCE_TEMPORAL_SMOOTHING') else True
        
        # Crear directorio
        configuracion.VIDEO_EVIDENCE_PATH.mkdir(parents=True, exist_ok=True)
        
        print(f"📹 EvidenceRecorder MÁXIMA CAPTURA DE VIOLENCIA:")
        print(f"   - FPS Captura: {self.capture_fps}")
        print(f"   - FPS Video: {self.fps}")
        print(f"   - Buffer Principal: {max_frames} frames ({buffer_seconds}s)")
        print(f"   - Buffer Violencia: 2000 frames (~100s)")
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
        """VERSIÓN CORREGIDA: Controla mejor el estado de violencia"""
        current_time = time.time()
        time_since_last = current_time - self.last_frame_time
        
        # DETECTAR ESTADO DE VIOLENCIA
        violence_detected = violence_info and violence_info.get('detectada', False)
        
        # CONTROL MEJORADO DE TRANSICIONES DE ESTADO
        if violence_detected and not self.last_violence_state:
            # INICIO de violencia
            self.violence_active = True
            self.violence_start_time = current_time
            self.violence_sequence_count += 1
            self.last_violence_state = True
            print(f"🔥 VIOLENCIA ACTIVA INICIADA en Evidence Recorder (Secuencia #{self.violence_sequence_count})")
            
        elif not violence_detected and self.last_violence_state:
            # FIN de violencia
            self.violence_end_time = current_time
            self.last_violence_state = False
            print(f"🔄 VIOLENCIA FINALIZADA en Evidence Recorder")
        
        # CAPTURA SÚPER AGRESIVA DURANTE VIOLENCIA
        if self.violence_active or violence_detected:
            # Durante violencia: CAPTURAR TODOS LOS FRAMES
            should_accept = True
            self.stats['violence_frames_captured'] += 1
        else:
            # Normal: usar intervalo permisivo
            should_accept = time_since_last >= (self.capture_interval * 0.7)
        
        if not should_accept:
            return
        
        # Crear copia del frame con información de detección
        frame_copy = frame.copy()
        
        # Dibujar detecciones de personas
        for detection in detections:
            self._draw_detection(frame_copy, detection)
        
        # Dibujar información de violencia si existe CON OVERLAY MUY INTENSO
        if violence_info and violence_info.get('detectada'):
            frame_copy = self._draw_violence_overlay_intenso(frame_copy, violence_info)
        
        frame_data = {
            'frame': frame_copy,
            'timestamp': current_time,
            'datetime': datetime.now(),
            'detections': detections,
            'violence_info': violence_info,
            'frame_id': self.frame_counter,
            'time_since_last': time_since_last,
            'is_violence_frame': violence_detected,
            'violence_active': self.violence_active,
            'sequence_id': self.violence_sequence_count
        }
        
        # 1) Siempre alimentar el buffer principal
        with self.buffer_lock:
            self.frame_buffer.append(frame_data)

        # 2) Capturar TODOS los fotogramas de violencia
        violence_detected = violence_info and violence_info.get('detectada', False)
        if violence_detected:
            with self.violence_buffer_lock:
                self.violence_sequence_buffer.append(frame_data)

        # 3) Resto de lógica de inicio/parada de grabación
        # Si detectamos violencia y no estamos grabando, iniciar
        if violence_detected and not self.is_recording:
            self._start_recording(current_time)
        
        # Verificar si debemos finalizar la grabación
        if not violence_detected and self.is_recording and self.violence_end_time:
            tiempo_sin_violencia = current_time - self.violence_end_time
            if tiempo_sin_violencia >= 8.0:  # 8 segundos sin violencia
                # Resetear estado de violencia activa
                self.violence_active = False
                self._finish_recording()
        
        # Log de estadísticas cada 50 frames
        if self.frame_counter % 50 == 0:
            violence_count = len([f for f in self.frame_buffer if f.get('is_violence_frame', False)])
            print(f"📊 Buffer Principal: {len(self.frame_buffer)} frames")
            print(f"📊 Buffer Violencia: {len(self.violence_sequence_buffer)} frames")
            print(f"📊 Estado Violencia: {'ACTIVA' if self.violence_active else 'INACTIVA'}")
            print(f"📊 Densidad: {len(self.frame_buffer) / max(1, time_since_last * 30):.2f} fps")

    def _draw_violence_overlay_intenso(self, frame: np.ndarray, violence_info: Dict) -> np.ndarray:
        """Overlay MUY INTENSO para frames de violencia"""
        height, width = frame.shape[:2]
        probability = violence_info.get('probabilidad', 0.0)
        
        # Overlay rojo MUY INTENSO
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 150), (0, 0, 255), -1)
        frame = cv2.addWeighted(frame, 0.4, overlay, 0.6, 0)  # Más overlay
        
        # Texto SÚPER GRANDE y VISIBLE
        cv2.putText(
            frame, 
            "*** VIOLENCIA DETECTADA ***", 
            (20, 50), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.8, 
            (255, 255, 255), 
            6,
            cv2.LINE_AA
        )
        
        # Probabilidad MUY DESTACADA
        cv2.putText(
            frame, 
            f"PROBABILIDAD: {probability:.1%}", 
            (20, 100), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.4, 
            (0, 255, 255), 
            5,
            cv2.LINE_AA
        )
        
        # Timestamp con milisegundos
        timestamp_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        cv2.putText(
            frame, 
            f"TIEMPO: {timestamp_str}", 
            (20, 135), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.9, 
            (255, 255, 255), 
            3,
            cv2.LINE_AA
        )
        
        return frame
    
    def _start_recording(self, violence_time: float):
        """Inicia la grabación EXTENDIDA para máxima captura"""
        if self.is_recording:
            return
        
        self.violence_start_time = violence_time
        self.is_recording = True
        
        print(f"🚨 Iniciando grabación de evidencia EXTENDIDA")
        print(f"📊 Buffer principal: {len(self.frame_buffer)} frames")
        print(f"📊 Buffer violencia: {len(self.violence_sequence_buffer)} frames")
        
        # TIEMPO DE GRABACIÓN MUY EXTENDIDO para capturar TODO
        total_recording_time = configuracion.EVIDENCE_PRE_INCIDENT_SECONDS + configuracion.EVIDENCE_POST_INCIDENT_SECONDS + 15
        total_recording_time = max(total_recording_time, 12.0)  # Mínimo 12 segundos
        
        print(f"📊 Tiempo total de grabación: {total_recording_time}s")
        
        # Programar finalización automática
        finish_timer = threading.Timer(total_recording_time, self._finish_recording)
        finish_timer.start()
    
    def _extract_evidence_frames(self) -> List[Dict]:
        """Prioriza todo el contenido de violencia y lo expande si es necesario"""
        # 1) Tomamos ambos buffers
        with self.buffer_lock:
            main_frames = list(self.frame_buffer)
        with self.violence_buffer_lock:
            violence_frames = list(self.violence_sequence_buffer)

        # 2) Si hay muy pocos fotogramas de violencia, los duplicamos para darles peso
        target_vf = int(self.fps * 1)  # al menos 1 segundo de violencia
        if len(violence_frames) and len(violence_frames) < target_vf:
            dup_factor = (target_vf + len(violence_frames) - 1) // len(violence_frames)
            extended = []
            span = (violence_frames[-1]['timestamp'] - violence_frames[0]['timestamp']) if len(violence_frames)>1 else timedelta(milliseconds=100)
            for vf in violence_frames:
                for i in range(dup_factor):
                    dup = vf.copy()
                    dup['timestamp'] = vf['timestamp'] + span * (i / dup_factor)
                    extended.append(dup)
            violence_frames = violence_frames + extended

        # 3) Combinar: primero todos los de violencia, luego contexto
        combined = { (f['timestamp'], f['frame_id']): f for f in main_frames }
        for vf in violence_frames:
            combined[(vf['timestamp'], vf['frame_id'])] = vf

        frames = sorted(combined.values(), key=lambda x: x['timestamp'])

        # 4) Garantizar mínima duración
        start = violence_frames[0]['timestamp'] - timedelta(seconds=self.min_duration_seconds/2) if violence_frames else frames[0]['timestamp']
        end   = violence_frames[-1]['timestamp'] + timedelta(seconds=self.min_duration_seconds/2) if violence_frames else frames[-1]['timestamp']
        selected = [f for f in frames if start <= f['timestamp'] <= end]

        return selected
    
    def _finish_recording(self):
        """Finaliza la grabación con verificación de contenido de violencia"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # Extraer frames relevantes del buffer MEJORADO
        evidence_frames = self._extract_evidence_frames()
        
        if evidence_frames:
            violence_frames_count = sum(1 for f in evidence_frames if f.get('is_violence_frame'))
            
            # VERIFICAR que hay suficiente contenido de violencia
            if len(evidence_frames) >= (self.min_duration_seconds * 8) and violence_frames_count >= 2:
                save_data = {
                    'frames': evidence_frames,
                    'violence_time': self.violence_start_time,
                    'timestamp': datetime.now(),
                    'buffer_density': self.stats['buffer_density'],
                    'violence_frames_count': violence_frames_count,
                    'violence_sequences': self.stats['violence_sequences'],
                    'min_duration_guarantee': self.min_duration_seconds
                }
                
                try:
                    self.save_queue.put_nowait(save_data)
                    duration_estimate = len(evidence_frames) / self.fps
                    print(f"📝 Evidencia CON VIOLENCIA enviada a cola:")
                    print(f"   - {len(evidence_frames)} frames")
                    print(f"   - {violence_frames_count} con violencia")
                    print(f"   - Duración estimada: {duration_estimate:.2f}s")
                except queue.Full:
                    print("⚠️ Cola de guardado llena - evidencia perdida")
            else:
                print(f"⚠️ Evidencia rechazada: insuficientes frames ({len(evidence_frames)}) o poca violencia ({violence_frames_count})")
        
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
        """Guarda el video con MÁXIMO contenido de violencia"""
        frames = save_data['frames']
        if not frames:
            return
        
        # Obtener configuración de evidencia desde config
        evidence_config = configuracion.obtener_configuracion_evidencia()
        
        # Generar nombre de archivo con información de violencia
        timestamp = save_data['timestamp'].strftime("%Y%m%d_%H%M%S")
        violence_frames = save_data.get('violence_frames_count', 0)
        sequences = save_data.get('violence_sequences', 0)
        estimated_duration = len(frames) / self.fps
        
        filename = f"violence_evidence_{timestamp}_f{len(frames)}_v{violence_frames}_d{estimated_duration:.1f}s.{configuracion.VIDEO_CONTAINER}"
        filepath = configuracion.VIDEO_EVIDENCE_PATH / "clips" / filename
        
        # Crear directorio si no existe
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"💾 Guardando evidencia CON MÁXIMA VIOLENCIA:")
            print(f"📊 Frames totales: {len(frames)}")
            print(f"📊 Frames de violencia: {violence_frames}")
            print(f"📊 Duración estimada: {estimated_duration:.2f}s")
            print(f"📊 Garantía mínima: {save_data.get('min_duration_guarantee', 5)}s")
            
            # USAR FRAMES DIRECTOS para preservar TODA la violencia
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
            violence_frames_written = 0
            for frame_data in smooth_frames:
                frame = frame_data['frame']
                
                # Asegurar dimensiones correctas
                if frame.shape[:2] != (self.frame_height, self.frame_width):
                    frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                
                video_writer.write(frame)
                frames_written += 1
                
                if frame_data.get('is_violence_frame', False):
                    violence_frames_written += 1
            
            video_writer.release()
            
            # Verificar archivo y estadísticas FINALES
            if filepath.exists() and frames_written > 0:
                file_size = filepath.stat().st_size / (1024 * 1024)
                final_duration = frames_written / target_fps
                effective_fps = frames_written / final_duration
                self.stats['videos_saved'] += 1
                
                print(f"✅ Evidencia CON MÁXIMA VIOLENCIA guardada: {filename}")
                print(f"📊 {frames_written} frames escritos")
                print(f"📊 {violence_frames_written} frames de violencia escritos")
                print(f"📊 Duración FINAL: {final_duration:.2f}s")
                print(f"📊 FPS efectivo: {effective_fps:.2f}")
                print(f"📊 Tamaño archivo: {file_size:.2f}MB")
                print(f"📊 Densidad de violencia: {(violence_frames_written/frames_written)*100:.1f}%")
                
                # VERIFICAR CUMPLIMIENTO DE GARANTÍA
                min_required = save_data.get('min_duration_guarantee', 5)
                if final_duration >= min_required and violence_frames_written >= 2:
                    print(f"✅ GARANTÍA CUMPLIDA: {final_duration:.2f}s >= {min_required}s con {violence_frames_written} frames de violencia")
                else:
                    print(f"⚠️ GARANTÍA PARCIAL: {final_duration:.2f}s, {violence_frames_written} frames de violencia")
            else:
                print(f"❌ Error: No se generó el archivo correctamente")
            
        except Exception as e:
            logger.error(f"Error guardando evidencia: {e}")
    
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