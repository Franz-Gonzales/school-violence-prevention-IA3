import os
import sys
from pathlib import Path
import numpy as np
import argparse
from PIL import Image, ImageEnhance
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import cv2

# Configuración por defecto (puedes modificar estos valores)
INPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_V2\images_yolo_process"
OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_V2\images_people"
MAX_WORKERS = 8  # Número de hilos para procesamiento en paralelo

def enhance_image_quality(img):
    """
    Aplica técnicas avanzadas para mejorar la calidad y nitidez de la imagen.
    
    Args:
        img: Imagen PIL
    
    Returns:
        Imagen PIL mejorada
    """
    # Convertir a array de OpenCV para operaciones avanzadas
    cv_img = np.array(img)
    cv_img = cv_img[:, :, ::-1].copy()  # RGB a BGR para OpenCV
    
    # Aplicar filtro de nitidez adaptativo
    # Este método protege las áreas lisas mientras aumenta la nitidez en los bordes
    sigma = 0.3
    blur = cv2.GaussianBlur(cv_img, (0, 0), sigma)
    enhanced = cv2.addWeighted(cv_img, 1.5, blur, -0.5, 0)
    
    # Realzar bordes con detector Laplaciano
    kernel_size = 3
    laplacian = cv2.Laplacian(cv_img, cv2.CV_64F, ksize=kernel_size)
    laplacian = cv2.convertScaleAbs(laplacian)
    
    # Ponderación para control de intensidad del realce
    edge_weight = 0.2
    enhanced = cv2.addWeighted(enhanced, 1.0, laplacian, edge_weight, 0)
    
    # Aplicar reducción de ruido preservando bordes
    enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 5, 5, 7, 21)
    
    # Convertir de vuelta a PIL para operaciones adicionales
    enhanced_pil = Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))
    
    # Mejoras adicionales con PIL
    # Ajuste de nitidez
    enhancer = ImageEnhance.Sharpness(enhanced_pil)
    enhanced_pil = enhancer.enhance(1.3)
    
    # Ajuste de contraste para mejor definición
    enhancer = ImageEnhance.Contrast(enhanced_pil)
    enhanced_pil = enhancer.enhance(1.1)
    
    # Ajuste sutíl de saturación
    enhancer = ImageEnhance.Color(enhanced_pil)
    enhanced_pil = enhancer.enhance(1.05)
    
    return enhanced_pil

def resize_with_padding(img, target_size=(640, 640)):
    """
    Redimensiona la imagen manteniendo la relación de aspecto y añadiendo padding.
    
    Args:
        img: Imagen PIL a redimensionar
        target_size: Tamaño objetivo (ancho, alto)
    
    Returns:
        Imagen PIL redimensionada con padding
    """
    # Obtener dimensiones originales
    width, height = img.size
    
    # Calcular relación de aspecto
    aspect = width / height
    
    # Calcular dimensiones para mantener relación de aspecto
    if width > height:
        # Imagen horizontal
        new_width = target_size[0]
        new_height = int(new_width / aspect)
    else:
        # Imagen vertical
        new_height = target_size[1]
        new_width = int(new_height * aspect)
    
    # Comprobar si necesitamos usar método de crecimiento para imágenes pequeñas
    if width < target_size[0] and height < target_size[1]:
        # Para imágenes muy pequeñas, usamos un algoritmo superior para el crecimiento
        resized = img.resize((new_width, new_height), Image.LANCZOS)
    else:
        # Para reducir tamaño, LANCZOS es la mejor opción para preservar detalles
        resized = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Crear imagen de destino con fondo negro
    result = Image.new("RGB", target_size, color=(0, 0, 0))
    
    # Calcular posición para centrar la imagen redimensionada
    paste_x = (target_size[0] - new_width) // 2
    paste_y = (target_size[1] - new_height) // 2
    
    # Pegar la imagen redimensionada centrada
    result.paste(resized, (paste_x, paste_y))
    
    return result

def process_image(input_path, output_path):
    """
    Procesa una imagen: la redimensiona a 640x640 y mejora su calidad.
    
    Args:
        input_path: Ruta de la imagen de entrada
        output_path: Ruta donde guardar la imagen procesada
    
    Returns:
        bool: True si el procesamiento fue exitoso
    """
    try:
        # Abrir imagen con PIL
        with Image.open(input_path) as img:
            # Convertir a RGB si es necesario (por ejemplo, si es RGBA)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionar con padding para mantener relación de aspecto
            resized = resize_with_padding(img, (640, 640))
            
            # Mejorar calidad y nitidez
            enhanced = enhance_image_quality(resized)
            
            # Guardar con alta calidad
            enhanced.save(output_path, format='JPEG', quality=95, 
                        optimize=True, subsampling=0)
        
        return True
    except Exception as e:
        print(f"Error procesando {input_path}: {e}")
        return False

def process_folder(input_folder, output_folder, max_workers=MAX_WORKERS):
    """
    Procesa todas las imágenes en una carpeta.
    
    Args:
        input_folder: Carpeta con imágenes originales
        output_folder: Carpeta para guardar imágenes procesadas
        max_workers: Número máximo de hilos para procesamiento paralelo
    
    Returns:
        int: Número de imágenes procesadas correctamente
    """
    # Asegurar que la carpeta de salida exista
    os.makedirs(output_folder, exist_ok=True)
    
    # Listar imágenes en la carpeta de entrada
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    input_files = [f for f in os.listdir(input_folder) 
                  if os.path.isfile(os.path.join(input_folder, f)) 
                  and f.lower().endswith(image_extensions)]
    
    if not input_files:
        print(f"No se encontraron imágenes en {input_folder}")
        return 0
    
    print(f"Encontradas {len(input_files)} imágenes para procesar")
    
    # Preparar rutas de entrada y salida
    tasks = []
    for filename in input_files:
        input_path = os.path.join(input_folder, filename)
        
        # Mantener la extensión original o convertir a .jpg
        output_filename = filename
        if not output_filename.lower().endswith('.jpg'):
            output_filename = os.path.splitext(filename)[0] + '.jpg'
        
        output_path = os.path.join(output_folder, output_filename)
        tasks.append((input_path, output_path))
    
    # Procesar imágenes en paralelo con barra de progreso
    success_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(
            executor.map(lambda args: process_image(*args), tasks),
            total=len(tasks),
            desc="Procesando imágenes"
        ))
        
        success_count = sum(1 for r in results if r)
    
    return success_count

def main():
    """Función principal para ejecutar el script desde línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Redimensiona imágenes a 640x640 para YOLOv12 preservando calidad.'
    )
    parser.add_argument('--input', '-i', type=str, default=INPUT_FOLDER,
                        help=f'Carpeta de entrada con imágenes (default: {INPUT_FOLDER})')
    parser.add_argument('--output', '-o', type=str, default=OUTPUT_FOLDER,
                        help=f'Carpeta de salida para imágenes procesadas (default: {OUTPUT_FOLDER})')
    parser.add_argument('--workers', '-w', type=int, default=MAX_WORKERS,
                        help=f'Número de hilos para procesamiento paralelo (default: {MAX_WORKERS})')
    
    args = parser.parse_args()
    
    print("=== REDIMENSIONAMIENTO DE IMÁGENES PARA YOLOv12 ===")
    print(f"Carpeta de entrada: {args.input}")
    print(f"Carpeta de salida: {args.output}")
    print(f"Trabajadores en paralelo: {args.workers}")
    print("================================================")
    
    # Verificar bibliotecas necesarias
    try:
        from PIL import __version__ as pil_version
        cv2_version = cv2.__version__
        print(f"Usando PIL versión: {pil_version}")
        print(f"Usando OpenCV versión: {cv2_version}")
    except:
        print("Error: Faltan dependencias.")
        print("Instale las dependencias necesarias con:")
        print("pip install pillow opencv-python tqdm")
        return 1
    
    # Procesar las imágenes
    try:
        processed = process_folder(args.input, args.output, args.workers)
        
        print("\n=== RESUMEN DE PROCESAMIENTO ===")
        print(f"Total de imágenes procesadas: {processed}")
        print(f"Las imágenes han sido guardadas en: {args.output}")
        print("===============================")
        
        if processed > 0:
            # Mostrar algunas estadísticas de las imágenes procesadas
            sample_path = next(Path(args.output).glob('*.jpg'), None)
            if sample_path:
                with Image.open(sample_path) as img:
                    print(f"Ejemplo de imagen procesada: {sample_path.name}")
                    print(f"Dimensiones: {img.size[0]}x{img.size[1]} px")
        
        return 0
    except Exception as e:
        print(f"Error durante el procesamiento: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())