import cv2
import numpy as np
import threading
import queue
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)

class ViolenceEvidenceRecorder:
    """Grabador de evidencia con MÁXIMA captura de frames de violencia - CORREGIDO"""
    
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
        
        # BUFFER DE VIOLENCIA GIGANTE PARA MÁXIMA CAPTURA - AUMENTADO
        self.violence_sequence_buffer = deque(maxlen=5000)  # AUMENTADO: 5000 frames
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
        
        # MULTIPLICADOR DE DUPLICACIÓN MASIVA PARA VIOLENCIA
        self.violence_duplication_multiplier = 12  # AUMENTADO: Cada frame de violencia se duplica 12 veces
        
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
            'last_video_duration': 0.0,
            'violence_duplications': 0  # NUEVO
        }
        
        # Configuración de interpolación
        self.interpolation_enabled = configuracion.EVIDENCE_FRAME_INTERPOLATION
        self.smooth_transitions = configuracion.EVIDENCE_SMOOTH_TRANSITIONS if hasattr(configuracion, 'EVIDENCE_SMOOTH_TRANSITIONS') else True
        self.temporal_smoothing = configuracion.EVIDENCE_TEMPORAL_SMOOTHING if hasattr(configuracion, 'EVIDENCE_TEMPORAL_SMOOTHING') else True
        
        # Crear directorio
        configuracion.VIDEO_EVIDENCE_PATH.mkdir(parents=True, exist_ok=True)
        
        print(f"📹 EvidenceRecorder MÁXIMA CAPTURA DE VIOLENCIA - CORREGIDO:")
        print(f"   - FPS Captura: {self.capture_fps}")
        print(f"   - FPS Video: {self.fps}")
        print(f"   - Buffer Principal: {max_frames} frames ({buffer_seconds}s)")
        print(f"   - Buffer Violencia: 5000 frames (~250s)")
        print(f"   - Multiplicador duplicación: {self.violence_duplication_multiplier}x")
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
        """VERSIÓN CORREGIDA: Captura MASIVA de frames con violencia"""
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
            'timestamp': datetime.now(),
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

        # 2) MÁXIMA DUPLICACIÓN: Capturar TODOS los fotogramas de violencia y multiplicarlos
        if violence_detected:
            with self.violence_buffer_lock:
                # Agregar el frame original
                self.violence_sequence_buffer.append(frame_data)
                
                # DUPLICACIÓN MASIVA: Crear múltiples copias del frame de violencia
                for i in range(self.violence_duplication_multiplier):
                    duplicate_data = frame_data.copy()
                    duplicate_data['frame'] = frame_copy.copy()  # Asegurar copia independiente
                    duplicate_data['timestamp'] = duplicate_data['timestamp'] + timedelta(microseconds=i*100)
                    duplicate_data['duplicated'] = True
                    duplicate_data['duplicate_round'] = i + 1
                    duplicate_data['frame_id'] = f"{self.frame_counter}_dup{i+1}"
                    self.violence_sequence_buffer.append(duplicate_data)
                    
                self.stats['violence_frames_captured'] += 1
                self.stats['violence_duplications'] += self.violence_duplication_multiplier
                
                # Log cada 5 frames de violencia para no saturar
                if self.stats['violence_frames_captured'] % 5 == 0:
                    total_frames_added = 1 + self.violence_duplication_multiplier
                    print(f"🔥 VIOLENCIA MASIVA: {total_frames_added} frames agregados al buffer (1 original + {self.violence_duplication_multiplier} duplicados)")
        
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
        total_recording_time = max(total_recording_time, 25.0)  # AUMENTADO: Mínimo 25 segundos
        
        print(f"📊 Tiempo total de grabación: {total_recording_time}s")
        
        # Programar finalización automática
        finish_timer = threading.Timer(total_recording_time, self._finish_recording)
        finish_timer.start()
    
    def _extract_evidence_frames(self) -> List[Dict]:
        """MÁXIMA EXTRACCIÓN: Prioriza frames de violencia con mayor peso"""
        # 1) Tomamos ambos buffers
        with self.buffer_lock:
            main_frames = list(self.frame_buffer)
        
        with self.violence_buffer_lock:
            violence_frames = [f for f in self.violence_sequence_buffer if f.get('is_violence_frame', False)]
        
        # Conteos para logs
        print(f"📹 Frames de VIOLENCIA extraídos: {len(violence_frames)}")
        print(f"📹 Frames de CONTEXTO extraídos: {len(main_frames)}")
        
        # 2) MULTIPLICACIÓN ADICIONAL si hay muy pocos frames de violencia
        target_violence_frames = int(self.fps * 8)  # AUMENTADO: Al menos 8 segundos de violencia
        if len(violence_frames) > 0 and len(violence_frames) < target_violence_frames:
            print(f"⚠️ Agregando MASIVAMENTE más frames de violencia para garantizar contenido robusto...")
            
            # TRIPLICAR frames existentes hasta alcanzar el objetivo
            original_vf = len(violence_frames)
            rounds = 0
            max_rounds = 5  # AUMENTADO: hasta 5 rondas de duplicación
            
            while len(violence_frames) < target_violence_frames and rounds < max_rounds and original_vf > 0:
                rounds += 1
                duplicate_frames = []
                
                # Duplicar los primeros frames originales
                source_frames = violence_frames[:min(20, original_vf)]  # AUMENTADO: primeros 20 frames
                
                for vf in source_frames:
                    # Crear 3 copias por frame original
                    for copy_num in range(3):
                        dup = vf.copy()
                        dup['frame'] = vf['frame'].copy()  # Copia independiente del frame
                        dup['frame_id'] = f"{vf['frame_id']}_extra_r{rounds}_c{copy_num}"
                        dup['timestamp'] = dup['timestamp'] + timedelta(microseconds=len(duplicate_frames)*25)
                        dup['duplicated'] = True
                        dup['extra_round'] = rounds
                        dup['copy_number'] = copy_num
                        duplicate_frames.append(dup)
                
                # Añadir duplicados a la lista
                violence_frames.extend(duplicate_frames)
                
                # Imprimir progreso
                print(f"📹 Ronda {rounds}: {len(duplicate_frames)} frames adicionales de violencia")
                
                # Verificar si hemos alcanzado el objetivo
                if len(violence_frames) >= target_violence_frames:
                    break
            
            print(f"📹 TOTAL frames de violencia después de duplicación: {len(violence_frames)}")
        
        # 3) MEJORADO: Combinar dando MÁXIMA PRIORIDAD a frames de violencia
        # Crear diccionario con timestamps únicos
        combined_frames = {}
        
        # Primero agregar frames de contexto
        for frame in sorted(main_frames, key=lambda x: x['timestamp']):
            timestamp_key = frame['timestamp'].isoformat()
            combined_frames[timestamp_key] = frame
        
        # SOBREESCRIBIR y AGREGAR frames de violencia con prioridad absoluta
        violence_timestamps = set()
        for vf in sorted(violence_frames, key=lambda x: x['timestamp']):
            timestamp_key = vf['timestamp'].isoformat()
            combined_frames[timestamp_key] = vf  # Sobreescribir cualquier frame de contexto
            violence_timestamps.add(timestamp_key)
        
        # Convertir de vuelta a lista y ordenar por timestamp
        frames = sorted(combined_frames.values(), key=lambda x: x['timestamp'])
        
        violence_effective = len([f for f in frames if f.get('is_violence_frame', False)])
        print(f"🔄 Frames combinados: {len(frames)} (Violencia efectiva: {violence_effective}, Contexto: {len(main_frames)})")
        
        # 4) GARANTIZAR duración mínima ROBUSTA
        if len(frames) > 0:
            start_time = frames[0]['timestamp'] - timedelta(seconds=self.min_duration_seconds/3)
            end_time = frames[-1]['timestamp'] + timedelta(seconds=self.min_duration_seconds/3)
            
            # Seleccionar frames dentro del rango de tiempo
            selected = [f for f in frames if start_time <= f['timestamp'] <= end_time]
        else:
            selected = frames
        
        # 5) EXPANSIÓN FINAL si es necesario
        min_frames_needed = int(self.fps * 8)  # AUMENTADO: Al menos 8 segundos de video
        if len(selected) < min_frames_needed:
            selected = self._expandir_frames_para_duracion_masiva(selected, min_frames_needed)
        
        print(f"📹 TOTAL frames para evidencia: {len(selected)}")
        print(f"📹 Duración estimada del clip: {len(selected)/self.fps:.2f} segundos")
        
        return selected
    
    def _expandir_frames_para_duracion_masiva(self, frames_data: List[Dict], frames_objetivo: int) -> List[Dict]:
        """EXPANSIÓN MASIVA priorizando frames de violencia"""
        if len(frames_data) >= frames_objetivo:
            return frames_data
        
        frames_expandidos = list(frames_data)  # Copiar lista original
        
        # Separar frames por tipo
        frames_violencia = [f for f in frames_data if f.get('is_violence_frame', False)]
        frames_normales = [f for f in frames_data if not f.get('is_violence_frame', False)]
        
        expansion_round = 0
        max_expansion_rounds = 10  # AUMENTADO: hasta 10 rondas de expansión
        
        # Expandir hasta alcanzar el objetivo
        while len(frames_expandidos) < frames_objetivo and expansion_round < max_expansion_rounds:
            expansion_round += 1
            frames_added_this_round = 0
            
            # PRIORIDAD MÁXIMA: Duplicar frames de violencia
            if frames_violencia:
                for frame_v in frames_violencia:
                    if len(frames_expandidos) >= frames_objetivo:
                        break
                    
                    # Crear múltiples copias del frame de violencia
                    copies_to_create = min(3, frames_objetivo - len(frames_expandidos))
                    for i in range(copies_to_create):
                        frame_copia = frame_v.copy()
                        frame_copia['frame'] = frame_v['frame'].copy()
                        frame_copia['timestamp'] = frame_copia['timestamp'] + timedelta(
                            microseconds=(expansion_round * 1000) + (i * 100)
                        )
                        frame_copia['expanded'] = True
                        frame_copia['expansion_round'] = expansion_round
                        frame_copia['expansion_copy'] = i
                        frames_expandidos.append(frame_copia)
                        frames_added_this_round += 1
                        
                        if len(frames_expandidos) >= frames_objetivo:
                            break
            
            # Si aún necesitamos más frames, duplicar frames normales
            if len(frames_expandidos) < frames_objetivo and frames_normales:
                for frame_n in frames_normales:
                    if len(frames_expandidos) >= frames_objetivo:
                        break
                    
                    frame_copia = frame_n.copy()
                    frame_copia['frame'] = frame_n['frame'].copy()
                    frame_copia['timestamp'] = frame_copia['timestamp'] + timedelta(
                        microseconds=(expansion_round * 1000) + frames_added_this_round * 100
                    )
                    frame_copia['expanded'] = True
                    frame_copia['expansion_round'] = expansion_round
                    frames_expandidos.append(frame_copia)
                    frames_added_this_round += 1
            
            # Evitar bucle infinito si no se agregaron frames
            if frames_added_this_round == 0:
                print(f"⚠️ No se pudieron agregar más frames en la ronda {expansion_round}")
                break
            
            print(f"📹 Ronda expansión {expansion_round}: +{frames_added_this_round} frames (total: {len(frames_expandidos)})")
        
        return frames_expandidos[:frames_objetivo]
    
    def _finish_recording(self):
        """Finaliza la grabación con verificación ROBUSTA de contenido de violencia"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # Extraer frames relevantes del buffer MEJORADO
        evidence_frames = self._extract_evidence_frames()
        
        if evidence_frames:
            violence_frames_count = sum(1 for f in evidence_frames if f.get('is_violence_frame'))
            
            # VERIFICACIÓN MEJORADA: que hay suficiente contenido de violencia
            min_frames_required = int(self.min_duration_seconds * 5)  # RELAJADO: 5fps mínimo
            min_violence_frames = 5  # RELAJADO: al menos 5 frames de violencia
            
            if len(evidence_frames) >= min_frames_required and violence_frames_count >= min_violence_frames:
                save_data = {
                    'frames': evidence_frames,
                    'violence_time': self.violence_start_time,
                    'timestamp': datetime.now(),
                    'buffer_density': self.stats['buffer_density'],
                    'violence_frames_count': violence_frames_count,
                    'violence_sequences': self.stats['violence_sequences'],
                    'min_duration_guarantee': self.min_duration_seconds,
                    'camera_id': 1,  # Default camera ID
                    'incidente_id': None  # Will be set by pipeline if available
                }
                
                try:
                    self.save_queue.put_nowait(save_data)
                    duration_estimate = len(evidence_frames) / self.fps
                    print(f"📝 Evidencia ROBUSTA enviada a cola:")
                    print(f"   - {len(evidence_frames)} frames")
                    print(f"   - {violence_frames_count} con violencia")
                    print(f"   - Duración estimada: {duration_estimate:.2f}s")
                    print(f"   - Duplicaciones totales: {self.stats['violence_duplications']}")
                except queue.Full:
                    print("⚠️ Cola de guardado llena - evidencia perdida")
            else:
                print(f"⚠️ Evidencia rechazada: frames insuficientes ({len(evidence_frames)}<{min_frames_required}) o poca violencia ({violence_frames_count}<{min_violence_frames})")
        
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
        self.stats['violence_duplications'] = 0
    
    def _save_evidence_video(self, save_data: Dict):
        """CORREGIDO: Guarda el video con máximo contenido de violencia"""
        frames = save_data['frames']
        if not frames:
            print("❌ No hay frames para guardar en el video")
            return
        
        # Verificar que hay suficientes frames o expandirlos
        min_frames_for_video = int(self.fps * 5)  # 5 segundos mínimo
        if len(frames) < min_frames_for_video:
            frames = self._expandir_frames_para_duracion_masiva(frames, min_frames_for_video)
            print(f"📹 Frames expandidos de {len(save_data['frames'])} a {len(frames)} para 5+ segundos")
        
        # Generar nombre de archivo con información de violencia
        timestamp = save_data['timestamp'].strftime("%Y%m%d_%H%M%S") if isinstance(save_data['timestamp'], datetime) else datetime.now().strftime("%Y%m%d_%H%M%S")
        camera_id = save_data.get('camera_id', 1)
        
        # CONTAR datos de violencia correctamente
        violence_frames_count = len([f for f in frames if f.get('is_violence_frame', False)])
        
        filename = f"evidencia_camara{camera_id}_{timestamp}.mp4"
        filepath = configuracion.VIDEO_EVIDENCE_PATH / "clips" / filename
        
        # Crear directorio si no existe
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Obtener primer frame para dimensiones
            first_frame = frames[0]['frame']
            height, width = first_frame.shape[:2]
            
            # Configurar escritor de video con codec más compatible
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Usar mp4v como principal
            out = cv2.VideoWriter(
                str(filepath),
                fourcc,
                self.fps,
                (width, height)
            )
            
            if not out.isOpened():
                print(f"⚠️ Reintentando con codec fallback...")
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter(
                    str(filepath.with_suffix('.avi')),  # Cambiar a AVI si MP4 falla
                    fourcc,
                    self.fps,
                    (width, height)
                )
                filepath = filepath.with_suffix('.avi')
            
            if not out.isOpened():
                print(f"❌ Error: No se pudo crear VideoWriter")
                return
            
            # Contador para frames de violencia
            violence_count = 0
            
            # Escribir frames al video con MÁXIMO RESALTADO de frames de violencia
            for i, frame_data in enumerate(frames):
                frame = frame_data['frame'].copy()
                
                # RESALTAR frames con violencia INTENSAMENTE
                if frame_data.get('is_violence_frame', False):
                    violence_count += 1
                    
                    # Agregar borde rojo GRUESO para enfatizar frame de violencia
                    border_thickness = 20
                    cv2.rectangle(frame, (0, 0), (width-1, height-1), (0, 0, 255), border_thickness)
                    
                    # Añadir texto "VIOLENCIA DETECTADA" MÁS GRANDE Y PROMINENTE
                    text_scale = min(width, height) / 400.0  # Escalar según resolución
                    text_thickness = max(3, int(text_scale * 3))
                    
                    cv2.putText(
                        frame,
                        "*** VIOLENCIA DETECTADA ***",
                        (border_thickness + 10, height - border_thickness - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        text_scale * 1.5,
                        (255, 255, 255),
                        text_thickness,
                        cv2.LINE_AA
                    )
                    
                    # Agregar probabilidad si está disponible
                    if 'probability' in frame_data:
                        prob_text = f"PROB: {frame_data['probability']:.1%}"
                        cv2.putText(
                            frame,
                            prob_text,
                            (border_thickness + 10, border_thickness + 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            text_scale,
                            (0, 255, 255),
                            text_thickness,
                            cv2.LINE_AA
                        )
                
                # Escribir frame al video
                out.write(frame)
            
            # Liberar recursos
            out.release()
            
            # Verificar archivo creado y calcular tamaño
            if filepath.exists():
                file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                # Log detallado
                print(f"✅ Video guardado: {filepath}")
                print(f"📹 Tamaño: {file_size_mb:.2f} MB")
                print(f"📹 Frames: {len(frames)}")
                print(f"📹 Duración: {len(frames)/self.fps:.2f} segundos")
                print(f"🔥 Contenido de violencia: {violence_count} frames ({violence_count/len(frames)*100:.1f}%)")
                
                # Actualizar estadísticas
                self.stats['videos_saved'] += 1
                self.stats['last_video_duration'] = len(frames) / self.fps
                
                return str(filepath)
            else:
                print(f"❌ Error: El archivo de video no se creó correctamente")
                return None
            
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
                print(f"Error procesando cola de guardado: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del recorder MEJORADAS"""
        return {
            'frames_added': self.stats['frames_added'],
            'violence_frames_captured': self.stats['violence_frames_captured'],
            'violence_duplications': self.stats['violence_duplications'],
            'violence_sequences': self.stats['violence_sequences'],
            'frames_interpolated': self.stats['frames_interpolated'],
            'videos_saved': self.stats['videos_saved'],
            'last_video_duration': self.stats['last_video_duration'],
            'buffer_size': len(self.frame_buffer),
            'violence_buffer_size': len(self.violence_sequence_buffer),
            'buffer_max_size': self.frame_buffer.maxlen,
            'violence_buffer_max_size': self.violence_sequence_buffer.maxlen,
            'buffer_density': self.stats['buffer_density'],
            'min_duration_guarantee': self.min_duration_seconds,
            'duplication_multiplier': self.violence_duplication_multiplier,
            'is_recording': self.is_recording,
            'violence_active': self.violence_active,
            'running': self.running,
            'config_fps': self.fps,
            'config_capture_fps': self.capture_fps,
            'interpolation_enabled': self.interpolation_enabled
        }

# Instancia global
evidence_recorder = ViolenceEvidenceRecorder()