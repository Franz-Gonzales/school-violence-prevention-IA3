# app/utils/video_utils.py
import cv2
import numpy as np
from typing import List, Tuple

class ProcesadorVideo:
    """Clase para procesar y manipular video frames"""

    def dibujar_bounding_box(
        self,
        frame: np.ndarray,
        bbox: List[float],
        label: str = None,
        color: Tuple[int, int, int] = (0, 255, 0),
        grosor: int = 2
    ) -> np.ndarray:
        """
        Dibuja un bounding box en el frame con una etiqueta opcional
        
        Args:
            frame: Frame de video (numpy array)
            bbox: Coordenadas [x, y, w, h]
            label: Etiqueta a mostrar (opcional)
            color: Color del bounding box (BGR)
            grosor: Grosor de la línea
        
        Returns:
            Frame con el bounding box dibujado
        """
        x, y, w, h = map(int, bbox)
        
        # Dibujar rectángulo
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            color,
            grosor
        )
        
        # Dibujar etiqueta si se proporciona
        if label:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            font_thickness = 1
            text_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
            
            # Fondo de la etiqueta
            cv2.rectangle(
                frame,
                (x, y - text_size[1] - 4),
                (x + text_size[0], y),
                color,
                -1
            )
            
            # Texto de la etiqueta
            cv2.putText(
                frame,
                label,
                (x, y - 2),
                font,
                font_scale,
                (255, 255, 255),  # Color blanco para el texto
                font_thickness,
                cv2.LINE_AA
            )
        
        return frame

    def agregar_texto_alerta(
        self,
        frame: np.ndarray,
        texto: str,
        color: Tuple[int, int, int] = (0, 0, 255),
        tamano: float = 1.0,
        posicion: Tuple[int, int] = (10, 30)
    ) -> np.ndarray:
        """
        Agrega texto de alerta en el frame
        
        Args:
            frame: Frame de video
            texto: Texto a mostrar
            color: Color del texto (BGR)
            tamano: Escala del texto
            posicion: Posición (x, y) del texto
        
        Returns:
            Frame con el texto dibujado
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(
            frame,
            texto,
            posicion,
            font,
            tamano,
            color,
            2,
            cv2.LINE_AA
        )
        return frame


