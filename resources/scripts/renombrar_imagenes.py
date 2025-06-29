import os
import shutil
import random

# Configuración: Define aquí las rutas de las carpetas
INPUT_FOLDER = r"C:\GONZALES\dataset_violencia\imagenes_YOLO11"
OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\imagenes_yolo"
PREFIX = "people_"  # Prefijo para los nuevos nombres de archivos
# Cantidad de imágenes a seleccionar aleatoriamente (si es None, selecciona todas en orden aleatorio)
NUM_RANDOM_IMAGES = None  # Cambia esto a un número entero si quieres limitar la cantidad

def random_rename_images():
    """Selecciona aleatoriamente imágenes, las renombra y las copia a la carpeta de salida."""
    # Crear la carpeta de salida si no existe
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    # Obtener la lista de archivos de imagen en la carpeta
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp']
    image_files = [f for f in os.listdir(INPUT_FOLDER) 
                if os.path.isfile(os.path.join(INPUT_FOLDER, f)) and 
                os.path.splitext(f)[1].lower() in image_extensions]
    
    # Seleccionar aleatoriamente las imágenes
    if NUM_RANDOM_IMAGES and NUM_RANDOM_IMAGES < len(image_files):
        selected_images = random.sample(image_files, NUM_RANDOM_IMAGES)
        print(f"Seleccionadas {NUM_RANDOM_IMAGES} imágenes aleatorias de un total de {len(image_files)}")
    else:
        selected_images = image_files.copy()
        random.shuffle(selected_images)  # Mezclar aleatoriamente todas las imágenes
        print(f"Todas las imágenes ({len(image_files)}) han sido seleccionadas en orden aleatorio")
    
    # Contador para los archivos procesados
    processed_count = 0

    
    # Procesar cada imagen seleccionada
    # for i, filename in enumerate(selected_images, start=5001):
    for i, filename in enumerate(selected_images, start=1):
        input_path = os.path.join(INPUT_FOLDER, filename)
        
        # Crear un nuevo nombre para la imagen
        file_ext = os.path.splitext(filename)[1]
        new_filename = f"{PREFIX}{i:03d}{file_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, new_filename)
        
        try:
            # Copiar la imagen con el nuevo nombre
            shutil.copy2(input_path, output_path)
            
            print(f"Renombrada: {filename} -> {new_filename}")
            processed_count += 1
            
        except Exception as e:
            print(f"Error al procesar {filename}: {e}")
    
    print(f"\nProceso completado. {processed_count} imágenes seleccionadas aleatoriamente, renombradas y guardadas en {OUTPUT_FOLDER}")

if __name__ == "__main__":
    # Verificar que la carpeta de entrada existe
    if not os.path.exists(INPUT_FOLDER):
        print(f"Error: La carpeta de entrada '{INPUT_FOLDER}' no existe.")
    else:
        random_rename_images()