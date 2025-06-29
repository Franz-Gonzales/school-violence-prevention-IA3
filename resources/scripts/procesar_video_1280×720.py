import os
from moviepy.editor import VideoFileClip

# PARÁMETROS PREDEFINIDOS - MODIFICA ESTOS VALORES
INPUT_PATH = r"C:\GONZALES\dataset_violencia\videos\videos_nuevos\videos_input.mp4"  # Ruta al video de entrada
OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\videos\videos_procesados"  # Carpeta donde se guardará el video procesado
START_TIME = 8  # Tiempo de inicio para el recorte (en segundos)
END_TIME = 13  # Tiempo de fin para el recorte (en segundos)
TARGET_RESOLUTION = (1280, 720)  # Resolución objetivo (ancho, alto)

def process_video(input_path, output_folder, start_time, end_time, target_resolution=(1280, 720)):
    """
    Procesa un video recortándolo por un rango de tiempo específico y ajustando su resolución.
    
    Args:
        input_path (str): Ruta al video de entrada
        output_folder (str): Carpeta donde se guardará el video procesado
        start_time (float): Tiempo de inicio para el recorte (en segundos)
        end_time (float): Tiempo de fin para el recorte (en segundos)
        target_resolution (tuple): Resolución objetivo en formato (ancho, alto)
    
    Returns:
        str: Ruta del archivo de salida procesado
    """
    # Verificar si el archivo de entrada existe
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"El archivo de video no existe: {input_path}")
    
    # Crear la carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta de salida creada: {output_folder}")
    
    # Obtener el nombre base del archivo de entrada sin extensión
    base_name = os.path.basename(input_path)
    file_name, file_ext = os.path.splitext(base_name)
    
    # Generar el nombre del archivo de salida
    output_name = f"{file_name}_recortado_{start_time}-{end_time}_1280x720{file_ext}"
    output_path = os.path.join(output_folder, output_name)
    
    try:
        # Cargar el video
        print(f"Cargando video: {input_path}")
        video = VideoFileClip(input_path)
        
        # Obtener información del video original
        original_duration = video.duration
        original_size = video.size
        print(f"Información del video original:")
        print(f"- Duración: {original_duration:.2f} segundos")
        print(f"- Resolución: {original_size[0]}x{original_size[1]}")
        
        # Validar tiempos de recorte
        if start_time < 0 or end_time > original_duration or start_time >= end_time:
            raise ValueError(f"Tiempos de recorte inválidos: {start_time}s - {end_time}s. " +
                            f"El video tiene una duración de {original_duration:.2f}s")
        
        # Recortar el video dentro del rango especificado
        print(f"Recortando video del segundo {start_time} al {end_time}")
        video_trimmed = video.subclip(start_time, end_time)
        
        # Redimensionar el video si es necesario
        if original_size[0] != target_resolution[0] or original_size[1] != target_resolution[1]:
            print(f"Redimensionando video de {original_size[0]}x{original_size[1]} a {target_resolution[0]}x{target_resolution[1]}")
            # Usar redimensionamiento compatible con moviepy 1.0.3 y Pillow 6.2.2
            video_processed = video_trimmed.resize(target_resolution)
        else:
            print("El video ya tiene la resolución objetivo. No es necesario redimensionar.")
            video_processed = video_trimmed
        
        # Guardar el video procesado con alta calidad
        print(f"Guardando video procesado: {output_path}")
        
        # Configurar parámetros de codificación para mantener buena calidad
        video_processed.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            bitrate="8000k",
            preset="slow",  # Mejor calidad
            threads=4,
            fps=video.fps,  # Mantener la misma tasa de fotogramas
            temp_audiofile="temp-audio.m4a",
            remove_temp=True
        )
        
        # Obtener información del video procesado
        print(f"Video procesado guardado exitosamente:")
        print(f"- Duración: {end_time - start_time:.2f} segundos")
        print(f"- Resolución: {target_resolution[0]}x{target_resolution[1]}")
        
        # Limpiar
        video.close()
        video_processed.close()
        
        return output_path
    
    except Exception as e:
        print(f"Error al procesar el video: {str(e)}")
        # Asegurar que los recursos se liberen en caso de error
        try:
            video.close()
        except:
            pass
        try:
            video_processed.close()
        except:
            pass
        raise

# Punto de entrada principal del script
if __name__ == "__main__":
    print("=" * 50)
    print("PROCESADOR DE VIDEO: RECORTE Y REDIMENSIONAMIENTO")
    print("=" * 50)
    print(f"Video de entrada: {INPUT_PATH}")
    print(f"Carpeta de salida: {OUTPUT_FOLDER}")
    print(f"Rango de recorte: {START_TIME}s - {END_TIME}s")
    print(f"Resolución objetivo: {TARGET_RESOLUTION[0]}x{TARGET_RESOLUTION[1]}")
    print("=" * 50)
    
    try:
        # Ejecutar procesamiento con los parámetros predefinidos
        result = process_video(INPUT_PATH, OUTPUT_FOLDER, START_TIME, END_TIME, TARGET_RESOLUTION)
        print("\n" + "=" * 50)
        print(f"PROCESO COMPLETADO EXITOSAMENTE")
        print(f"Video procesado guardado en: {result}")
        print("=" * 50)
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"ERROR: {str(e)}")
        print("=" * 50)