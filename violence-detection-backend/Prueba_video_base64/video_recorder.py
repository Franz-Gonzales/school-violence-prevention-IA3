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

class VoiceActivatedVideoRecorder:
    def __init__(self, output_dir="voice_clips", fps=30, silence_duration=2.0, voice_threshold=200):
        """
        Inicializa el grabador de video activado por voz
        """
        self.output_dir = output_dir
        self.fps = fps
        self.silence_duration = silence_duration
        self.voice_threshold = voice_threshold
        
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Variables de control de grabación
        self.is_recording_video = False
        self.video_writer = None
        self.recording_start_time = None
        self.current_filepath = None
        
        # Variables de audio
        self.is_voice_detected = False
        self.silence_start_time = None
        self.last_voice_time = time.time()
        
        # Configuración de audio
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        # Buffer para suavizar detección de voz - AUMENTADO para más estabilidad
        self.audio_buffer = collections.deque(maxlen=10)
        
        # Configuración de video
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Cambié a XVID para mejor compatibilidad
        self.frame_width = None
        self.frame_height = None
        
        # Control de hilos
        self.running = False
        self.audio_thread = None
        
        # Variables para control de timing
        self.last_frame_time = 0
        self.frame_interval = 1.0 / self.fps
        
    def process_frame(self, frame):
        """
        Procesa un frame individual
        """
        processed_frame = frame.copy()
        
        # Agregar indicador visual de estado de grabación
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_color = (0, 255, 0) if self.is_recording_video else (128, 128, 128)
        status_text = "GRABANDO" if self.is_recording_video else "ESPERANDO VOZ"
        
        # Fondo para el texto
        cv2.rectangle(processed_frame, (10, 10), (400, 80), (0, 0, 0), -1)
        cv2.rectangle(processed_frame, (10, 10), (400, 80), status_color, 2)
        
        # Texto de estado
        cv2.putText(processed_frame, status_text, 
                   (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(processed_frame, timestamp, 
                   (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Indicador de nivel de audio
        if self.audio_buffer:
            audio_level = np.mean(self.audio_buffer)
            bar_width = int((audio_level / max(self.voice_threshold, 1)) * 200)
            bar_width = min(bar_width, 200)
            
            cv2.rectangle(processed_frame, (420, 30), (620, 50), (50, 50, 50), -1)
            if bar_width > 0:
                color = (0, 255, 0) if self.is_voice_detected else (0, 255, 255)
                cv2.rectangle(processed_frame, (420, 30), (420 + bar_width, 50), color, -1)
            
            cv2.putText(processed_frame, f"Audio: {int(audio_level)}", 
                       (420, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Mostrar tiempo de grabación si está grabando
        if self.is_recording_video and self.recording_start_time:
            recording_time = time.time() - self.recording_start_time
            time_text = f"Grabando: {recording_time:.1f}s"
            cv2.putText(processed_frame, time_text, 
                       (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return processed_frame
    
    def detect_voice_activity(self):
        """
        Hilo separado para detectar actividad de voz con mejor estabilidad
        """
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            print("🎤 Sistema de audio iniciado - Habla para comenzar a grabar")
            
            consecutive_voice_count = 0
            consecutive_silence_count = 0
            VOICE_CONFIRM_THRESHOLD = 3  # Necesita 3 detecciones consecutivas para confirmar voz
            SILENCE_CONFIRM_THRESHOLD = 5  # Necesita 5 detecciones consecutivas para confirmar silencio
            
            while self.running:
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    
                    # Calcular nivel de audio RMS
                    count = len(data)//2
                    if count > 0:
                        format_str = "%dh" % count
                        shorts = struct.unpack(format_str, data)
                        sum_squares = sum(sample * sample for sample in shorts)
                        rms = math.sqrt(sum_squares / count)
                    else:
                        rms = 0
                    
                    self.audio_buffer.append(rms)
                    
                    # Determinar si hay voz (promedio del buffer)
                    avg_rms = np.mean(self.audio_buffer) if self.audio_buffer else 0
                    voice_detected_now = avg_rms > self.voice_threshold
                    
                    current_time = time.time()
                    
                    # Sistema de confirmación para evitar detecciones falsas
                    if voice_detected_now:
                        consecutive_voice_count += 1
                        consecutive_silence_count = 0
                        
                        # Confirmar voz solo después de varias detecciones consecutivas
                        if consecutive_voice_count >= VOICE_CONFIRM_THRESHOLD:
                            if not self.is_voice_detected:
                                print(f"🔊 Voz confirmada (nivel: {avg_rms:.0f})")
                                # Iniciar grabación solo si no estamos grabando ya
                                if not self.is_recording_video:
                                    self.start_video_recording()
                            
                            self.is_voice_detected = True
                            self.last_voice_time = current_time
                            self.silence_start_time = None
                    
                    else:
                        consecutive_silence_count += 1
                        consecutive_voice_count = 0
                        
                        # Confirmar silencio solo después de varias detecciones consecutivas
                        if consecutive_silence_count >= SILENCE_CONFIRM_THRESHOLD:
                            if self.is_voice_detected:
                                self.silence_start_time = current_time
                                print("🔇 Silencio confirmado")
                            
                            self.is_voice_detected = False
                            
                            # Parar grabación después de silencio prolongado
                            if (self.is_recording_video and 
                                self.silence_start_time and 
                                (current_time - self.silence_start_time) >= self.silence_duration):
                                print(f"⏰ Deteniendo grabación tras {self.silence_duration}s de silencio")
                                self.stop_video_recording()
                    
                    time.sleep(0.05)  # 50ms entre lecturas de audio
                
                except Exception as e:
                    print(f"Error en audio: {e}")
                    time.sleep(0.1)
        
        except Exception as e:
            print(f"Error inicializando audio: {e}")
        
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
            audio.terminate()

    def start_video_recording(self):
        """
        Inicia la grabación de video
        """
        if self.is_recording_video:
            return
        
        if self.frame_width is None or self.frame_height is None:
            print("⚠️ Dimensiones de frame no disponibles aún")
            return
        
        # Crear nombre de archivo único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voice_clip_{timestamp}.avi"  # Cambié a .avi para XVID
        filepath = os.path.join(self.output_dir, filename)
        
        # Crear VideoWriter con configuración específica
        self.video_writer = cv2.VideoWriter(
            filepath, 
            self.fourcc, 
            self.fps,  # FPS exacto como int
            (self.frame_width, self.frame_height)
        )
        
        if not self.video_writer.isOpened():
            print(f"❌ Error: No se pudo crear archivo {filepath}")
            self.video_writer = None
            return
        
        self.is_recording_video = True
        self.current_filepath = filepath
        self.recording_start_time = time.time()
        print(f"🎬 Grabación iniciada: {filename}")
    
    def stop_video_recording(self):
        """
        Detiene la grabación de video y guarda el archivo
        """
        if not self.is_recording_video or self.video_writer is None:
            return
        
        self.is_recording_video = False
        
        # Liberar el video writer de manera segura
        try:
            self.video_writer.release()
        except:
            pass
        
        self.video_writer = None
        
        if self.recording_start_time:
            recording_duration = time.time() - self.recording_start_time
            print(f"✅ Clip guardado: {os.path.basename(self.current_filepath)} ({recording_duration:.2f}s)")
        
        self.current_filepath = None
        self.recording_start_time = None
    
    def start_camera_processing(self, camera_index=0):
        """
        Inicia el procesamiento de la cámara con timing preciso
        """
        # Inicializar cámara
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"❌ Error: No se pudo abrir la cámara {camera_index}")
            return
        
        # Configurar cámara
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        
        self.frame_width = actual_width
        self.frame_height = actual_height
        
        print(f"📹 Cámara configurada: {actual_width}x{actual_height} @ {actual_fps} FPS")
        print(f"📁 Clips se guardarán en: {self.output_dir}")
        print(f"🔊 Umbral de voz: {self.voice_threshold}")
        print(f"⏱️ Tiempo de silencio: {self.silence_duration}s")
        print("\n🎯 INSTRUCCIONES:")
        print("- Habla continuamente para iniciar grabación")
        print("- La grabación para tras 2 segundos de silencio")
        print("- Presiona 'q' para salir")
        print("- Presiona 'r' para grabar manualmente")
        print("- Presiona '+'/'-' para ajustar sensibilidad\n")
        
        self.running = True
        
        # Iniciar hilo de detección de audio
        self.audio_thread = threading.Thread(target=self.detect_voice_activity, daemon=True)
        self.audio_thread.start()
        
        # Variables para control de timing preciso
        self.last_frame_time = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                
                # Leer frame de la cámara
                ret, frame = cap.read()
                
                if not ret:
                    print("❌ Error leyendo frame de la cámara")
                    break
                
                # Control de timing - solo procesar si ha pasado el tiempo correcto
                time_since_last_frame = current_time - self.last_frame_time
                
                if time_since_last_frame >= self.frame_interval:
                    # Procesar frame para mostrar
                    processed_frame = self.process_frame(frame)
                    
                    # Si estamos grabando, escribir frame al video
                    if self.is_recording_video and self.video_writer is not None:
                        try:
                            self.video_writer.write(frame)  # Usar frame original
                        except Exception as e:
                            print(f"Error escribiendo frame: {e}")
                            self.stop_video_recording()
                    
                    # Actualizar tiempo del último frame procesado
                    self.last_frame_time = current_time
                
                # Mostrar frame procesado (esto no afecta la grabación)
                processed_frame = self.process_frame(frame)
                cv2.imshow('Video con Grabación por Voz', processed_frame)
                
                # Manejar entrada de teclado
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    if not self.is_recording_video:
                        self.start_video_recording()
                    else:
                        self.stop_video_recording()
                elif key == ord('+') or key == ord('='):
                    self.voice_threshold += 25
                    print(f"🔊 Umbral aumentado: {self.voice_threshold}")
                elif key == ord('-'):
                    self.voice_threshold = max(25, self.voice_threshold - 25)
                    print(f"🔊 Umbral reducido: {self.voice_threshold}")
                
                # Pausa muy pequeña para no saturar el CPU
                time.sleep(0.001)
        
        except KeyboardInterrupt:
            print("\n⚠️ Interrumpido por el usuario")
        
        finally:
            # Detener grabación si está activa
            if self.is_recording_video:
                self.stop_video_recording()
            
            # Limpiar recursos
            self.running = False
            cap.release()
            cv2.destroyAllWindows()
            
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=2)
            
            print("🏁 Sistema finalizado")

def main():
    """
    Función principal
    """
    print("=== 🎬 GRABADOR DE VIDEO ACTIVADO POR VOZ ===\n")
    
    # Configuración mejorada
    OUTPUT_DIR = "voice_clips"
    FPS = 15
    SILENCE_DURATION = 2.0  # segundos de silencio antes de parar
    VOICE_THRESHOLD = 150   # umbral más bajo para mayor sensibilidad
    
    # Crear grabador
    recorder = VoiceActivatedVideoRecorder(
        output_dir=OUTPUT_DIR,
        fps=FPS,
        silence_duration=SILENCE_DURATION,
        voice_threshold=VOICE_THRESHOLD
    )
    
    print("🚀 Iniciando sistema...")
    recorder.start_camera_processing(camera_index=0)

if __name__ == "__main__":
    main()