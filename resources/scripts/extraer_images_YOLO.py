import os
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

def extract_frames_from_video(video_path, output_folder, num_frames=3, prefix=None):
    """
    Extrae un número específico de frames equidistantes de un video con calidad estándar.
    
    Args:
        video_path (str): Ruta al archivo de video
        output_folder (str): Carpeta donde se guardarán los frames
        num_frames (int): Número de frames a extraer
        prefix (str): Prefijo opcional para los archivos de imagen generados
    
    Returns:
        list: Rutas de los frames extraídos
    """
    # Abrir el video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: No se pudo abrir el video {video_path}")
        return []
    
    # Obtener información del video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if total_frames <= 0 or fps <= 0:
        print(f"Error: No se pudo leer la información del video {video_path}")
        cap.release()
        return []
    
    # Determinar los índices de los frames a extraer
    if total_frames < num_frames:
        # Si hay menos frames que los solicitados, tomar todos
        frame_indices = list(range(total_frames))
    else:
        # Distribuir equitativamente los frames a lo largo del video
        frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
    
    # Preparar nombre base para los archivos de salida
    video_filename = os.path.splitext(os.path.basename(video_path))[0]
    if prefix:
        video_filename = f"{prefix}_{video_filename}"
    
    # Extraer los frames seleccionados
    extracted_frames = []
    for i, frame_idx in enumerate(frame_indices):
        # Posicionar en el frame correcto
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            print(f"Error: No se pudo leer el frame {frame_idx} del video {video_path}")
            continue
        
        # Crear nombre de archivo para el frame - ahora usando JPG
        frame_filename = f"{video_filename}_frame_{i+1:03d}.jpg"
        frame_path = os.path.join(output_folder, frame_filename)
        
        # Aplicar una leve mejora de nitidez (opcional - mantiene calidad visual pero con archivos más pequeños)
        kernel = np.array([[-0.5, -1, -0.5], [-1, 7, -1], [-0.5, -1, -0.5]]) / 3.0
        frame = cv2.filter2D(frame, -1, kernel)
        
        # Guardar el frame en formato JPG con calidad estándar (90%)
        # Equilibrio entre buena calidad visual y tamaño de archivo razonable
        cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        extracted_frames.append(frame_path)
    
    # Liberar recursos
    cap.release()
    
    return extracted_frames

def process_videos_in_folder(input_folder, output_folder, num_frames=3, max_workers=4):
    """
    Procesa todos los videos en una carpeta y extrae frames de cada uno.
    
    Args:
        input_folder (str): Carpeta que contiene los videos
        output_folder (str): Carpeta donde se guardarán los frames
        num_frames (int): Número de frames a extraer de cada video
        max_workers (int): Número máximo de hilos para procesamiento paralelo
    
    Returns:
        int: Número total de frames extraídos
    """
    # Asegurar que la carpeta de salida exista
    os.makedirs(output_folder, exist_ok=True)
    
    # Obtener lista de videos en la carpeta de entrada
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')
    videos = [f for f in os.listdir(input_folder) 
              if os.path.isfile(os.path.join(input_folder, f)) 
              and f.lower().endswith(video_extensions)]
    
    if not videos:
        print(f"No se encontraron videos en {input_folder}")
        return 0
    
    print(f"Encontrados {len(videos)} videos para procesar")
    
    # Procesar videos en paralelo para mejorar rendimiento
    frames_extracted = 0
    
    # Función para procesar un solo video
    def process_video(video):
        video_path = os.path.join(input_folder, video)
        extracted = extract_frames_from_video(video_path, output_folder, num_frames)
        return len(extracted)
    
    # Procesar videos con una barra de progreso
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map the function to the videos and wrap with tqdm for progress
        results = list(tqdm(
            executor.map(process_video, videos),
            total=len(videos),
            desc="Procesando videos"
        ))
        
        frames_extracted = sum(results)
    
    return frames_extracted

if __name__ == "__main__":
    # Configuración de rutas y parámetros
    INPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_V2\videos_procesados\no_violence"
    OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_V2\images_yolo_process"
    NUM_FRAMES = 3  # Número de frames a extraer por video
    MAX_WORKERS = 4  # Número de hilos para procesamiento paralelo
    
    print("=== EXTRACCIÓN DE FRAMES DE VIDEOS ===")
    print(f"Carpeta de entrada: {INPUT_FOLDER}")
    print(f"Carpeta de salida: {OUTPUT_FOLDER}")
    print(f"Frames por video: {NUM_FRAMES}")
    print("=====================================")
    
    # Verificar que OpenCV esté correctamente instalado
    try:
        cv2_version = cv2.__version__
        print(f"Usando OpenCV versión: {cv2_version}")
    except:
        print("Error: OpenCV no está instalado correctamente.")
        print("Instale OpenCV con: pip install opencv-python")
        exit(1)
    
    # Procesar los videos
    total_frames = process_videos_in_folder(
        INPUT_FOLDER, 
        OUTPUT_FOLDER, 
        NUM_FRAMES,
        MAX_WORKERS
    )
    
    # Mostrar estadísticas sobre los archivos generados
    if total_frames > 0:
        # Calcular tamaño promedio de los frames
        total_size = 0
        frame_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.lower().endswith('.jpg')]
        for frame_file in frame_files:
            filepath = os.path.join(OUTPUT_FOLDER, frame_file)
            total_size += os.path.getsize(filepath)
        
        avg_size = total_size / len(frame_files) / 1024  # en KB
        print(f"Tamaño promedio por frame: {avg_size:.2f} KB")
    
    print("\n=== RESUMEN DE EXTRACCIÓN ===")
    print(f"Total de frames extraídos: {total_frames}")
    print(f"Los frames han sido guardados en: {OUTPUT_FOLDER}")
    print("==============================")