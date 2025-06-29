import os
from moviepy.editor import VideoFileClip

# Parámetros predefinidos
INPUT_VIDEO_PATH = r"C:\GONZALES\dataset_violencia\dataset_V2\videos_a_procesar\violencia\violencia-menores-secundaria.mp4"  # Ruta del video original
OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_V2\videos_extra_a_procesar\procesados"     # Carpeta donde se guardarán los clips
SEGMENT_DURATION = 5                    # Duración de cada subclip (en segundos)
PREFIX = "no_v1lll2"                        # Prefijo para los nombres de archivos

segundo_inicio = 19
segundo_fin = 29

# Define el segmento principal donde ocurre la acción (segundo_inicio, segundo_fin)
ACTION_SEGMENT = (segundo_inicio, segundo_fin)  # Ejemplo: la acción ocurre entre el segundo 20 y 50

def extract_and_split_video(input_video_path, output_folder, action_segment, segment_duration, prefix):
    
    # Crear carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta creada: {output_folder}")
    
    # Cargar el video
    print(f"Cargando video: {input_video_path}")
    original_video = VideoFileClip(input_video_path)
    
    # Obtener la duración total del video
    total_duration = original_video.duration
    print(f"Duración total del video: {total_duration:.2f} segundos")
    
    # Validar el segmento de acción
    start_time, end_time = action_segment
    if start_time < 0 or end_time > total_duration or start_time >= end_time:
        print(f"Error: tiempos inválidos para el segmento de acción ({start_time} - {end_time})")
        original_video.close()
        return
    
    # Extraer el segmento principal donde ocurre la acción
    print(f"Extrayendo segmento principal de acción: {start_time}s - {end_time}s")
    action_segment_clip = original_video.subclip(start_time, end_time)
    
    # Duración del segmento de acción
    action_duration = end_time - start_time
    print(f"Duración del segmento de acción: {action_duration:.2f} segundos")
    
    # Calcular el número de subclips de 5 segundos
    num_subclips = int(action_duration // segment_duration)
    if action_duration % segment_duration > 0:
        num_subclips += 1  # Para el último segmento parcial
    
    print(f"Dividiendo el segmento de acción en {num_subclips} subclips de {segment_duration} segundos...")
    
    # Procesar cada subclip
    for i in range(num_subclips):
        subclip_start = i * segment_duration
        subclip_end = min((i + 1) * segment_duration, action_duration)
        
        # Si el último subclip es demasiado corto, podemos omitirlo o ajustar el comportamiento
        if subclip_end - subclip_start < 1:  # Si es menor a 1 segundo, omitirlo
            continue
        
        # Crear subclip desde el segmento de acción
        print(f"Creando subclip {i+1}/{num_subclips}: {subclip_start:.2f}s - {subclip_end:.2f}s del segmento de acción")
        subclip = action_segment_clip.subclip(subclip_start, subclip_end)
        
        # Calcular tiempo absoluto respecto al video original para el nombre del archivo
        abs_start = start_time + subclip_start
        abs_end = start_time + subclip_end
        
        # Generar nombre de archivo con padding de ceros (001, 002, etc.)
        output_filename = f"{prefix}_{str(i+1).zfill(3)}_{int(abs_start)}-{int(abs_end)}.mp4"
        output_path = os.path.join(output_folder, output_filename)
        
        # Guardar el subclip con configuración de alta calidad
        print(f"Guardando: {output_path}")
        subclip.write_videofile(
            output_path,
            codec="libx264",           # Codec de video H.264 (alta compatibilidad)
            audio_codec="aac",         # Codec de audio AAC (alta compatibilidad)
            bitrate="8000k",           # Bitrate alto para mantener calidad
            preset="medium",           # Balance entre velocidad y calidad
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            threads=4                  # Usar múltiples núcleos para codificación más rápida
        )
    
    # Cerrar los clips
    action_segment_clip.close()
    original_video.close()
    print("¡Proceso completado!")

if __name__ == "__main__":
    # Ejecutar la función con los parámetros predefinidos
    extract_and_split_video(
        INPUT_VIDEO_PATH, 
        OUTPUT_FOLDER, 
        ACTION_SEGMENT, 
        SEGMENT_DURATION, 
        PREFIX
    )
    
    # Mensaje para indicar que el proceso ha terminado
    print("\n" + "="*50)
    action_duration = ACTION_SEGMENT[1] - ACTION_SEGMENT[0]
    num_clips = int(action_duration // SEGMENT_DURATION)
    if action_duration % SEGMENT_DURATION > 0:
        num_clips += 1
    
    print(f"Se ha completado el procesamiento del video!")
    print(f"Segmento de acción extraído: {ACTION_SEGMENT[0]}s - {ACTION_SEGMENT[1]}s")
    print(f"Se han creado aproximadamente {num_clips} subclips de {SEGMENT_DURATION} segundos")
    print(f"Los clips se han guardado en la carpeta: {OUTPUT_FOLDER}")
    print(f"Prefijo utilizado: {PREFIX}")
    print("="*50)