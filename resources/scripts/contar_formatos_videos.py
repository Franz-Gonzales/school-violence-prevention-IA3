import os

def count_video_files(source_dir):
    # Definir los formatos de video a contar
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    # Diccionario para almacenar los recuentos
    video_counts = {ext: 0 for ext in video_extensions}
    total_videos = 0

    # Validación de directorio fuente
    if not os.path.isdir(source_dir):
        print(f"Error: El directorio '{source_dir}' no existe.")
        return

    print(f"Contando archivos en: {source_dir}\n")

    # Recorremos todos los archivos en el directorio fuente
    for entry in os.scandir(source_dir):
        if entry.is_file():
            file_ext = os.path.splitext(entry.name)[1].lower()
            if file_ext in video_extensions:
                video_counts[file_ext] += 1
                total_videos += 1

    # Resultados finales
    print("--- Resumen del conteo de archivos de video ---")
    for ext, count in video_counts.items():
        print(f"Total archivos {ext}: {count}")
    print(f"Total general de archivos de video: {total_videos}")

# Ruta de la carpeta a analizar (modifica esta variable según tus necesidades)
source_dir = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_procesar\no_violence"

# Ejecutar la función
count_video_files(source_dir)