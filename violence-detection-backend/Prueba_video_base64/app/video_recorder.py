import cv2
import numpy as np
import os
import time
from datetime import datetime
import threading
import pyaudio
import struct
import math
import collections
import base64
import ffmpeg
import subprocess

class SimpleVideoRecorder:
    def __init__(self, output_dir="temp_videos", fps=15, max_duration=10):  # AUMENTAR FPS A 30
        """
        Grabador de video simplificado para el prototipo
        """
        self.output_dir = output_dir
        self.fps = fps
        self.max_duration = max_duration
        
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Variables de control
        self.is_recording = False
        self.video_writer = None
        self.recording_start_time = None
        self.current_filepath = None
        
        # MEJORAR CONFIGURACIÓN DE VIDEO
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.extension = '.mp4'
        self.frame_width = 640   # AUMENTAR RESOLUCIÓN
        self.frame_height = 480  # AUMENTAR RESOLUCIÓN
        
        # VARIABLES DE CONTROL DE TIMING MEJORADAS
        self.frame_interval = 1.0 / self.fps  # Intervalo entre frames
        self.last_frame_time = 0
        self.frames_written = 0  # Contador de frames escritos
        
        print(f"📹 Video recorder inicializado - {self.fps} FPS, {self.frame_width}x{self.frame_height}")

    def start_recording(self):
        """Inicia la grabación de video con timing mejorado"""
        if self.is_recording:
            return None
        
        # Crear nombre de archivo único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}{self.extension}"
        filepath = os.path.join(self.output_dir, filename)
        
        # Crear VideoWriter con FPS exacto
        self.video_writer = cv2.VideoWriter(
            filepath, 
            self.fourcc, 
            self.fps,  # FPS exacto
            (self.frame_width, self.frame_height)
        )
        
        if not self.video_writer.isOpened():
            print(f"Error: No se pudo crear archivo {filepath}")
            return None
        
        self.is_recording = True
        self.current_filepath = filepath
        self.recording_start_time = time.time()
        self.last_frame_time = time.time()  # Inicializar timing
        self.frames_written = 0  # Resetear contador
        print(f"Grabación iniciada: {filename}")
        return filename
    
    def stop_recording(self):
        """Detiene la grabación con información de timing"""
        if not self.is_recording or self.video_writer is None:
            return None
        
        self.is_recording = False
        self.video_writer.release()
        self.video_writer = None
        
        filepath = self.current_filepath
        self.current_filepath = None
        
        # CALCULAR DURACIÓN REAL
        if self.recording_start_time:
            actual_duration = time.time() - self.recording_start_time
            expected_frames = int(actual_duration * self.fps)
            print(f"📊 Duración real: {actual_duration:.2f}s")
            print(f"📊 Frames escritos: {self.frames_written}")
            print(f"📊 Frames esperados: {expected_frames}")
            print(f"📊 FPS efectivo: {self.frames_written / actual_duration:.2f}")
        
        self.recording_start_time = None
        self.frames_written = 0
        
        print(f"Grabación detenida: {os.path.basename(filepath)}")
        return filepath
    
    def record_video_session(self, camera_index=0):
        """
        Graba un video con control de timing mejorado
        """
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"Error: No se pudo abrir la cámara {camera_index}")
            return None
        
        # CONFIGURAR CÁMARA CON FPS REAL
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Verificar FPS real de la cámara
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Cámara configurada: {actual_width}x{actual_height} @ {actual_fps:.1f} FPS")
        print(f"Presiona ESPACIO para iniciar/detener grabación")
        print(f"Presiona 'q' para salir")
        print(f"Duración máxima: {self.max_duration} segundos")
        
        final_video_path = None
        
        try:
            while True:
                current_time = time.time()
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Redimensionar frame para asegurar dimensiones correctas
                frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                
                # Agregar información visual mejorada
                status_text = "GRABANDO" if self.is_recording else "PRESIONA ESPACIO"
                color = (0, 255, 0) if self.is_recording else (0, 0, 255)
                
                # Fondo para el texto
                cv2.rectangle(frame, (10, 10), (500, 80), (0, 0, 0), -1)
                cv2.putText(frame, status_text, (20, 35), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                
                # Mostrar información detallada durante grabación
                if self.is_recording and self.recording_start_time:
                    elapsed = current_time - self.recording_start_time
                    fps_actual = self.frames_written / elapsed if elapsed > 0 else 0
                    
                    cv2.putText(frame, f"Tiempo: {elapsed:.1f}s", 
                               (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    cv2.putText(frame, f"Frames: {self.frames_written} | FPS: {fps_actual:.1f}", 
                               (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # CONTROL DE TIMING PRECISO - Solo escribir frames a la velocidad correcta
                    time_since_last_frame = current_time - self.last_frame_time
                    
                    if time_since_last_frame >= self.frame_interval:
                        # Escribir frame solo si ha pasado el tiempo correcto
                        if self.video_writer is not None:
                            self.video_writer.write(frame)
                            self.frames_written += 1
                            self.last_frame_time = current_time
                    
                    # Detener automáticamente después del tiempo máximo
                    if elapsed >= self.max_duration:
                        final_video_path = self.stop_recording()
                        cap.release()
                        cv2.destroyAllWindows()
                        return final_video_path
                
                # Mostrar frame (esto no afecta la grabación)
                cv2.imshow('Grabador de Video', frame)
                
                # Manejar teclas
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    if self.is_recording:
                        final_video_path = self.stop_recording()
                    break
                elif key == ord(' '):  # Espacio para iniciar/detener
                    if not self.is_recording:
                        self.start_recording()
                    else:
                        final_video_path = self.stop_recording()
                        cap.release()
                        cv2.destroyAllWindows()
                        return final_video_path
        
        except KeyboardInterrupt:
            print("Interrumpido por el usuario")
            if self.is_recording:
                final_video_path = self.stop_recording()
        
        finally:
            if self.is_recording:
                final_video_path = self.stop_recording()
            cap.release()
            cv2.destroyAllWindows()
        
        return final_video_path

def convert_video_to_web_format(input_path, output_path):
    """Convierte video a formato web-compatible respetando FPS original"""
    try:
        print(f"🔄 Convirtiendo {input_path} a formato web...")
        
        # Verificar que FFmpeg está disponible
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ FFmpeg no está instalado o no está en PATH")
            return False
        
        # OBTENER FPS ORIGINAL DEL VIDEO
        try:
            cap = cv2.VideoCapture(input_path)
            original_fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            
            # Usar FPS original o 15 como fallback
            output_fps = str(int(original_fps)) if original_fps > 0 else "15"
            print(f"📊 FPS original detectado: {original_fps}, usando: {output_fps}")
            
        except Exception as e:
            print(f"⚠️ No se pudo detectar FPS original: {e}, usando 15 FPS")
            output_fps = "15"
        
        # COMANDO FFMPEG CORREGIDO - USAR FPS ORIGINAL
        command = [
            'ffmpeg',
            '-i', input_path,                    # Input file
            '-c:v', 'libx264',                   # Video codec H.264
            '-profile:v', 'baseline',            # Profile compatible con web
            '-level', '3.0',                     # Level compatible
            '-pix_fmt', 'yuv420p',              # Pixel format compatible
            '-r', output_fps,                   # USAR FPS ORIGINAL (NO FORZAR 30)
            '-movflags', '+faststart',           # Optimización para web
            '-preset', 'fast',                   # Preset de velocidad
            '-crf', '23',                       # MEJOR CALIDAD (23 es muy bueno)
            '-maxrate', '1M',                   # Límite de bitrate para web
            '-bufsize', '2M',                   # Buffer size
            '-y',                               # Sobrescribir output
            output_path
        ]
        
        print(f"🔧 Comando FFmpeg: {' '.join(command)}")
        
        # Ejecutar conversión
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Video convertido exitosamente: {output_path}")
            
            # Verificar FPS del archivo convertido
            try:
                cap = cv2.VideoCapture(output_path)
                converted_fps = cap.get(cv2.CAP_PROP_FPS)
                cap.release()
                print(f"📊 FPS del archivo convertido: {converted_fps}")
            except:
                pass
            
            # Verificar que el archivo se creó
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                print("❌ El archivo convertido está vacío o no existe")
                return False
        else:
            print(f"❌ Error en FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error convirtiendo video: {e}")
        return False

def video_to_base64(video_path):
    """Convierte un archivo de video a Base64 con conversión web-compatible"""
    try:
        # Verificar que el archivo existe
        if not os.path.exists(video_path):
            print(f"❌ Error: El archivo no existe: {video_path}")
            return None
        
        # Crear archivo temporal convertido
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        converted_path = os.path.join(os.path.dirname(video_path), f"{base_name}_web.mp4")
        
        # Convertir a formato web-compatible
        if not convert_video_to_web_format(video_path, converted_path):
            print("❌ Error: No se pudo convertir el video a formato web")
            return None
        
        # Usar el archivo convertido para Base64
        final_path = converted_path
        
        file_size = os.path.getsize(final_path)
        print(f"📏 Tamaño del archivo convertido: {file_size} bytes")
        
        # Límite de 5MB para el archivo convertido
        if file_size > 5 * 1024 * 1024:
            print(f"⚠️ Advertencia: Archivo convertido muy grande ({file_size} bytes)")
        
        with open(final_path, "rb") as video_file:
            video_data = video_file.read()
            print(f"📖 Datos leídos del archivo convertido: {len(video_data)} bytes")
            
            if len(video_data) == 0:
                print("❌ Error: El archivo convertido está vacío")
                return None
            
            base64_data = base64.b64encode(video_data).decode('utf-8')
            print(f"🔄 Base64 generado: {len(base64_data)} caracteres")
            
            # Verificar que el Base64 es válido
            try:
                decoded_test = base64.b64decode(base64_data)
                if len(decoded_test) != len(video_data):
                    print("❌ Error: Validación de Base64 falló")
                    return None
                print("✅ Base64 validado correctamente")
            except Exception as validation_error:
                print(f"❌ Error validando Base64: {validation_error}")
                return None
        
        # Limpiar archivo convertido temporal
        try:
            os.remove(converted_path)
            print(f"🗑️ Archivo convertido temporal eliminado: {converted_path}")
        except:
            pass
        
        return base64_data
            
    except Exception as e:
        print(f"❌ Error convirtiendo video a Base64: {e}")
        return None

def get_video_info(video_path):
    """Obtiene información del video con validación mejorada"""
    try:
        if not os.path.exists(video_path):
            print(f"❌ Error: El archivo no existe: {video_path}")
            return {'duration': 0, 'file_size': 0}
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Error: No se pudo abrir el video: {video_path}")
            return {'duration': 0, 'file_size': 0}
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        file_size = os.path.getsize(video_path)
        
        print(f"📊 Video info - FPS: {fps}, Frames: {frame_count}, Duración: {duration:.2f}s, Tamaño: {file_size} bytes")
        
        return {
            'duration': duration,
            'file_size': file_size
        }
    except Exception as e:
        print(f"❌ Error obteniendo info del video: {e}")
        return {'duration': 0, 'file_size': 0}