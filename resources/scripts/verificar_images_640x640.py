from PIL import Image
import os

def check_image_resolution(folder_path, target_width=640, target_height=640):
    non_compliant_images = []
    
    # Recorrer todos los archivos en la carpeta
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # Verificar si el archivo es una imagen
        if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    # Verificar si la resolución no coincide con la objetivo
                    if width != target_width or height != target_height:
                        non_compliant_images.append((filename, width, height))
            except Exception as e:
                print(f"Error al procesar {filename}: {e}")

    # Resultados
    if non_compliant_images:
        print("\n--- Imágenes que NO cumplen con la resolución 640x640 ---")
        for img_info in non_compliant_images:
            print(f"Imagen: {img_info[0]}, Resolución: {img_info[1]}x{img_info[2]}")
    else:
        print("\n¡Todas las imágenes cumplen con la resolución 640x640!")

    print(f"\nTotal de imágenes verificadas: {len(os.listdir(folder_path))}")
    print(f"Imágenes no compliantes: {len(non_compliant_images)}")

# Ruta de la carpeta con las imágenes (modifica esta variable)
folder_path = r"C:\GONZALES\dataset_violencia\dataset_people\images\val"

# Ejecutar la verificación
check_image_resolution(folder_path)