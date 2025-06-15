# app/tasks/video_recorder.py - ACTUALIZADO PARA BASE64
import cv2
import numpy as np
import threading
import queue
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque
from app.config import configuracion
from app.models.incident import Incidente, EstadoIncidente
from app.utils.logger import obtener_logger
from app.utils.video_base64_utils import video_to_base64, get_video_info_detailed  # NUEVO IMPORT

logger = obtener_logger(__name__)

class ViolenceEvidenceRecorder:
    """Grabador de evidencia con conversión a Base64 - ACTUALIZADO"""
    
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
            'violence_duplications': 0,
            'base64_conversions': 0,  # NUEVO
            'base64_size_mb': 0.0     # NUEVO
        }
        
        # Crear directorios
        configuracion.VIDEO_EVIDENCE_PATH.mkdir(parents=True, exist_ok=True)
        (configuracion.VIDEO_EVIDENCE_PATH / "temp").mkdir(parents=True, exist_ok=True)
        
        print(f"📹 EvidenceRecorder CON BASE64 - ACTUALIZADO:")
        print(f"   - FPS Captura: {self.capture_fps}")
        print(f"   - FPS Video: {self.fps}")
        print(f"   - Buffer Principal: {max_frames} frames ({buffer_seconds}s)")
        print(f"   - Buffer Violencia: 5000 frames (~250s)")
        print(f"   - Multiplicador duplicación: {self.violence_duplication_multiplier}x")
        print(f"   - Duración mínima garantizada: {self.min_duration_seconds}s")
        print(f"   - 🆕 CONVERSIÓN A BASE64 HABILITADA")
    
    def start_processing(self):
        """Inicia el hilo de procesamiento"""
        if not self.running:
            self.running = True
            self.save_thread = threading.Thread(target=self._process_save_queue, daemon=True)
            self.save_thread.start()
            print("🚀 Procesamiento de evidencias con Base64 iniciado")
    
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
                self._start_recording(self.violence_start_time)
                
        elif not violence_detected and self.last_violence_state:
            # Solo finalizar estado de violencia después de un periodo de enfriamiento
            if not hasattr(self, 'violence_cooldown_time') or current_time - getattr(self, 'violence_cooldown_time', 0) > 2.0:
                self.violence_active = False
                self.violence_end_time = datetime.now()
                self.last_violence_state = False
                self.violence_cooldown_time = current_time
                print(f"🔄 VIOLENCIA FINALIZADA en Evidence Recorder")
        
        # Control de frecuencia de captura
        should_accept = True
        if violence_detected:
            should_accept = True
            if not hasattr(self, 'violence_cooldown_time'):
                self.violence_cooldown_time = current_time
            else:
                self.violence_cooldown_time = current_time
        else:
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
                # Agregar frame original
                self.violence_sequence_buffer.append(frame_data)
                
                # DUPLICACIÓN MASIVA para garantizar presencia en video
                for i in range(self.violence_duplication_multiplier):
                    duplicate_frame = frame_data.copy()
                    duplicate_frame['duplicate_id'] = i + 1
                    duplicate_frame['frame_type'] = 'duplicated'
                    self.violence_sequence_buffer.append(duplicate_frame)
                
                self.stats['violence_frames_captured'] += 1
                self.stats['violence_duplications'] += self.violence_duplication_multiplier
        
        # 3) Actualizar estadísticas y contadores
        self.frame_counter += 1
        self.last_frame_time = current_time
        
        # Log de estadísticas cada 50 frames
        if self.frame_counter % 50 == 0:
            self._log_buffer_stats()
    
    def _save_evidence_video(self, save_data: Dict):
        """*** MÉTODO PRINCIPAL ACTUALIZADO PARA BASE64 ***"""
        try:
            frames_data = save_data['frames']
            camara_id = save_data['camara_id']
            violence_start_time = save_data['violence_start_time']
            incidente_id = save_data.get('incidente_id')
            
            # **CORREGIR: Asegurar que violence_start_time sea datetime**
            if isinstance(violence_start_time, (int, float)):
                violence_start_time = datetime.fromtimestamp(violence_start_time)
            elif isinstance(violence_start_time, str):
                violence_start_time = datetime.fromisoformat(violence_start_time)
            elif not isinstance(violence_start_time, datetime):
                violence_start_time = datetime.now()
                print(f"⚠️ violence_start_time tenía tipo inesperado: {type(violence_start_time)}")
            
            if not frames_data:
                print("❌ No hay frames para guardar")
                return
            
            # *** PASO 1: GUARDAR VIDEO TEMPORAL ***
            timestamp_str = violence_start_time.strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"evidencia_camara{camara_id}_{timestamp_str}.mp4"
            
            # Crear archivo temporal para conversión
            temp_dir = configuracion.VIDEO_EVIDENCE_PATH / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_video_path = temp_dir / nombre_archivo
            
            print(f"📹 Guardando video temporal: {nombre_archivo}")
            print(f"📹 Dimensiones: {self.frame_width}x{self.frame_height}")
            print(f"📹 FPS objetivo: {self.fps}")
            print(f"📹 Frames disponibles: {len(frames_data)}")
            
            # Configurar el escritor de video
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Usar mp4v como en el ejemplo
            
            out = cv2.VideoWriter(
                str(temp_video_path),
                fourcc,
                self.fps,
                (self.frame_width, self.frame_height)
            )
            
            if not out.isOpened():
                print(f"❌ Error: No se pudo abrir el escritor de video para {temp_video_path}")
                return
            
            frames_escritos = 0
            frames_con_violencia = 0
            
            # Escribir frames al video temporal
            for frame_data in frames_data:
                if frame_data and 'frame' in frame_data:
                    frame = frame_data['frame']
                    if frame is not None and frame.size > 0:
                        # Redimensionar si es necesario
                        if frame.shape[:2] != (self.frame_height, self.frame_width):
                            frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                        
                        out.write(frame)
                        frames_escritos += 1
                        
                        # Contar frames con violencia
                        if frame_data.get('is_violence_frame', False):
                            frames_con_violencia += 1
            
            out.release()
            
            # *** PASO 2: CONVERTIR A BASE64 ***
            print(f"🔄 Convirtiendo video a Base64...")
            
            if not temp_video_path.exists():
                print(f"❌ Error: El archivo temporal no se creó: {temp_video_path}")
                return
            
            # Obtener información del video antes de conversión
            video_info = get_video_info_detailed(str(temp_video_path))
            
            # Convertir a Base64 usando las utilidades (como en tu ejemplo)
            base64_data = video_to_base64(str(temp_video_path))
            
            if not base64_data:
                print("❌ Error: No se pudo convertir el video a Base64")
                # Limpiar archivo temporal
                try:
                    temp_video_path.unlink()
                except:
                    pass
                return
            
            # *** PASO 3: CALCULAR ESTADÍSTICAS ***
            file_size = temp_video_path.stat().st_size
            duracion_segundos = frames_escritos / self.fps
            base64_size_mb = len(base64_data) / (1024 * 1024)
            
            print(f"✅ Video convertido a Base64 exitosamente:")
            print(f"📹 Tamaño original: {file_size / (1024*1024):.2f} MB")
            print(f"📹 Tamaño Base64: {base64_size_mb:.2f} MB")
            print(f"📹 Caracteres Base64: {len(base64_data)}")
            print(f"📹 Frames: {frames_escritos}")
            print(f"📹 Duración: {duracion_segundos:.2f} segundos")
            print(f"🔥 Contenido de violencia: {frames_con_violencia} frames ({frames_con_violencia/frames_escritos*100:.1f}%)")
            
            # *** PASO 4: ACTUALIZAR INCIDENTE CON BASE64 ***
            if incidente_id:
                self._actualizar_incidente_con_base64(incidente_id, base64_data, {
                    'frames_total': frames_escritos,
                    'frames_violencia': frames_con_violencia,
                    'duracion_segundos': duracion_segundos,
                    'tamaño_mb': base64_size_mb,
                    'file_size': file_size,
                    'fps': self.fps,
                    'resolution': f"{self.frame_width}x{self.frame_height}",
                    'codec': 'mp4v',
                    'video_info': video_info
                })
            
            # *** PASO 5: LIMPIAR ARCHIVO TEMPORAL ***
            try:
                temp_video_path.unlink()
                print(f"🗑️ Archivo temporal eliminado: {temp_video_path}")
            except Exception as e:
                print(f"⚠️ No se pudo eliminar archivo temporal: {e}")
            
            # Actualizar estadísticas
            self.stats['videos_saved'] += 1
            self.stats['last_video_duration'] = duracion_segundos
            self.stats['base64_conversions'] += 1
            self.stats['base64_size_mb'] = base64_size_mb
            
        except Exception as e:
            print(f"❌ Error guardando video con Base64: {e}")
            import traceback
            print(traceback.format_exc())

    def _actualizar_incidente_con_base64(self, incidente_id: int, base64_data: str, stats: Dict):
        """*** NUEVO: Actualiza el incidente con Base64 en lugar de archivo ***"""
        try:
            import requests
            
            print(f"📝 Actualizando incidente {incidente_id} con Base64")
            print(f"📊 Tamaño Base64: {len(base64_data)} caracteres")
            print(f"📊 Duración: {stats['duracion_segundos']:.2f}s")
            
            # Preparar datos de actualización con Base64
            datos_actualizacion = {
                # *** NUEVOS CAMPOS BASE64 ***
                'video_base64': base64_data,
                'video_file_size': stats['file_size'],
                'video_duration': stats['duracion_segundos'],
                'video_codec': stats['codec'],
                'video_fps': stats['fps'],
                'video_resolution': stats['resolution'],
                
                # *** CAMPOS ESTÁNDAR ***
                'fecha_hora_fin': datetime.now().isoformat(),
                'duracion_segundos': int(stats['duracion_segundos']),
                'estado': EstadoIncidente.CONFIRMADO.value,
                
                # *** METADATA EXTENDIDA ***
                'metadata_json': {
                    'video_stats': {
                        'frames_total': stats['frames_total'],
                        'frames_violencia': stats['frames_violencia'],
                        'duracion_segundos': stats['duracion_segundos'],
                        'tamaño_archivo_mb': stats['tamaño_mb'],
                        'tamaño_base64_mb': len(base64_data) / (1024 * 1024),
                        'base64_length': len(base64_data),
                        'generado_por': 'evidence_recorder_base64',
                        'codec': stats['codec'],
                        'fps': stats['fps'],
                        'resolution': stats['resolution'],
                        'conversion_info': stats.get('video_info', {})
                    }
                }
            }
            
            print(f"🔗 Datos a enviar: Base64={len(base64_data)} chars, Codec={stats['codec']}")
            
            # Realizar petición HTTP al endpoint interno
            response = requests.patch(
                f"http://localhost:8000/api/v1/incidents/{incidente_id}/internal",
                json=datos_actualizacion,
                timeout=30  # Aumentar timeout para Base64 grandes
            )
            
            if response.status_code == 200:
                print(f"✅ Incidente {incidente_id} actualizado con Base64 exitosamente")
                print(f"💾 Base64 guardado en DB: {len(base64_data)} caracteres")
            else:
                print(f"❌ Error actualizando incidente: {response.status_code}")
                print(f"❌ Respuesta: {response.text}")
                
        except Exception as e:
            print(f"❌ Error actualizando incidente {incidente_id} con Base64: {e}")
            import traceback
            print(traceback.format_exc())
    
    def _start_recording(self, violence_datetime):
        """Inicia la grabación de evidencia - Acepta datetime"""
        if self.is_recording:
            return
        
        print(f"🚨 Iniciando grabación de evidencia CON BASE64")
        
        # **CORREGIR: Manejar tanto datetime como float**
        if isinstance(violence_datetime, datetime):
            self.violence_start_time = violence_datetime
        elif isinstance(violence_datetime, (int, float)):
            self.violence_start_time = datetime.fromtimestamp(violence_datetime)
        else:
            self.violence_start_time = datetime.now()
            print(f"⚠️ Tipo inesperado para violence_datetime: {type(violence_datetime)}")
        
        self.is_recording = True
        
        # Estadísticas del buffer actual
        with self.buffer_lock:
            buffer_size = len(self.frame_buffer)
        
        with self.violence_buffer_lock:
            violence_buffer_size = len(self.violence_sequence_buffer)
        
        print(f"📊 Buffer principal: {buffer_size} frames")
        print(f"📊 Buffer violencia: {violence_buffer_size} frames")
        print(f"📊 Conversión a Base64: HABILITADA")
    
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
    
    def _finish_recording(self):
        """CORREGIDO: Finaliza la grabación y envía datos para guardar"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # **IMPORTANTE: Extraer frames antes de que se pierdan**
        frames_data = self._extract_evidence_frames()
        
        if not frames_data:
            print("⚠️ No hay frames de evidencia para guardar")
            return
        
        # **CORREGIR: Asegurar que violence_start_time sea datetime**
        if not isinstance(self.violence_start_time, datetime):
            if isinstance(self.violence_start_time, (int, float)):
                violence_start_time = datetime.fromtimestamp(self.violence_start_time)
            else:
                violence_start_time = datetime.now()
        else:
            violence_start_time = self.violence_start_time
        
        # Preparar datos para guardado
        save_data = {
            'frames': frames_data,
            'camara_id': 1,  # Hardcoded por ahora
            'violence_start_time': violence_start_time,  # Ahora es datetime garantizado
            'incidente_id': getattr(self, 'current_incident_id', None)
        }
        
        print(f"📹 Frames de VIOLENCIA extraídos: {len([f for f in frames_data if f.get('is_violence_frame', False)])}")
        print(f"📹 Frames de CONTEXTO extraídos: {len([f for f in frames_data if not f.get('is_violence_frame', False)])}")
        print(f"🔄 CONVERSIÓN A BASE64: PROGRAMADA")
        
        # **DEBUG: Verificar tipo de violence_start_time**
        print(f"🕒 Tipo de violence_start_time: {type(violence_start_time)} - Valor: {violence_start_time}")
        
        # Enviar a cola de guardado
        try:
            self.save_queue.put(save_data, timeout=5)
            print(f"📹 Video de evidencia enviado a cola de guardado CON BASE64")
        except queue.Full:
            print("❌ Error: Cola de guardado llena, descartando video")
        
        # Limpiar estado
        self.violence_start_time = None
        with self.violence_buffer_lock:
            self.violence_sequence_buffer.clear()
    
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
    
    def _log_buffer_stats(self):
        """Log de estadísticas del buffer cada cierto tiempo"""
        with self.buffer_lock:
            buffer_size = len(self.frame_buffer)
        
        with self.violence_buffer_lock:
            violence_size = len(self.violence_sequence_buffer)
        
        # Calcular densidad del buffer
        if self.frame_buffer.maxlen > 0:
            buffer_density = (buffer_size / self.frame_buffer.maxlen) * 100
        else:
            buffer_density = 0
        
        self.stats['buffer_density'] = buffer_density
        
        # Log cada 100 frames para no saturar
        if self.frame_counter % 100 == 0:
            print(f"📊 Buffer Stats - Principal: {buffer_size}, Violencia: {violence_size}, Densidad: {buffer_density:.1f}%")

    def _draw_violence_overlay_intenso(self, frame: np.ndarray, violence_info: Dict) -> np.ndarray:
        """Overlay de violencia con tamaño más moderado y mejor legibilidad"""
        height, width = frame.shape[:2]
        probability = violence_info.get('probabilidad', 0.0)
        
        # *** REDUCIR ALTURA DEL OVERLAY ***
        overlay_height = 80  # Reducido de 150 a 80
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, overlay_height), (0, 0, 255), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)  # Menos intensidad
        
        # *** TEXTO PRINCIPAL MÁS PEQUEÑO ***
        cv2.putText(
            frame, 
            "VIOLENCIA DETECTADA", 
            (15, 25), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8,  # Reducido de 1.8 a 0.8
            (255, 255, 255), 
            2,    # Reducido de 6 a 2
            cv2.LINE_AA
        )
        
        # *** PROBABILIDAD MÁS PEQUEÑA ***
        cv2.putText(
            frame, 
            f"Probabilidad: {probability:.1%}", 
            (15, 50), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6,  # Reducido de 1.4 a 0.6
            (0, 255, 255), 
            2,    # Reducido de 5 a 2
            cv2.LINE_AA
        )
        
        # *** TIMESTAMP MÁS PEQUEÑO ***
        timestamp_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        cv2.putText(
            frame, 
            f"{timestamp_str}", 
            (15, 70), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5,  # Reducido de 0.9 a 0.5
            (255, 255, 255), 
            1,    # Reducido de 3 a 1
            cv2.LINE_AA
        )
        
        return frame
    
    def set_current_incident_id(self, incidente_id: int):
        """Establece el ID del incidente actual para el video"""
        self.current_incident_id = incidente_id
        print(f"📋 Incident ID {incidente_id} asignado al evidence_recorder CON BASE64")

    def _draw_detection(self, frame: np.ndarray, detection: Dict):
        """Dibuja bounding box de persona detectada con tamaño moderado"""
        bbox = detection['bbox']
        confidence = detection['confianza']
        
        x, y, w, h = map(int, bbox)
        
        # *** BOUNDING BOX VERDE MÁS DISCRETO ***
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Reducido de 3 a 2
        
        # *** ETIQUETA MÁS PEQUEÑA ***
        label = f"Persona: {confidence:.2f}"
        (text_width, text_height), _ = cv2.getTextSize(
            label, 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5,  # Reducido de 0.7 a 0.5
            1     # Reducido de 2 a 1
        )
        
        # Fondo más pequeño
        cv2.rectangle(
            frame, 
            (x, y - text_height - 8), 
            (x + text_width, y), 
            (0, 255, 0), 
            -1
        )
        
        cv2.putText(
            frame, 
            label, 
            (x, y - 4), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5,  # Reducido de 0.7 a 0.5
            (0, 0, 0), 
            1     # Reducido de 2 a 1
        )
    
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
            'base64_conversions': self.stats['base64_conversions'],  # NUEVO
            'base64_size_mb': self.stats['base64_size_mb'],         # NUEVO
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
            'interpolation_enabled': self.interpolation_enabled if hasattr(self, 'interpolation_enabled') else False,
            'base64_enabled': True  # NUEVO INDICADOR
        }

# Instancia global
evidence_recorder = ViolenceEvidenceRecorder()