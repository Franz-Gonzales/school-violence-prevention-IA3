import os
import random
from PIL import Image, ImageEnhance

# Configuración: Define aquí las rutas de las carpetas
INPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_V2\images_yolo_process"
OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_V2\images_people"
PREFIX = "mejoradas_"  # Prefijo para los nuevos nombres de archivos

def enhance_image(img):
    """Mejora la calidad de la imagen aplicando varios filtros."""
    # Aumentar la nitidez
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(5.0)  # Factor de nitidez (2.0 = más nítido)
    
    # Mejorar el contraste
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1)  # Factor de contraste
    
    # Ajustar el brillo
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1)  # Factor de brillo
    
    return img

def process_images():
    """Procesa todas las imágenes en la carpeta de entrada y las guarda en la carpeta de salida."""
    # Crear la carpeta de salida si no existe
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    # Obtener la lista de archivos de imagen en la carpeta
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = [f for f in os.listdir(INPUT_FOLDER) 
                if os.path.isfile(os.path.join(INPUT_FOLDER, f)) and 
                os.path.splitext(f)[1].lower() in image_extensions]
    
    # 🔀 Mezclar aleatoriamente la lista de imágenes
    random.shuffle(image_files)

    # Procesar cada imagen
    for i, filename in enumerate(image_files, start=5001):
        input_path = os.path.join(INPUT_FOLDER, filename)
        
        # Crear un nuevo nombre para la imagen
        file_ext = os.path.splitext(filename)[1]
        new_filename = f"{PREFIX}{i:03d}{file_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, new_filename)
        
        try:
            # Abrir la imagen
            with Image.open(input_path) as img:
                # Mejorar la calidad
                enhanced_img = enhance_image(img)
                
                # Guardar la imagen mejorada con mayor calidad
                enhanced_img.save(output_path, quality=95)
                
            print(f"Procesada: {filename} -> {new_filename}")
        except Exception as e:
            print(f"Error al procesar {filename}: {e}")
    
    print(f"\nProceso completado. {len(image_files)} imágenes mejoradas y guardadas en {OUTPUT_FOLDER}")

if __name__ == "__main__":
    # Verificar que la carpeta de entrada existe
    if not os.path.exists(INPUT_FOLDER):
        print(f"Error: La carpeta de entrada '{INPUT_FOLDER}' no existe.")
    else:
        process_images()