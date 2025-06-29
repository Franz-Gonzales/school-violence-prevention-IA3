import os
from moviepy.editor import VideoFileClip

# Parámetros predefinidos
INPUT_VIDEO_PATH = r"C:\GONZALES\dataset_violencia\videos\videos_nuevos"  # Cambia esto a la ruta de tu video
OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\videos\videos_procesados"     # Carpeta donde se guardarán los clips
OUTPUT_FILENAME = "pelea_recorta.mp4"  # Nombre del archivo de salida

# Define los segmentos a extraer como una lista de tuplas (inicio, fin, nombre)
# Puedes añadir múltiples segmentos si quieres extraer varias partes del mismo video
SEGMENTS_TO_EXTRACT = [
    (8, 13, "video_prueba"),  # (segundo_inicio, segundo_fin, nombre_archivo)
    # Puedes añadir más segmentos si lo necesitas, por ejemplo:
    # (18, 22, "pelea_2"),
    # (35, 42, "pelea_3"),
]

def extract_video_segments(input_video_path, output_folder, segments):
    """
    Extrae segmentos específicos de un video.
    
    Args:
        input_video_path (str): Ruta al video de entrada
        output_folder (str): Carpeta donde se guardarán los segmentos
        segments (list): Lista de tuplas (inicio, fin, nombre) que definen los segmentos a extraer
    """
    # Crear carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta creada: {output_folder}")
    
    # Cargar el video
    print(f"Cargando video: {input_video_path}")
    video = VideoFileClip(input_video_path)
    
    # Obtener la duración total del video
    duration = video.duration
    print(f"Duración total del video: {duration:.2f} segundos")
    
    # Procesar cada segmento
    for i, (start_time, end_time, segment_name) in enumerate(segments):
        # Validar tiempos
        if start_time < 0 or end_time > duration or start_time >= end_time:
            print(f"Error en segmento {i+1}: tiempos inválidos ({start_time} - {end_time})")
            continue
            
        print(f"Extrayendo segmento {i+1}/{len(segments)}: {start_time}s - {end_time}s")
        
        # Crear subclip
        segment = video.subclip(start_time, end_time)
        
        # Generar nombre de archivo
        output_filename = f"{segment_name}.mp4"
        output_path = os.path.join(output_folder, output_filename)
        
        # Guardar el segmento con alta calidad para evitar degradación
        print(f"Guardando: {output_path}")
        segment.write_videofile(
            output_path,
            codec="libx264",           # Codec de video H.264 (alta compatibilidad)
            audio_codec="aac",         # Codec de audio AAC (alta compatibilidad)
            bitrate="8000k",           # Bitrate alto para mantener calidad
            preset="slow",             # Codificación más lenta pero mejor calidad
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            threads=4                  # Usar múltiples núcleos para codificación más rápida
        )
    
    # Cerrar el video original
    video.close()
    print("¡Proceso completado!")

if __name__ == "__main__":
    # Ejecutar la función con los parámetros predefinidos
    extract_video_segments(INPUT_VIDEO_PATH, OUTPUT_FOLDER, SEGMENTS_TO_EXTRACT)
    
    # Mensaje para indicar que el proceso ha terminado
    print("\n" + "="*50)
    print(f"Se han extraído {len(SEGMENTS_TO_EXTRACT)} segmentos del video!")
    print(f"Los clips se han guardado en la carpeta: {OUTPUT_FOLDER}")
    print("="*50)