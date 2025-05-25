"""
Tareas asíncronas para procesamiento de video
"""
import asyncio
from pathlib import Path
from typing import Optional
from celery import Celery
from app.config import configuracion
from app.utils.logger import obtener_logger
from app.utils.video_utils import ProcesadorVideo
import cv2

logger = obtener_logger(__name__)

# Configurar Celery (opcional, puedes usar asyncio en su lugar)
# celery_app = Celery('video_tasks', broker=configuracion.REDIS_URL)


async def procesar_video_diferido(
    video_path: Path,
    output_path: Path,
    agregar_marcas: bool = True
) -> bool:
    """
    Procesa un video de manera diferida (para re-procesamiento)
    
    Args:
        video_path: Ruta del video original
        output_path: Ruta de salida
        agregar_marcas: Si debe agregar marcas de tiempo
        
    Returns:
        True si se procesó correctamente
    """
    try:
        cap = cv2.VideoCapture(str(video_path))
        
        # Obtener propiedades del video
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Crear escritor de video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Agregar marcas si es necesario
            if agregar_marcas:
                timestamp_text = f"Frame: {frame_count}"
                cv2.putText(
                    frame,
                    timestamp_text,
                    (10, height - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
            
            out.write(frame)
            frame_count += 1
            
            # Yield control para no bloquear
            if frame_count % 30 == 0:
                await asyncio.sleep(0)
        
        cap.release()
        out.release()
        
        logger.info(f"Video procesado: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error procesando video: {e}")
        return False


async def generar_thumbnail_video(
    video_path: Path,
    output_path: Path,
    frame_position: float = 0.5
) -> bool:
    """
    Genera un thumbnail de un video
    
    Args:
        video_path: Ruta del video
        output_path: Ruta de salida para el thumbnail
        frame_position: Posición relativa del frame (0.0 a 1.0)
        
    Returns:
        True si se generó correctamente
    """
    try:
        cap = cv2.VideoCapture(str(video_path))
        
        # Obtener frame en la posición especificada
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        target_frame = int(total_frames * frame_position)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        
        if ret:
            # Redimensionar si es necesario
            thumbnail = cv2.resize(frame, (320, 180))
            cv2.imwrite(str(output_path), thumbnail)
            logger.info(f"Thumbnail generado: {output_path}")
            
        cap.release()
        return ret
        
    except Exception as e:
        logger.error(f"Error generando thumbnail: {e}")
        return False


async def comprimir_video_evidencia(
    video_path: Path,
    calidad: str = "media"
) -> Optional[Path]:
    """
    Comprime un video de evidencia para almacenamiento
    
    Args:
        video_path: Ruta del video original
        calidad: "baja", "media", "alta"
        
    Returns:
        Ruta del video comprimido o None si falla
    """
    try:
        # Configuración de compresión según calidad
        calidades = {
            "baja": {"bitrate": "500k", "scale": 0.5},
            "media": {"bitrate": "1000k", "scale": 0.75},
            "alta": {"bitrate": "2000k", "scale": 1.0}
        }
        
        config = calidades.get(calidad, calidades["media"])
        
        # Generar nombre de salida
        output_path = video_path.parent / f"{video_path.stem}_compressed{video_path.suffix}"
        
        # Usar ffmpeg para comprimir (requiere ffmpeg instalado)
        import subprocess
        
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-b:v', config["bitrate"],
            '-vf', f"scale=iw*{config['scale']}:ih*{config['scale']}",
            '-y',  # Sobrescribir si existe
            str(output_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        await process.wait()
        
        if process.returncode == 0:
            logger.info(f"Video comprimido: {output_path}")
            return output_path
        else:
            logger.error("Error en compresión de video")
            return None
            
    except Exception as e:
        logger.error(f"Error comprimiendo video: {e}")
        return None


async def extraer_clips_por_tiempo(
    video_path: Path,
    tiempos: list,
    duracion_clip: int = 5
) -> list:
    """
    Extrae clips específicos de un video basado en marcas de tiempo
    
    Args:
        video_path: Ruta del video
        tiempos: Lista de tiempos en segundos donde extraer clips
        duracion_clip: Duración de cada clip en segundos
        
    Returns:
        Lista de rutas de clips generados
    """
    clips_generados = []
    
    try:
        for idx, tiempo_inicio in enumerate(tiempos):
            output_path = video_path.parent / f"{video_path.stem}_clip_{idx}.mp4"
            
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-ss', str(tiempo_inicio),
                '-t', str(duracion_clip),
                '-c', 'copy',
                '-y',
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            await process.wait()
            
            if process.returncode == 0:
                clips_generados.append(output_path)
                logger.info(f"Clip extraído: {output_path}")
            
    except Exception as e:
        logger.error(f"Error extrayendo clips: {e}")
    
    return clips_generados