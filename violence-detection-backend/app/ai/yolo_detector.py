"""
Detector de personas usando YOLOv11
"""
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from ultralytics import YOLO
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class DetectorPersonas:
    """Detector de personas basado en YOLOv11"""
    
    def __init__(self, modelo: YOLO):
        self.modelo = modelo
        self.confianza_minima = configuracion.YOLO_CONFIDENCE
        
    def detectar(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detecta personas en un frame
        
        Args:
            frame: Frame de video (numpy array)
            
        Returns:
            Lista de detecciones con formato:
            [{'bbox': [x, y, w, h], 'confianza': float, 'clase': 'persona'}]
        """
        try:
            # Realizar inferencia
            resultados = self.modelo(
                frame,
                conf=self.confianza_minima,
                classes=[0],  # Solo clase persona
                verbose=False
            )
            
            detecciones = []
            
            for resultado in resultados:
                if resultado.boxes is not None:
                    for box in resultado.boxes:
                        # Obtener coordenadas
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Convertir a formato [x, y, w, h]
                        bbox = [
                            float(x1),
                            float(y1),
                            float(x2 - x1),
                            float(y2 - y1)
                        ]
                        
                        deteccion = {
                            'bbox': bbox,
                            'confianza': float(box.conf[0]),
                            'clase': 'persona'
                        }
                        
                        detecciones.append(deteccion)
            
            return detecciones
            
        except Exception as e:
            logger.error(f"Error en detección YOLO: {e}")
            return []
    
    def detectar_con_procesamiento(
        self, 
        frame: np.ndarray,
        redimensionar: bool = True
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """
        Detecta personas con preprocesamiento opcional
        
        Returns:
            Tupla de (detecciones, frame_procesado)
        """
        frame_procesado = frame.copy()
        
        # Redimensionar si es necesario
        if redimensionar:
            altura_original, ancho_original = frame.shape[:2]
            frame_redimensionado = cv2.resize(
                frame, 
                configuracion.PROCESSING_RESOLUTION,
                interpolation=cv2.INTER_LINEAR
            )
            
            # Detectar en frame redimensionado
            detecciones = self.detectar(frame_redimensionado)
            
            # Escalar coordenadas al tamaño original
            escala_x = ancho_original / configuracion.PROCESSING_RESOLUTION[0]
            escala_y = altura_original / configuracion.PROCESSING_RESOLUTION[1]
            
            for deteccion in detecciones:
                bbox = deteccion['bbox']
                bbox[0] *= escala_x  # x
                bbox[1] *= escala_y  # y
                bbox[2] *= escala_x  # width
                bbox[3] *= escala_y  # height
        else:
            detecciones = self.detectar(frame)
        
        return detecciones, frame_procesado