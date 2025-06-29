import os
from moviepy.editor import VideoFileClip

# Parámetros predefinidos (puedes modificar estos valores directamente en el código)
INPUT_VIDEO_PATH = r"C:\GONZALES\Dataset-violence\violence_procesado\1d_352.mp4"  # Cambia esto a la ruta de tu video
OUTPUT_FOLDER = r"C:\GONZALES\Dataset-violence\procesar\frames"         # Carpeta donde se guardarán los frames
FRAMES_PER_SECOND = 5                                                   # Número de frames por segundo a extraer
PREFIX = "frame"                                                        # Prefijo para los nombres de las imágenes

def extract_frames(input_video_path, output_folder, frames_per_second=5, prefix="frame"):
    # Crear carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta creada: {output_folder}")
    
    # Cargar el video
    print(f"Cargando video: {input_video_path}")
    video = VideoFileClip(input_video_path)
    
    # Obtener la duración total del video
    duration = video.duration
    print(f"Duración del video: {duration:.2f} segundos")
    
    # Calcular el intervalo entre frames (en segundos)
    frame_interval = 1.0 / frames_per_second  # Por ejemplo, para 5 FPS, un frame cada 0.2 segundos
    
    # Calcular el número total de frames a extraer
    total_frames = int(duration * frames_per_second)
    print(f"Extrayendo {total_frames} frames a {frames_per_second} FPS (un frame cada {frame_interval:.2f} segundos)...")
    
    # Extraer y guardar cada frame
    for i in range(total_frames):
        # Calcular el tiempo exacto del frame
        frame_time = i * frame_interval
        
        # Asegurarse de no exceder la duración del video
        if frame_time > duration:
            break
        
        # Extraer el frame en el tiempo especificado
        frame = video.get_frame(frame_time)
        
        # Generar nombre de archivo con padding de ceros (001, 002, etc.)
        output_filename = f"{prefix}_{str(i+1).zfill(4)}.png"
        output_path = os.path.join(output_folder, output_filename)
        
        # Guardar el frame como imagen
        print(f"Guardando frame {i+1}/{total_frames} en t={frame_time:.2f}s: {output_filename}")
        video.save_frame(output_path, t=frame_time)
    
    # Cerrar el video
    video.close()
    print("¡Extracción de frames completada!")

if __name__ == "__main__":
    # Ejecutar la función con los parámetros predefinidos
    extract_frames(INPUT_VIDEO_PATH, OUTPUT_FOLDER, FRAMES_PER_SECOND, PREFIX)
    
    # Mensaje final
    print("\n" + "="*50)
    print(f"Se ha completado la extracción de frames!")
    print(f"Los frames se han guardado en la carpeta: {OUTPUT_FOLDER}")
    print(f"Prefijo utilizado: {PREFIX}")
    print(f"Frames por segundo: {FRAMES_PER_SECOND}")
    print("="*50)