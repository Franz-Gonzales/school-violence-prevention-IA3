
import os
from moviepy.editor import VideoFileClip

# Parámetros predefinidos (puedes modificar estos valores directamente en el código)
INPUT_VIDEO_PATH = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\procesados\Video de WhatsApp 2025-04-20 a las 22.26.38_c0c6b60c.mp4"  # Cambia esto a la ruta de tu video
OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_a_procesar"     # Carpeta donde se guardarán los clips
SEGMENT_DURATION = 5                     # Duración de cada clip en segundos
PREFIX = "ambioud"                  # Prefijo para los nombres de archivos

def split_video(input_video_path, output_folder, segment_duration=5, prefix="clip"):
    
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
    
    # Calcular el número de segmentos
    num_segments = int(duration // segment_duration)
    if duration % segment_duration > 0:
        num_segments += 1  # Para el último segmento parcial
    
    print(f"Dividiendo en {num_segments} segmentos de {segment_duration} segundos...")
    
    # Procesar cada segmento
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, duration)
        
        # Si el último segmento es demasiado corto, podemos omitirlo o ajustar el comportamiento
        if end_time - start_time < 1:  # Si es menor a 1 segundo, omitirlo
            continue
        
        # Crear subclip
        segment = video.subclip(start_time, end_time)
        
        # Generar nombre de archivo con padding de ceros (001, 002, etc.)
        output_filename = f"{prefix}_{str(i+1).zfill(3)}.mp4"
        output_path = os.path.join(output_folder, output_filename)
        
        # Guardar el segmento
        print(f"Guardando segmento {i+1}/{num_segments}: {start_time:.2f}s - {end_time:.2f}s")
        segment.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True
        )
    
    # Cerrar el video original
    video.close()
    print("¡Proceso completado!")

if __name__ == "__main__":
    # Ejecutar la función con los parámetros predefinidos
    split_video(INPUT_VIDEO_PATH, OUTPUT_FOLDER, SEGMENT_DURATION, PREFIX)
    
    # Mensaje para indicar que el proceso ha terminado
    print("\n" + "="*50)
    print(f"Se ha completado la división del video!")
    print(f"Los clips se han guardado en la carpeta: {OUTPUT_FOLDER}")
    print(f"Prefijo utilizado: {PREFIX}")
    print(f"Duración de cada clip: {SEGMENT_DURATION} segundos")
    print("="*50)