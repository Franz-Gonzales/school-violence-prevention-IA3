import cv2
import numpy as np
from typing import List, Tuple
from app.config import configuracion

class TimesFormerProcessor:
    """Procesador de frames para el modelo TimesFormer ONNX"""
    
    def __init__(self):
        self.config = configuracion.TIMESFORMER_CONFIG
        self.frame_cache = {}  # Caché para frames preprocesados
        self.cache_hits = 0
        self.cache_misses = 0
        
    def resize_and_pad(self, frame: np.ndarray) -> Tuple[np.ndarray, Tuple[float, float]]:
        """Redimensiona y añade padding manteniendo el aspect ratio"""
        target_size = self.config["input_size"]
        height, width = frame.shape[:2]
        
        scale = min(target_size/width, target_size/height)
        new_size = (int(width * scale), int(height * scale))
        
        resized = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)  # Usar INTER_AREA para reducción
        
        pad_h = (target_size - new_size[1]) // 2
        pad_w = (target_size - new_size[0]) // 2
        
        padded = np.zeros((target_size, target_size, 3), dtype=np.uint8)  # Usar uint8 inicialmente
        padded[pad_h:pad_h + new_size[1], pad_w:pad_w + new_size[0]] = resized
        
        return padded, (scale, scale)
    
    def normalize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Normaliza un frame usando mean y std"""
        frame = frame.astype(np.float32) / 255.0
        mean = np.array(self.config["mean"])
        std = np.array(self.config["std"])
        frame = (frame - mean) / std
        return frame
    
    def preprocess_frames(self, frames: List[np.ndarray]) -> np.ndarray:
        """Preprocesa una lista de frames para TimesFormer"""
        if len(frames) != self.config["num_frames"]:
            print(f"Error: Se requieren {self.config['num_frames']} frames, recibidos {len(frames)}")
            raise ValueError(f"Se requieren {self.config['num_frames']} frames")
        
        processed_frames = []
        for frame in frames:  # Removed enumerate here
            try:
                # Convertir frame a array de bytes para hash
                frame_bytes = frame.tobytes()
                frame_hash = hash(frame_bytes)
                
                if frame_hash in self.frame_cache:
                    processed_frames.append(self.frame_cache[frame_hash])
                    self.cache_hits += 1
                else:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_padded, _ = self.resize_and_pad(frame_rgb)
                    frame_normalized = self.normalize_frame(frame_padded)
                    processed_frames.append(frame_normalized)
                    self.frame_cache[frame_hash] = frame_normalized
                    self.cache_misses += 1
                    
                    # Limitar tamaño de caché
                    if len(self.frame_cache) > 100:
                        self.frame_cache.pop(next(iter(self.frame_cache)))
                        
            except Exception as e:
                print(f"Error procesando frame: {str(e)}")
                raise

        batch = np.stack(processed_frames, axis=0)  # [T, H, W, C]
        batch = batch.transpose(3, 0, 1, 2)  # [C, T, H, W]
        batch = np.expand_dims(batch, axis=0)  # [B, C, T, H, W]
        
        return batch.astype(np.float16)