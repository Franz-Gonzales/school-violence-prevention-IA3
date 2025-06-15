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
        """CORREGIDO: Verificación robusta de parámetros de entrada"""
        
        # *** VERIFICACIÓN CRÍTICA DE ENTRADA ***
        if frame is None:
            print("⚠️ Frame None recibido, saltando")
            return
        
        if not isinstance(detections, list):
            detections = []
        
        current_time = time.time()
        time_since_last = current_time - self.last_frame_time
        
        # DETECTAR ESTADO DE VIOLENCIA CON VERIFICACIÓN
        violence_detected = False
        violence_probability = 0.0
        
        if violence_info is not None and isinstance(violence_info, dict):
            violence_detected = violence_info.get('detectada', False)
            violence_probability = violence_info.get('probabilidad', 0.0)
        
        # *** CORRECCIÓN: Detectar secuencias COMPLETAS con verificación ***
        is_violence_sequence = (
            violence_detected or  # Frame con violencia confirmada
            (violence_info is not None and violence_info.get('es_secuencia_violencia', False)) or
            (violence_info is not None and violence_info.get('es_contexto_secuencia', False)) or
            (violence_info is not None and violence_info.get('frames_analizados', 0) >= 6)
        )
        
        # CONTROL MEJORADO DE TRANSICIONES DE ESTADO
        if violence_detected and not self.last_violence_state:
            self._start_recording(datetime.now())
            self.violence_sequence_count += 1
            print(f"🚨 VIOLENCIA DETECTADA - Iniciando captura MASIVA de secuencia")
            
        elif not violence_detected and self.last_violence_state:
            # Continuar grabando por más tiempo después de que termine la violencia
            if not hasattr(self, 'violence_end_grace_period'):
                self.violence_end_grace_period = current_time + 3.0  # *** 3 segundos de gracia ***
                print(f"⏰ Violencia terminó - Continuando captura por 3s más")
            
            if hasattr(self, 'violence_end_grace_period') and current_time > self.violence_end_grace_period:
                self._finish_recording()
                if hasattr(self, 'violence_end_grace_period'):
                    delattr(self, 'violence_end_grace_period')
        
        # *** CORRECCIÓN: Control de frecuencia MEJORADO ***
        if is_violence_sequence or violence_detected:
            # Durante violencia/análisis: capturar MÁS frames para preservar secuencia
            capture_interval = 1.0 / 60  # 60 FPS durante violencia *** AUMENTADO ***
            should_accept = True  # SIEMPRE aceptar durante secuencias de violencia
        else:
            # Normal: mantener frecuencia estándar
            capture_interval = 1.0 / self.capture_fps
            should_accept = time_since_last >= capture_interval
        
        if not should_accept:
            return
        
        # *** VERIFICACIÓN ANTES DE CREAR frame_data ***
        try:
            frame_copy = frame.copy()
        except Exception as e:
            print(f"❌ Error copiando frame: {e}")
            return
        
        # Dibujar detecciones de personas
        for detection in detections:
            bbox = detection.get('bbox', [])
            if len(bbox) == 4:
                x, y, w, h = map(int, bbox)
                cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
                conf = detection.get('confianza', 0)
                cv2.putText(frame_copy, f'Persona {conf:.2f}', (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # *** CORRECCIÓN: Overlay mejorado para TODA la secuencia ***
        if violence_info and (violence_detected or is_violence_sequence):
            frame_copy = self._draw_violence_overlay_mejorado(frame_copy, violence_info)
        
        # *** VERIFICACIÓN AL CREAR frame_data ***
        frame_data = {
            'frame': frame_copy,
            'timestamp': datetime.now(),
            'datetime': datetime.now(),
            'detections': detections if detections is not None else [],
            'violence_info': violence_info if violence_info is not None else {},
            'frame_id': self.frame_counter,
            'time_since_last': time_since_last,
            'is_violence_frame': violence_detected,
            'is_violence_sequence': is_violence_sequence,
            'violence_active': self.violence_active,
            'sequence_id': self.violence_sequence_count,
            'probability': violence_probability,
            'frames_analizados': violence_info.get('frames_analizados', 0) if violence_info else 0,
            'es_contexto_secuencia': violence_info.get('es_contexto_secuencia', False) if violence_info else False
        }
        
        # *** VERIFICACIÓN ANTES DE AGREGAR AL BUFFER ***
        if frame_data is not None and isinstance(frame_data, dict):
            # 1) Siempre alimentar el buffer principal
            with self.buffer_lock:
                self.frame_buffer.append(frame_data)
            
            # 2) *** CORRECCIÓN: Captura MÁS INTELIGENTE para secuencias completas ***
            if is_violence_sequence or violence_detected:
                with self.violence_buffer_lock:
                    # Frame original SIEMPRE
                    self.violence_sequence_buffer.append(frame_data)
                    
                    # *** CORRECCIÓN: Duplicación inteligente basada en importancia ***
                    if violence_detected and violence_probability > 0.7:
                        # VIOLENCIA CONFIRMADA: Duplicación masiva
                        duplications = self.violence_duplication_multiplier
                        duplication_type = 'confirmed_violence'
                    elif is_violence_sequence and violence_info.get('es_secuencia_violencia', False):
                        # SECUENCIA DE ANÁLISIS: Duplicación moderada
                        duplications = self.violence_duplication_multiplier // 2  # *** 6 duplicaciones ***
                        duplication_type = 'analysis_sequence'
                    elif violence_info.get('es_contexto_secuencia', False):
                        # CONTEXTO DURANTE VIOLENCIA: Duplicación mínima
                        duplications = 3
                        duplication_type = 'context_sequence'
                    else:
                        duplications = 0
                        duplication_type = 'none'
                    
                    # Realizar duplicaciones
                    for i in range(duplications):
                        duplicate = frame_data.copy()
                        duplicate['frame'] = frame_copy.copy()
                        duplicate['frame_type'] = duplication_type
                        duplicate['duplicate_id'] = i + 1
                        self.violence_sequence_buffer.append(duplicate)
                    
                    if duplications > 0:
                        self.stats['violence_duplications'] += duplications
                        print(f"🔥 Frame {duplication_type} P={violence_probability:.3f} - {duplications+1} copias guardadas")
                    
                    self.stats['violence_frames_captured'] += 1
        
        # 3) Actualizar estadísticas y contadores
        self.frame_counter += 1
        self.last_frame_time = current_time
        self.last_violence_state = violence_detected
        self.stats['frames_added'] += 1

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
        """CORREGIDO: Extracción con verificación robusta de frames None"""
        # 1) Obtener frames de ambos buffers
        with self.buffer_lock:
            main_frames = list(self.frame_buffer)
        
        with self.violence_buffer_lock:
            violence_frames = list(self.violence_sequence_buffer)
        
        # *** CORRECCIÓN CRÍTICA: Filtrar frames None INMEDIATAMENTE ***
        main_frames = [f for f in main_frames if f is not None]
        violence_frames = [f for f in violence_frames if f is not None]
        
        print(f"📹 Frames filtrados: {len(main_frames)} principales, {len(violence_frames)} violencia")
        
        # *** CORRECCIÓN: Análisis seguro por TIPO de frame ***
        violence_confirmed = []
        violence_sequence = []
        violence_context = []
        
        for f in violence_frames:
            if f is not None and isinstance(f, dict):
                if f.get('is_violence_frame', False):
                    violence_confirmed.append(f)
                elif f.get('is_violence_sequence', False):
                    violence_sequence.append(f)
        
        for f in main_frames:
            if f is not None and isinstance(f, dict):
                violence_info = f.get('violence_info')
                if violence_info is not None and isinstance(violence_info, dict):
                    if violence_info.get('es_contexto_secuencia', False):
                        violence_context.append(f)
        
        print(f"📹 Análisis de frames por tipo:")
        print(f"   - Violencia confirmada: {len(violence_confirmed)} frames")
        print(f"   - Secuencia de análisis: {len(violence_sequence)} frames")  
        print(f"   - Contexto de violencia: {len(violence_context)} frames")
        
        # *** CORRECCIÓN: Construcción segura de video ***
        combined_frames = {}
        
        # PASO 1: Agregar frames de contexto como base
        for frame in main_frames:
            if frame is not None and isinstance(frame, dict):
                if not frame.get('is_violence_frame', False):  # Solo contexto
                    timestamp_key = frame['timestamp'].isoformat()
                    combined_frames[timestamp_key] = frame
        
        # PASO 2: SOBRESCRIBIR con frames de secuencia de análisis
        for frame in violence_sequence:
            if frame is not None and isinstance(frame, dict):
                timestamp_key = frame['timestamp'].isoformat()
                combined_frames[timestamp_key] = frame
        
        # PASO 3: SOBRESCRIBIR con frames de violencia confirmada (máxima prioridad)
        for frame in violence_confirmed:
            if frame is not None and isinstance(frame, dict):
                timestamp_key = frame['timestamp'].isoformat()
                combined_frames[timestamp_key] = frame
        
        # PASO 4: Agregar contexto específico de violencia
        for frame in violence_context:
            if frame is not None and isinstance(frame, dict):
                timestamp_key = frame['timestamp'].isoformat()
                if timestamp_key not in combined_frames:  # Solo si no hay algo mejor
                    combined_frames[timestamp_key] = frame
        
        # 3) Convertir a lista ordenada y filtrar None final
        frames = [f for f in sorted(combined_frames.values(), key=lambda x: x['timestamp']) if f is not None]
        
        # *** ESTADÍSTICAS CORREGIDAS Y SEGURAS ***
        final_violence_confirmed = 0
        final_violence_sequence = 0
        final_context = 0
        
        for f in frames:
            if f is not None and isinstance(f, dict):
                if f.get('is_violence_frame', False):
                    final_violence_confirmed += 1
                elif f.get('is_violence_sequence', False):
                    final_violence_sequence += 1
                else:
                    final_context += 1
        
        print(f"📹 Frames combinados: {len(frames)} total")
        print(f"📹 Frames de violencia confirmada: {final_violence_confirmed}")
        print(f"📹 Frames de secuencia de análisis: {final_violence_sequence}")
        print(f"📹 Frames de contexto: {final_context}")
        
        if len(frames) > 0:
            relevance_percentage = ((final_violence_confirmed + final_violence_sequence) / len(frames) * 100)
            print(f"📹 Porcentaje de contenido relevante: {relevance_percentage:.1f}%")
        
        # 4) *** CORRECCIÓN: Verificar contenido MÍNIMO con validación ***
        min_relevant_frames = 45  # 3 segundos de contenido relevante a 15 FPS
        current_relevant = final_violence_confirmed + final_violence_sequence
        
        if current_relevant < min_relevant_frames:
            print(f"⚠️ Insuficiente contenido relevante ({current_relevant}/{min_relevant_frames})")
            print(f"🔄 Expandiendo contenido de violencia...")
            
            # Expandir específicamente contenido relevante
            frames = self._expand_relevant_content(frames, min_relevant_frames)
        
        # 5) *** CORRECCIÓN: Garantizar duración MÍNIMA pero ÓPTIMA ***
        min_frames_needed = int(self.fps * 8)  # 8 segundos para análisis completo
        max_frames_allowed = int(self.fps * 15) # 15 segundos máximo
        
        if len(frames) < min_frames_needed:
            print(f"⚠️ Expandiendo video de {len(frames)} a {min_frames_needed} frames mínimos")
            frames = self._expandir_frames_para_duracion_masiva(frames, min_frames_needed)
        elif len(frames) > max_frames_allowed:
            print(f"⚠️ Optimizando video de {len(frames)} a {max_frames_allowed} frames máximos")
            frames = self._optimizar_frames_para_video(frames, max_frames_allowed)
        
        # *** FILTRADO FINAL ABSOLUTO ***
        frames = [f for f in frames if f is not None and isinstance(f, dict)]
        
        # *** ESTADÍSTICAS FINALES SEGURAS ***
        final_violence_after = len([f for f in frames if f.get('is_violence_frame', False)])
        final_sequence_after = len([f for f in frames if f.get('is_violence_sequence', False) and not f.get('is_violence_frame', False)])
        
        print(f"📹 FINAL: {len(frames)} frames para video de evidencia")
        print(f"📹 Duración estimada: {len(frames)/self.fps:.2f} segundos a {self.fps} FPS")
        print(f"📹 Violencia confirmada final: {final_violence_after} frames ({(final_violence_after/len(frames)*100):.1f}%)")
        print(f"📹 Secuencia de análisis final: {final_sequence_after} frames ({(final_sequence_after/len(frames)*100):.1f}%)")
        print(f"📹 Contenido relevante total: {((final_violence_after + final_sequence_after)/len(frames)*100):.1f}%")
        
        return frames
    
    # *** NUEVO MÉTODO: Expandir contenido relevante ***
    def _expand_relevant_content(self, frames: List[Dict], min_relevant_frames: int) -> List[Dict]:
        """NUEVO: Expande específicamente el contenido relevante (violencia + secuencia)"""
        violence_frames = [f for f in frames if f.get('is_violence_frame', False)]
        sequence_frames = [f for f in frames if f.get('is_violence_sequence', False) and not f.get('is_violence_frame', False)]
        normal_frames = [f for f in frames if not f.get('is_violence_sequence', False) and not f.get('is_violence_frame', False)]
        
        current_relevant = len(violence_frames) + len(sequence_frames)
        needed_relevant = min_relevant_frames - current_relevant
        
        if needed_relevant <= 0:
            return frames
        
        print(f"🔄 Expandiendo contenido relevante: {current_relevant} → {min_relevant_frames}")
        
        expanded_relevant = violence_frames + sequence_frames
        
        # PRIORIDAD 1: Duplicar frames de violencia confirmada
        if violence_frames and needed_relevant > 0:
            violence_duplications = min(needed_relevant, len(violence_frames) * 6)
            for i in range(violence_duplications):
                if len(expanded_relevant) >= min_relevant_frames:
                    break
                idx = i % len(violence_frames)
                duplicate = violence_frames[idx].copy()
                duplicate['frame'] = violence_frames[idx]['frame'].copy()
                duplicate['timestamp'] = violence_frames[idx]['timestamp'] + timedelta(microseconds=i*50)
                duplicate['expanded_violence'] = True
                duplicate['expansion_type'] = 'violence_expansion'
                expanded_relevant.append(duplicate)
            
            needed_relevant = min_relevant_frames - len(expanded_relevant)
        
        # PRIORIDAD 2: Duplicar frames de secuencia
        if sequence_frames and needed_relevant > 0:
            sequence_duplications = min(needed_relevant, len(sequence_frames) * 4)
            for i in range(sequence_duplications):
                if len(expanded_relevant) >= min_relevant_frames:
                    break
                idx = i % len(sequence_frames)
                duplicate = sequence_frames[idx].copy()
                duplicate['frame'] = sequence_frames[idx]['frame'].copy()
                duplicate['timestamp'] = sequence_frames[idx]['timestamp'] + timedelta(microseconds=i*75)
                duplicate['expanded_sequence'] = True
                duplicate['expansion_type'] = 'sequence_expansion'
                expanded_relevant.append(duplicate)
        
        # Combinar con frames normales
        all_frames = expanded_relevant + normal_frames
        all_frames.sort(key=lambda x: x['timestamp'])
        
        print(f"📹 Contenido relevante expandido a {len([f for f in all_frames if f.get('is_violence_frame', False) or f.get('is_violence_sequence', False)])} frames")
        
        return all_frames
    
    def _optimizar_frames_para_video(self, frames: List[Dict], max_frames: int) -> List[Dict]:
        """NUEVO: Optimiza los frames para un video de duración adecuada"""
        if len(frames) <= max_frames:
            return frames
        
        # Separar frames por tipo
        violence_frames = [f for f in frames if f.get('is_violence_frame', False)]
        sequence_frames = [f for f in frames if f.get('is_violence_sequence', False) and not f.get('is_violence_frame', False)]
        normal_frames = [f for f in frames if not f.get('is_violence_sequence', False) and not f.get('is_violence_frame', False)]
        
        print(f"🎬 Optimizando video: {len(violence_frames)} violencia, {len(sequence_frames)} secuencia, {len(normal_frames)} normales")
        
        # Prioridad: mantener TODOS los frames de violencia
        selected = list(violence_frames)
        remaining_slots = max_frames - len(selected)
        
        # Agregar frames de secuencia (análisis)
        if remaining_slots > 0 and sequence_frames:
            sequence_to_add = min(len(sequence_frames), remaining_slots // 2)
            selected.extend(sequence_frames[:sequence_to_add])
            remaining_slots -= sequence_to_add
        
        # Rellenar con frames normales si es necesario
        if remaining_slots > 0 and normal_frames:
            normal_to_add = min(len(normal_frames), remaining_slots)
            selected.extend(normal_frames[:normal_to_add])
        
        # Ordenar por timestamp para mantener secuencia temporal
        selected.sort(key=lambda x: x['timestamp'])
        
        print(f"🎬 Video optimizado: {len(selected)} frames seleccionados")
        return selected

    def _draw_violence_overlay_mejorado(self, frame: np.ndarray, violence_info: Dict) -> np.ndarray:
        """CORREGIDO: Overlay diferenciado según tipo de frame"""
        height, width = frame.shape[:2]
        probability = violence_info.get('probabilidad', 0.0)
        frames_analizados = violence_info.get('frames_analizados', 0)
        is_confirmed = violence_info.get('detectada', False)
        es_secuencia = violence_info.get('es_secuencia_violencia', False)
        es_contexto = violence_info.get('es_contexto_secuencia', False)
        
        # *** CORRECCIÓN: Color y texto según tipo de frame ***
        if is_confirmed:
            color = (0, 0, 255)  # Rojo para violencia confirmada
            estado_texto = "VIOLENCIA DETECTADA"
            intensidad_overlay = 0.35
        elif es_secuencia:
            color = (0, 165, 255)  # Naranja para secuencia de análisis
            estado_texto = "SECUENCIA EN ANÁLISIS"
            intensidad_overlay = 0.25
        elif es_contexto:
            color = (0, 255, 255)  # Amarillo para contexto
            estado_texto = "CONTEXTO DE VIOLENCIA"
            intensidad_overlay = 0.15
        else:
            color = (128, 128, 128)  # Gris para otros
            estado_texto = "PROCESANDO..."
            intensidad_overlay = 0.10
        
        # *** Overlay escalado según importancia ***
        overlay_height = 85
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, overlay_height), color, -1)
        frame = cv2.addWeighted(frame, 1 - intensidad_overlay, overlay, intensidad_overlay, 0)
        
        # *** Texto principal ***
        cv2.putText(frame, estado_texto, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
        # *** Información específica ***
        if is_confirmed:
            cv2.putText(frame, f"Probabilidad: {probability:.1%}", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        elif es_secuencia:
            cv2.putText(frame, f"Frames batch: {frames_analizados}/8", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        elif es_contexto:
            frames_desde = violence_info.get('frames_desde_violencia', 0)
            cv2.putText(frame, f"Contexto +{frames_desde} frames", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # *** Timestamp ***
        timestamp_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        cv2.putText(frame, timestamp_str, (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        
        return frame
    
    def _expand_violence_content(self, frames: List[Dict], min_violence_frames: int) -> List[Dict]:
        """NUEVO: Expande específicamente el contenido de violencia"""
        violence_frames = [f for f in frames if f.get('is_violence_frame', False)]
        non_violence_frames = [f for f in frames if not f.get('is_violence_frame', False)]
        
        current_violence_count = len(violence_frames)
        needed_violence_frames = min_violence_frames - current_violence_count
        
        if needed_violence_frames <= 0:
            return frames
        
        print(f"🔄 Expandiendo contenido de violencia: {current_violence_count} → {min_violence_frames}")
        
        # Expandir frames de violencia existentes
        expanded_violence = list(violence_frames)
        
        # Duplicar frames de violencia para alcanzar el mínimo
        duplication_rounds = (needed_violence_frames // len(violence_frames)) + 1
        
        for round_num in range(duplication_rounds):
            if len(expanded_violence) >= min_violence_frames:
                break
                
            for original_frame in violence_frames:
                if len(expanded_violence) >= min_violence_frames:
                    break
                    
                # Crear duplicado con timestamp ligeramente diferente
                duplicate = original_frame.copy()
                duplicate['frame'] = original_frame['frame'].copy()
                duplicate['timestamp'] = original_frame['timestamp'] + timedelta(microseconds=round_num*100)
                duplicate['expanded_violence'] = True
                duplicate['expansion_round'] = round_num
                expanded_violence.append(duplicate)
        
        # Combinar con frames no violentos
        all_frames = expanded_violence + non_violence_frames
        
        # Ordenar por timestamp
        all_frames.sort(key=lambda x: x['timestamp'])
        
        return all_frames[:len(frames) + needed_violence_frames]
    
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
        
    def _finish_recording(self):
        """CORREGIDO: Finaliza la grabación y guarda el video de evidencia"""
        if not self.is_recording:
            print("⚠️ No hay grabación activa para finalizar")
            return
        
        try:
            print("📹 Finalizando grabación de evidencia...")
            
            # Marcar fin de grabación
            self.is_recording = False
            self.violence_active = False
            
            # Extraer frames para el video
            frames_evidencia = self._extract_evidence_frames()
            
            if not frames_evidencia:
                print("❌ No hay frames para crear video de evidencia")
                return
            
            # Preparar datos para guardar
            save_data = {
                'frames': frames_evidencia,
                'camara_id': getattr(self, 'current_camera_id', 1),
                'violence_start_time': self.violence_start_time,
                'incidente_id': getattr(self, 'current_incident_id', None),
                'timestamp': datetime.now()
            }
            
            # Agregar a la cola de guardado
            try:
                self.save_queue.put_nowait(save_data)
                print(f"✅ Video de evidencia agregado a cola de guardado")
                print(f"📊 Frames en video: {len(frames_evidencia)}")
                
                # Estadísticas de contenido
                violence_frames = len([f for f in frames_evidencia if f.get('is_violence_frame', False)])
                sequence_frames = len([f for f in frames_evidencia if f.get('is_violence_sequence', False)])
                print(f"📊 Frames de violencia: {violence_frames}")
                print(f"📊 Frames de secuencia: {sequence_frames}")
                
            except queue.Full:
                print("❌ Cola de guardado llena, descartando video")
                
        except Exception as e:
            print(f"❌ Error finalizando grabación: {e}")
            import traceback
            print(traceback.format_exc())
        finally:
            # *** CORREGIDO: Reset de variables con verificación de existencia ***
            self.violence_start_time = None
            self.violence_end_time = None
            
            # Solo eliminar si existe
            if hasattr(self, 'violence_end_grace_period'):
                delattr(self, 'violence_end_grace_period')
                
            # *** NUEVO: Limpiar otros estados relacionados ***
            self.last_violence_state = False
            self.violence_active = False

    def _expandir_frames_para_duracion_masiva(self, frames_originales: List[Dict], frames_objetivo: int) -> List[Dict]:
        """MEJORADO: Expande frames para alcanzar duración objetivo priorizando violencia"""
        if not frames_originales:
            return []
        
        frames_expandidos = frames_originales.copy()
        
        # Si ya tenemos suficientes frames, devolver
        if len(frames_expandidos) >= frames_objetivo:
            return frames_expandidos[:frames_objetivo]
        
        print(f"📹 Expandiendo frames de {len(frames_originales)} a {frames_objetivo}")
        
        # Separar frames por tipo para duplicación inteligente
        violence_frames = [f for f in frames_originales if f.get('is_violence_frame', False)]
        sequence_frames = [f for f in frames_originales if f.get('is_violence_sequence', False) and not f.get('is_violence_frame', False)]
        normal_frames = [f for f in frames_originales if not f.get('is_violence_sequence', False) and not f.get('is_violence_frame', False)]
        
        frames_faltantes = frames_objetivo - len(frames_expandidos)
        
        # PRIORIDAD 1: Duplicar frames de violencia confirmada masivamente
        if violence_frames and frames_faltantes > 0:
            duplicaciones_violencia = min(frames_faltantes, len(violence_frames) * 8)
            for i in range(duplicaciones_violencia):
                idx = i % len(violence_frames)
                frame_duplicado = violence_frames[idx].copy()
                frame_duplicado['frame'] = violence_frames[idx]['frame'].copy()
                frame_duplicado['timestamp'] = violence_frames[idx]['timestamp'] + timedelta(microseconds=100 + i*10)
                frame_duplicado['duplicated'] = True
                frame_duplicado['duplicate_round'] = 'violence_expansion'
                frames_expandidos.append(frame_duplicado)
            
            frames_faltantes = frames_objetivo - len(frames_expandidos)
            print(f"📹 Duplicación violencia: +{duplicaciones_violencia} frames")
        
        # PRIORIDAD 2: Duplicar frames de secuencia de análisis
        if sequence_frames and frames_faltantes > 0:
            duplicaciones_secuencia = min(frames_faltantes, len(sequence_frames) * 4)
            for i in range(duplicaciones_secuencia):
                idx = i % len(sequence_frames)
                frame_duplicado = sequence_frames[idx].copy()
                frame_duplicado['frame'] = sequence_frames[idx]['frame'].copy()
                frame_duplicado['timestamp'] = sequence_frames[idx]['timestamp'] + timedelta(microseconds=200 + i*20)
                frame_duplicado['duplicated'] = True
                frame_duplicado['duplicate_round'] = 'sequence_expansion'
                frames_expandidos.append(frame_duplicado)
            
            frames_faltantes = frames_objetivo - len(frames_expandidos)
            print(f"📹 Duplicación secuencia: +{duplicaciones_secuencia} frames")
        
        # PRIORIDAD 3: Duplicar frames normales si es necesario
        if normal_frames and frames_faltantes > 0:
            duplicaciones_normales = min(frames_faltantes, len(normal_frames) * 2)
            for i in range(duplicaciones_normales):
                idx = i % len(normal_frames)
                frame_duplicado = normal_frames[idx].copy()
                frame_duplicado['frame'] = normal_frames[idx]['frame'].copy()
                frame_duplicado['timestamp'] = normal_frames[idx]['timestamp'] + timedelta(microseconds=300 + i*30)
                frame_duplicado['duplicated'] = True
                frame_duplicado['duplicate_round'] = 'normal_expansion'
                frames_expandidos.append(frame_duplicado)
            
            print(f"📹 Duplicación normal: +{duplicaciones_normales} frames")
        
        # PRIORIDAD 4: Si aún faltan frames, repetir todo el ciclo
        while len(frames_expandidos) < frames_objetivo:
            frames_faltantes = frames_objetivo - len(frames_expandidos)
            if frames_faltantes <= 0:
                break
            
            # Repetir todo el conjunto de frames originales
            for frame in frames_originales[:min(frames_faltantes, len(frames_originales))]:
                frame_repetido = frame.copy()
                frame_repetido['frame'] = frame['frame'].copy()
                frame_repetido['timestamp'] = frame['timestamp'] + timedelta(microseconds=500 + len(frames_expandidos)*5)
                frame_repetido['repeated'] = True
                frames_expandidos.append(frame_repetido)
            
            # Evitar bucle infinito
            if len(frames_expandidos) >= frames_objetivo * 2:
                break
        
        # Limitar al objetivo exacto
        frames_expandidos = frames_expandidos[:frames_objetivo]
        
        # Ordenar por timestamp para mantener secuencia temporal
        frames_expandidos.sort(key=lambda x: x['timestamp'])
        
        print(f"📹 Expansión completada: {len(frames_expandidos)} frames finales")
        return frames_expandidos

    def set_camera_id(self, camera_id: int):
        """Establece el ID de la cámara actual"""
        self.current_camera_id = camera_id
        print(f"📹 Camera ID {camera_id} asignado al evidence_recorder")

# Instancia global
evidence_recorder = ViolenceEvidenceRecorder()