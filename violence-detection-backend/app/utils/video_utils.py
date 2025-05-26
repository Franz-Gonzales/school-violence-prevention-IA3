"""
Utilidades para procesamiento de video
"""
import cv2
import numpy as np
from typing import Tuple, List, Optional
from pathlib import Path
import asyncio
from datetime import datetime
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class ProcesadorVideo:
    """Clase para procesar video"""
    
    @staticmethod
    def redimensionar_frame(
        frame: np.ndarray, 
        tamano: Tuple[int, int]
    ) -> np.ndarray:
        """Redimensiona un frame al tamaño especificado"""
        return cv2.resize(frame, tamano, interpolation=cv2.INTER_LINEAR)
    
    @staticmethod
    def frame_a_bytes(frame: np.ndarray, formato: str = '.jpg') -> bytes:
        """Convierte un frame a bytes"""
        _, buffer = cv2.imencode(formato, frame)
        return buffer.tobytes()
    
    @staticmethod
    def dibujar_bounding_box(
        frame: np.ndarray,
        bbox: List[float],
        id_persona: int,
        color: Tuple[int, int, int] = (0, 255, 0),
        grosor: int = 2
    ) -> np.ndarray:
        """Dibuja un bounding box en el frame"""
        x, y, w, h = [int(coord) for coord in bbox]
        
        # Dibujar rectángulo
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, grosor)
        
        # Agregar ID
        texto = f"ID: {id_persona}"
        cv2.putText(
            frame, 
            texto, 
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )
        
        return frame
    
    @staticmethod
    def agregar_texto_alerta(
        frame: np.ndarray,
        texto: str,
        posicion: Tuple[int, int] = (50, 50),
        color: Tuple[int, int, int] = (0, 0, 255),
        tamano: float = 1.0
    ) -> np.ndarray:
        """Agrega texto de alerta al frame"""
        cv2.putText(
            frame,
            texto,
            posicion,
            cv2.FONT_HERSHEY_SIMPLEX,
            tamano,
            color,
            2,
            cv2.LINE_AA
        )
        return frame
    
    @staticmethod
    async def guardar_clip_video(
        frames: List[np.ndarray],
        ruta_salida: Path,
        fps: int = 15,
        codec: str = 'mp4v'
    ) -> bool:
        """Guarda una lista de frames como video"""
        try:
            if not frames:
                logger.error("No hay frames para guardar")
                print("No hay frames para guardar")
                return False
            
            # Obtener dimensiones del primer frame
            altura, ancho = frames[0].shape[:2]
            
            # Crear escritor de video
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(
                str(ruta_salida),
                fourcc,
                fps,
                (ancho, altura)
            )
            
            # Escribir frames
            for frame in frames:
                out.write(frame)
            
            out.release()
            logger.info(f"Clip guardado en: {ruta_salida}")
            print(f"Clip guardado en: {ruta_salida}")
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar clip: {e}")
            print(f"Error al guardar clip: {e}")
            return False
    
    @staticmethod
    def extraer_thumbnail(
        frames: List[np.ndarray],
        indice: int = 0
    ) -> Optional[np.ndarray]:
        """Extrae un thumbnail de una lista de frames"""
        if not frames or indice >= len(frames):
            return None
        
        return frames[indice]