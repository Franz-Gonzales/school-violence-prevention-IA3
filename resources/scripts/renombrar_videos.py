import os
import random
import shutil
from tqdm import tqdm

# Parámetros predefinidos
INPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\videos_procesados\violencia_directa"  # Carpeta de entrada con videos de violencia
OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\videos_completados\violencia_directa"  # Carpeta de salida
ACTION = "copy"  # Opciones: "copy" (copiar) o "move" (mover)
PREFIX = "violencia_directa"  # Prefijo para renombrar (cambiar a "no_violence" manualmente si necesitas)

def process_videos(input_folder, output_folder, prefix="violence", action="copy"):
    """
    Procesa videos de una carpeta de entrada, los renombra con un prefijo (ej. violence_XXX),
    y los copia/mueve aleatoriamente a una carpeta de salida.
    
    Args:
        input_folder (str): Ruta a la carpeta con los videos originales
        output_folder (str): Ruta a la carpeta de salida
        prefix (str): Prefijo para los nuevos nombres (ej. 'violence' o 'no_violence')
        action (str): "copy" para copiar, "move" para mover
    """
    # Validar acción
    if action not in ["copy", "move"]:
        raise ValueError("ACTION debe ser 'copy' o 'move'")
    action_func = shutil.copy2 if action == "copy" else shutil.move

    # Crear la carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta de salida creada: {output_folder}")

    # Obtener lista de videos
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
    videos = []
    
    if os.path.exists(input_folder):
        for file in os.listdir(input_folder):
            file_path = os.path.join(input_folder, file)
            if os.path.isfile(file_path) and os.path.splitext(file)[1].lower() in video_extensions:
                videos.append(file_path)
    else:
        print(f"¡Error! La carpeta de entrada no existe: {input_folder}")
        return

    # Estadísticas iniciales
    total_videos = len(videos)
    print(f"Total de videos encontrados: {total_videos}")
    if total_videos == 0:
        print("No se encontraron videos. Verifica la carpeta de entrada.")
        return

    # Mezclar aleatoriamente
    random.shuffle(videos)

    # Procesar videos
    print(f"\nProcesando videos con prefijo '{prefix}'...")
    for i, video_path in enumerate(tqdm(videos)):
        new_name = f"{prefix}_{str(i+1).zfill(3)}{os.path.splitext(video_path)[1]}"
        dest_path = os.path.join(output_folder, new_name)
        action_func(video_path, dest_path)

    # Estadísticas finales
    print("\n¡Proceso completado!")
    print(f"Total de videos procesados: {total_videos}")
    print(f"- Videos con prefijo '{prefix}': {total_videos}")

if __name__ == "__main__":
    print("=== INICIANDO PROCESAMIENTO DE VIDEOS ===")
    print(f"Carpeta de entrada: {INPUT_FOLDER}")
    print(f"Carpeta de salida: {OUTPUT_FOLDER}")
    print(f"Acción: {ACTION}")
    print(f"Prefijo: {PREFIX}")
    print("========================================")
    
    # Ejecutar la función principal
    process_videos(INPUT_FOLDER, OUTPUT_FOLDER, PREFIX, ACTION)