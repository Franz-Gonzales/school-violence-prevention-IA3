import cv2
import numpy as np
from typing import List, Tuple
from app.config import configuracion

class TimesFormerProcessor:
    """Procesador de frames para el modelo TimesFormer ONNX"""
    
    def __init__(self):
        self.config = configuracion.TIMESFORMER_CONFIG
        
    def resize_and_pad(self, frame: np.ndarray) -> Tuple[np.ndarray, Tuple[float, float]]:
        """Redimensiona y añade padding manteniendo el aspect ratio"""
        target_size = self.config["input_size"]
        height, width = frame.shape[:2]
        
        # Calcular escala manteniendo aspect ratio
        scale = min(target_size/width, target_size/height)
        new_size = (int(width * scale), int(height * scale))
        
        # Redimensionar
        resized = cv2.resize(frame, new_size)
        
        # Calcular padding
        pad_h = (target_size - new_size[1]) // 2
        pad_w = (target_size - new_size[0]) // 2
        
        # Crear imagen con padding
        padded = np.zeros((target_size, target_size, 3), dtype=np.float32)
        padded[pad_h:pad_h + new_size[1], pad_w:pad_w + new_size[0]] = resized
        
        return padded, (scale, scale)
    
    def normalize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Normaliza un frame usando mean y std"""
        # Convertir a float32 y escalar a [0,1]
        frame = frame.astype(np.float32) / 255.0
        
        # Normalizar usando mean y std
        mean = np.array(self.config["mean"])
        std = np.array(self.config["std"])
        frame = (frame - mean) / std
        
        return frame
    
    def preprocess_frames(self, frames: List[np.ndarray]) -> np.ndarray:
        """Preprocesa una lista de frames para TimesFormer"""
        if len(frames) != self.config["num_frames"]:
            raise ValueError(f"Se requieren {self.config['num_frames']} frames")
        
        processed_frames = []
        for frame in frames:
            # Convertir BGR a RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Redimensionar y añadir padding
            frame, _ = self.resize_and_pad(frame)
            
            # Normalizar
            frame = self.normalize_frame(frame)
            
            processed_frames.append(frame)
        
        # Apilar frames y reorganizar para ONNX
        # [batch_size=1, channels=3, num_frames=8, height=224, width=224]
        batch = np.stack(processed_frames, axis=0)  # [T, H, W, C]
        batch = batch.transpose(3, 0, 1, 2)  # [C, T, H, W]
        batch = np.expand_dims(batch, axis=0)  # [B, C, T, H, W]
        
        return batch.astype(np.float32)