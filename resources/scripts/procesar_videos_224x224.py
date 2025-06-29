import os
import sys
import subprocess
import cv2
import concurrent.futures
import shutil
import tempfile
import logging
from tqdm import tqdm
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("video_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Configuración fija
INPUT_DIR = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_aumentation\ambiguos"
OUTPUT_DIR = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_semicompletos\ambiguo"
TARGET_SIZE = (224, 224)  # 224x224
TARGET_FPS = 15
NUM_WORKERS = 4

def get_video_info(video_path):
    """Obtiene información del video: resolución, fps, duración."""
    try:
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            raise ValueError(f"No se pudo abrir el video: {video_path}")
            
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        video.release()
        return {
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": frame_count,
            "duration": duration
        }
    except Exception as e:
        logger.error(f"Error al obtener información del video {video_path}: {str(e)}")
        return None

def create_ffmpeg_command(input_path, output_path, target_size=TARGET_SIZE, target_fps=TARGET_FPS):
    """Crea el comando de FFmpeg para procesar el video."""
    info = get_video_info(input_path)
    if not info:
        return None
    
    original_width, original_height = info["width"], info["height"]
    aspect_ratio = original_width / original_height
    
    if aspect_ratio > 1:  # Más ancho que alto
        new_width = target_size[0]
        new_height = int(new_width / aspect_ratio)
        pad_x = 0
        pad_y = (target_size[1] - new_height) // 2
    else:  # Más alto que ancho o cuadrado
        new_height = target_size[1]
        new_width = int(new_height * aspect_ratio)
        pad_y = 0
        pad_x = (target_size[0] - new_width) // 2
    
    new_width = min(new_width, target_size[0])
    new_height = min(new_height, target_size[1])
    
    command = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264',        # Códec H.264
        '-preset', 'slow',        # Balance calidad/velocidad
        '-crf', '1',             # Alta calidad
        '-r', str(target_fps),    # FPS objetivo
        '-vf', f'scale={new_width}:{new_height}:force_original_aspect_ratio=decrease,'
            f'pad={target_size[0]}:{target_size[1]}:{pad_x}:{pad_y}:color=black',
        '-pix_fmt', 'yuv420p',    # Formato de píxel estándar
        '-movflags', '+faststart',# Optimización para streaming
        '-an',                    # Sin audio (TimeSformer no lo usa)
        '-y',                     # Sobrescribir salida
        output_path
    ]
    
    return command

def process_video(video_path, output_dir, target_size=TARGET_SIZE, target_fps=TARGET_FPS):
    """Procesa un solo video para TimeSformer."""
    video_name = os.path.basename(video_path)
    output_path = os.path.join(output_dir, video_name)
    
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        temp_output = temp_file.name
    
    try:
        command = create_ffmpeg_command(video_path, temp_output, target_size, target_fps)
        if not command:
            logger.error(f"No se pudo crear comando FFmpeg para {video_path}")
            return False
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error al procesar {video_path}: {result.stderr}")
            return False
        
        output_info = get_video_info(temp_output)
        if not output_info:
            logger.error(f"El video de salida {temp_output} no es válido")
            return False
        
        shutil.move(temp_output, output_path)
        
        logger.info(f"Video procesado: {video_name}")
        logger.info(f"  Dimensión original: {get_video_info(video_path)['width']}x{get_video_info(video_path)['height']}")
        logger.info(f"  Dimensión nueva: {output_info['width']}x{output_info['height']}")
        logger.info(f"  FPS original: {get_video_info(video_path)['fps']}")
        logger.info(f"  FPS nuevo: {output_info['fps']}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error inesperado al procesar {video_path}: {str(e)}")
        if os.path.exists(temp_output):
            os.unlink(temp_output)
        return False

def process_videos(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR, target_size=TARGET_SIZE, target_fps=TARGET_FPS, num_workers=NUM_WORKERS):
    """Procesa todos los videos en un directorio en paralelo."""
    os.makedirs(output_dir, exist_ok=True)
    
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    video_files = [
        os.path.join(input_dir, f) for f in os.listdir(input_dir)
        if os.path.isfile(os.path.join(input_dir, f)) and 
        os.path.splitext(f)[1].lower() in video_extensions
    ]
    
    if not video_files:
        logger.warning(f"No se encontraron videos en {input_dir}")
        return
    
    logger.info(f"Encontrados {len(video_files)} videos para procesar")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(
                process_video, 
                video_path, 
                output_dir, 
                target_size, 
                target_fps
            ): video_path for video_path in video_files
        }
        
        success_count = 0
        failed_videos = []
        
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Procesando videos"):
            video_path = futures[future]
            video_name = os.path.basename(video_path)
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    failed_videos.append(video_name)
            except Exception as e:
                logger.error(f"Error en el procesamiento de {video_name}: {str(e)}")
                failed_videos.append(video_name)
    
    logger.info(f"Procesamiento completado: {success_count} de {len(video_files)} videos procesados correctamente")
    if failed_videos:
        logger.warning(f"Videos con errores ({len(failed_videos)}): {', '.join(failed_videos)}")
    
    verify_processed_videos(output_dir, target_size, target_fps)

def verify_processed_videos(output_dir, target_size=TARGET_SIZE, target_fps=TARGET_FPS):
    """Verifica que los videos procesados cumplan con los requisitos."""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    video_files = [
        os.path.join(output_dir, f) for f in os.listdir(output_dir)
        if os.path.isfile(os.path.join(output_dir, f)) and 
        os.path.splitext(f)[1].lower() in video_extensions
    ]
    
    issues_found = 0
    
    for video_path in video_files:
        video_name = os.path.basename(video_path)
        info = get_video_info(video_path)
        
        if not info:
            logger.warning(f"No se pudo verificar {video_name}")
            issues_found += 1
            continue
        
        if info["width"] != target_size[0] or info["height"] != target_size[1]:
            logger.warning(f"Dimensiones incorrectas en {video_name}: {info['width']}x{info['height']}")
            issues_found += 1
        
        if abs(info["fps"] - target_fps) > 0.1:
            logger.warning(f"FPS incorrectos en {video_name}: {info['fps']}")
            issues_found += 1
    
    if issues_found == 0:
        logger.info(f"Verificación completada: Todos los videos cumplen con los requisitos de TimeSformer")
    else:
        logger.warning(f"Verificación completada: Se encontraron {issues_found} problemas")

def check_ffmpeg():
    """Verifica si FFmpeg está instalado."""
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def main():
    """Ejecuta el preprocesamiento de videos con configuración fija."""
    if not check_ffmpeg():
        logger.error("FFmpeg no está instalado o no se encuentra en el PATH. Por favor, instala FFmpeg.")
        sys.exit(1)
    
    logger.info("Iniciando preprocesamiento de videos para TimeSformer")
    logger.info(f"Carpeta de entrada: {INPUT_DIR}")
    logger.info(f"Carpeta de salida: {OUTPUT_DIR}")
    logger.info(f"Tamaño objetivo: {TARGET_SIZE}")
    logger.info(f"FPS objetivo: {TARGET_FPS}")
    logger.info(f"Trabajadores paralelos: {NUM_WORKERS}")
    
    process_videos()

if __name__ == "__main__":
    main()