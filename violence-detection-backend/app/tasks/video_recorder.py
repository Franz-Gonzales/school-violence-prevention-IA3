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
        """VERSIÓN MEJORADA: Prioriza captura agresiva de frames con violencia"""
        current_time = time.time()
        time_since_last = current_time - self.last_frame_time
        
        # DETECTAR ESTADO DE VIOLENCIA
        violence_detected = violence_info and violence_info.get('detectada', False)
        
        # CONTROL MEJORADO DE TRANSICIONES DE ESTADO
        if violence_detected and not self.last_violence_state:
            self.violence_active = True
            self.violence_start_time = datetime.now()
            self.last_violence_state = True
            self.violence_sequence_count += 1
            
            print(f"🔥 VIOLENCIA ACTIVA INICIADA en Evidence Recorder (Secuencia #{self.violence_sequence_count})")
            
            # NUEVO: Iniciar grabación inmediatamente al detectar violencia
            if not self.is_recording:
                self._start_recording(current_time)
                
        elif not violence_detected and self.last_violence_state:
            # Solo finalizar estado de violencia después de un periodo de enfriamiento
            if not hasattr(self, 'violence_cooldown_time') or current_time - self.violence_cooldown_time > 2.0:
                self.violence_active = False
                self.violence_end_time = datetime.now()
                self.last_violence_state = False
                print(f"🔄 VIOLENCIA FINALIZADA en Evidence Recorder")
        
        # CAPTURA SÚPER AGRESIVA DURANTE VIOLENCIA - SIEMPRE ACEPTAR FRAMES DE VIOLENCIA
        should_accept = True
        if violence_detected:
            # SIEMPRE aceptar frames de violencia, sin importar el tiempo transcurrido
            should_accept = True
            if not hasattr(self, 'violence_cooldown_time'):
                self.violence_cooldown_time = current_time
            else:
                self.violence_cooldown_time = current_time
        else:
            # Para frames normales, usar el intervalo regular
            should_accept = time_since_last >= self.capture_interval
        
        if not should_accept:
            return
        
        # Crear copia del frame con información de detección
        frame_copy = frame.copy()
        
        # Dibujar detecciones de personas
        for detection in detections:
            bbox = detection.get('bbox', [0, 0, 0, 0])
            self._draw_detection(frame_copy, detection)
        
        # MEJORADO: Overlay de violencia más intenso y visible
        if violence_info and violence_info.get('detectada'):
            frame_copy = self._draw_violence_overlay_intenso(frame_copy, violence_info)
            probability = violence_info.get('probabilidad', 0.0)
            
            # NUEVO: Log detallado para cada frame de violencia
            print(f"🔥 Frame de VIOLENCIA capturado - Prob: {probability:.3f} - Frame #{self.frame_counter}")
        
        frame_data = {
            'frame': frame_copy,
            'timestamp': datetime.now(),  # CORREGIDO: Usar datetime en lugar de float
            'datetime': datetime.now(),
            'detections': detections,
            'violence_info': violence_info,
            'frame_id': self.frame_counter,
            'time_since_last': time_since_last,
            'is_violence_frame': violence_detected,
            'violence_active': self.violence_active,
            'sequence_id': self.violence_sequence_count,
            'probability': violence_info.get('probabilidad', 0.0) if violence_info else 0.0
        }
        
        # 1) Siempre alimentar el buffer principal
        with self.buffer_lock:
            self.frame_buffer.append(frame_data)
            self.stats['frames_added'] += 1

        # 2) MEJORADO: Capturar TODOS los fotogramas de violencia y duplicarlos para mayor presencia
        if violence_detected:
            with self.violence_buffer_lock:
                # Agregar el frame original
                self.violence_sequence_buffer.append(frame_data)
                
                # NUEVO: Duplicar el frame de violencia para darle más peso (3 copias)
                for _ in range(3):  # Crear 3 copias adicionales
                    duplicate_data = frame_data.copy()
                    duplicate_data['duplicated'] = True
                    duplicate_data['frame_id'] = f"{self.frame_counter}_dup{_}"
                    self.violence_sequence_buffer.append(duplicate_data)
                    
                self.stats['violence_frames_captured'] += 4  # 1 original + 3 duplicados
        
        # 3) Actualizar estadísticas y contadores
        self.frame_counter += 1
        self.last_frame_time = current_time
        
        # Log de estadísticas cada 50 frames
        if self.frame_counter % 50 == 0:
            violence_frames = len([f for f in self.violence_sequence_buffer if f.get('is_violence_frame', False)])
            total_frames = len(self.frame_buffer)
            density = violence_frames / max(1, total_frames)
            
            print(f"📊 Buffer Principal: {len(self.frame_buffer)} frames")
            print(f"📊 Buffer Violencia: {violence_frames} frames")
            print(f"📊 Estado Violencia: {'ACTIVA' if self.violence_active else 'INACTIVA'}")
            print(f"📊 Densidad: {density:.2f} fps")

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
        """MEJORADO: Prioriza frames de violencia con mayor peso"""
        # 1) Tomamos ambos buffers
        with self.buffer_lock:
            main_frames = list(self.frame_buffer)
        
        with self.violence_buffer_lock:
            violence_frames = [f for f in self.violence_sequence_buffer if f.get('is_violence_frame', False)]
        
        # Conteos para logs
        print(f"📹 Frames de VIOLENCIA extraídos: {len(violence_frames)}")
        print(f"📹 Frames de CONTEXTO extraídos: {len(main_frames)}")
        
        # 2) Si hay muy pocos fotogramas de violencia, duplicarlos aún más
        target_vf = int(self.fps * 2)  # Al menos 2 segundos de violencia
        if len(violence_frames) > 0 and len(violence_frames) < target_vf:
            print(f"⚠️ Agregando más frames de violencia para garantizar contenido...")
            
            # Duplicar frames existentes hasta alcanzar el objetivo
            original_vf = len(violence_frames)
            while len(violence_frames) < target_vf and original_vf > 0:
                # Tomar un frame de violencia y duplicarlo
                duplicate_frames = []
                for vf in violence_frames[:original_vf]:  # Solo duplicar los originales
                    dup = vf.copy()
                    dup['frame_id'] = f"{vf['frame_id']}_extra_{len(duplicate_frames)}"
                    dup['duplicated'] = True
                    duplicate_frames.append(dup)
                
                # Añadir duplicados a la lista
                violence_frames.extend(duplicate_frames)
                
                # Imprimir progreso
                print(f"📹 Frames adicionales de violencia: {len(duplicate_frames)}")
                
                # Evitar bucle infinito si no hay frames originales
                if original_vf == 0:
                    break
        
        # 3) MEJORADO: Combinar dando ALTA PRIORIDAD a frames de violencia
        # Primero ordenar por timestamp para garantizar secuencia temporal
        sorted_frames = sorted(main_frames, key=lambda x: x['timestamp'])
        
        # Crear diccionario con todos los frames normales
        combined = {(f['timestamp'], f['frame_id']): f for f in sorted_frames}
        
        # Insertar frames de violencia con mayor prioridad
        for vf in sorted(violence_frames, key=lambda x: x['timestamp']):
            # Asegurar que el frame de violencia se incluya, incluso si ya existe uno en ese timestamp
            key = (vf['timestamp'], vf['frame_id'])
            combined[key] = vf
        
        # Convertir de vuelta a lista y ordenar por timestamp
        frames = sorted(combined.values(), key=lambda x: x['timestamp'])
        
        print(f"🔄 Frames combinados: {len(frames)} (Violencia: {len(violence_frames)}, Contexto: {len(main_frames)})")
        
        # 4) Garantizar mínima duración
        start_time = violence_frames[0]['timestamp'] - timedelta(seconds=self.min_duration_seconds/2) if violence_frames else frames[0]['timestamp']
        end_time = violence_frames[-1]['timestamp'] + timedelta(seconds=self.min_duration_seconds/2) if violence_frames else frames[-1]['timestamp']
        
        # Seleccionar frames dentro del rango de tiempo
        selected = [f for f in frames if start_time <= f['timestamp'] <= end_time]
        
        # 5) NUEVO: Verificar que hay suficientes frames para una buena duración
        min_frames_needed = int(self.fps * 5)  # Al menos 5 segundos de video
        
        print(f"📹 TOTAL frames para evidencia: {len(selected)}")
        print(f"📹 Duración del clip: {len(selected)/self.fps:.2f} segundos")
        
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
        """CORREGIDO: Guarda el video con máximo contenido de violencia"""
        frames = save_data['frames']
        if not frames:
            print("❌ No hay frames para guardar en el video")
            return
        
        # Verificar que hay suficientes frames o expandirlos
        if len(frames) < int(self.fps * 5):  # Mínimo 5 segundos
            frames = self._expandir_frames_para_duracion(frames, int(self.fps * 5))
            print(f"📹 Frames expandidos de {len(save_data['frames'])} a {len(frames)} para 5+ segundos")
        
        # Generar nombre de archivo con información de violencia
        timestamp = save_data['timestamp'].strftime("%Y%m%d_%H%M%S") if isinstance(save_data['timestamp'], datetime) else datetime.now().strftime("%Y%m%d_%H%M%S")
        camera_id = save_data.get('camera_id', 1)
        
        # CORREGIDO: Calcular datos de violencia correctamente
        violence_frames_count = len([f for f in frames if f.get('is_violence_frame', False)])
        
        filename = f"evidencia_camara{camera_id}_{timestamp}.mp4"
        filepath = configuracion.VIDEO_EVIDENCE_PATH / "clips" / filename
        
        # Crear directorio si no existe
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Obtener primer frame para dimensiones
            first_frame = frames[0]['frame']
            height, width = first_frame.shape[:2]
            
            # Configurar escritor de video
            fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
            out = cv2.VideoWriter(
                str(filepath),
                fourcc,
                self.fps,
                (width, height)
            )
            
            # Contador para frames de violencia
            violence_count = 0
            
            # Escribir frames al video con RESALTADO de frames de violencia
            for i, frame_data in enumerate(frames):
                frame = frame_data['frame']
                
                # MEJORADO: Resaltar frames con violencia aún más
                if frame_data.get('is_violence_frame', False):
                    violence_count += 1
                    
                    # Agregar borde rojo para enfatizar frame de violencia
                    cv2.rectangle(frame, (0, 0), (width-1, height-1), (0, 0, 255), 15)
                    
                    # Añadir texto "VIOLENCIA DETECTADA" más grande
                    cv2.putText(
                        frame,
                        "VIOLENCIA DETECTADA",
                        (int(width/2) - 240, height - 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.5,
                        (0, 0, 255),
                        5,
                        cv2.LINE_AA
                    )
                
                # Escribir frame al video
                out.write(frame)
            
            # Liberar recursos
            out.release()
            
            # Calcular tamaño del archivo
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            # Log detallado
            print(f"✅ Video guardado: {filepath}")
            print(f"📹 Tamaño: {file_size_mb:.2f} MB")
            print(f"📹 Frames: {len(frames)}")
            print(f"📹 Duración: {len(frames)/self.fps:.2f} segundos")
            print(f"🔥 Contenido de violencia: {violence_count} frames")
            
            # NUEVO: Agregar datos al incidente a través de una API interna
            self._actualizar_incidente_thread_safe(save_data.get('incidente_id'), str(filepath))
            
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Error al guardar video: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
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