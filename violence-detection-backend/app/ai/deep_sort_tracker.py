"""
Tracker de personas usando DeepSORT
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from deep_sort_realtime.deepsort_tracker import DeepSort
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class TrackerPersonas:
    """Tracker de personas basado en DeepSORT"""
    
    def __init__(self):
        self.tracker = DeepSort(
            max_age=30,
            n_init=3,
            nms_max_overlap=1.0,
            max_cosine_distance=0.3,
            nn_budget=None,
            override_track_class=None,
            embedder="mobilenet",
            half=True,
            bgr=True,
            embedder_gpu=True,
            embedder_model_name=None,
            embedder_wts=None,
            polygon=False,
            today=None
        )
        
    def actualizar(
        self, 
        frame: np.ndarray,
        detecciones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Actualiza el tracker con nuevas detecciones
        
        Args:
            frame: Frame actual
            detecciones: Lista de detecciones de YOLO
            
        Returns:
            Lista de tracks con IDs asignados
        """
        try:
            if not detecciones:
                # Actualizar tracker sin detecciones
                self.tracker.update_tracks([], frame=frame)
                return []
            
            # Convertir detecciones al formato DeepSORT
            detecciones_deepsort = []
            for det in detecciones:
                bbox = det['bbox']  # [x, y, w, h]
                # DeepSORT espera [x1, y1, w, h]
                deteccion_ds = ([bbox[0], bbox[1], bbox[2], bbox[3]], det['confianza'], 'persona')
                detecciones_deepsort.append(deteccion_ds)
            
            # Actualizar tracks
            tracks = self.tracker.update_tracks(detecciones_deepsort, frame=frame)
            # Convertir tracks al formato de salida
            personas_rastreadas = []
            for track in tracks:
                if not track.is_confirmed():
                    continue
                
                track_id = track.track_id
                ltrb = track.to_ltrb()
                
                # Convertir a formato [x, y, w, h]
                bbox = [
                    float(ltrb[0]),
                    float(ltrb[1]),
                    float(ltrb[2] - ltrb[0]),
                    float(ltrb[3] - ltrb[1])
                ]
                
                persona = {
                    'id': track_id,
                    'bbox': bbox,
                    'clase': 'persona',
                    'edad_track': track.age,
                    'estado': 'confirmado'
                }
                
                personas_rastreadas.append(persona)
            
            return personas_rastreadas
            
        except Exception as e:
            logger.error(f"Error en actualización de tracker: {e}")
            return []
    
    def reiniciar(self):
        """Reinicia el tracker"""
        self.tracker.tracker.tracks = []
        self.tracker.tracker._next_id = 1
        logger.info("Tracker reiniciado")