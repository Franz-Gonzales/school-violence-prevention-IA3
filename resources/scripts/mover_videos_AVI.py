import shutil
import os

def move_avi_files():
    # Configuración de rutas (modifica estas variables según tus necesidades)
    source_dir = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_procesar\no_violence"  # Ruta de la carpeta origen con videos
    dest_dir = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_procesar\procesados"   # Ruta de la carpeta destino para archivos .avi

    # Variables para conteo
    avi_count = 0
    mp4_count = 0
    moved_files = 0

    # Validación de directorio fuente
    if not os.path.isdir(source_dir):
        print(f"Error: El directorio fuente '{source_dir}' no existe.")
        return

    # Creación de directorio destino si no existe
    os.makedirs(dest_dir, exist_ok=True)

    print(f"Procesando archivos en: {source_dir}")
    print(f"Moviendo .avi a: {dest_dir}\n")

    # Recorremos todos los archivos en el directorio fuente
    for entry in os.scandir(source_dir):
        if entry.is_file():
            file_ext = os.path.splitext(entry.name)[1].lower()
            
            if file_ext == '.avi':
                avi_count += 1
                try:
                    shutil.move(entry.path, dest_dir)
                    moved_files += 1
                    print(f"Moved: {entry.name}")
                except Exception as e:
                    print(f"Error moving {entry.name}: {str(e)}")
            elif file_ext == '.mp4':
                mp4_count += 1

    # Resultados finales
    print("\n--- Resumen del proceso ---")
    print(f"Total archivos .mp4 encontrados: {mp4_count}")
    print(f"Total archivos .avi encontrados: {avi_count}")
    print(f"Archivos .avi movidos con éxito: {moved_files}")
    print(f"Archivos .avi no movidos: {avi_count - moved_files}")

if __name__ == "__main__":
    move_avi_files()