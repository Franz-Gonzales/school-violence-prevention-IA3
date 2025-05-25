"""
Detector de violencia usando TimesFormer
"""
import cv2
import torch
import numpy as np
from collections import deque
from typing import Dict, List, Tuple, Optional, Any
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class DetectorViolencia:
    """Detector de violencia basado en TimesFormer"""
    
    def __init__(self, modelo_info: Dict[str, Any]):
        self.modelo = modelo_info['modelo']
        self.tipo_modelo = modelo_info['tipo']
        self.procesador = modelo_info.get('procesador')
        self.config = modelo_info['config']
        
        # Configuración
        self.num_frames = self.config['num_frames']
        self.image_size = self.config['image_size']
        self.threshold = self.config['threshold']
        
        # Buffer de frames
        self.buffer_frames = deque(maxlen=self.num_frames)
        
        # Estado
        self.violencia_detectada = False
        self.probabilidad_violencia = 0.0
        self.frames_con_violencia = 0
        self.inicio_violencia = None
        
    def agregar_frame(self, frame: np.ndarray):
        """Agrega un frame al buffer"""
        # Redimensionar frame
        frame_redimensionado = cv2.resize(
            frame,
            (self.image_size, self.image_size),
            interpolation=cv2.INTER_LINEAR
        )
        
        # Convertir a RGB si es necesario
        if len(frame_redimensionado.shape) == 2:
            frame_redimensionado = cv2.cvtColor(frame_redimensionado, cv2.COLOR_GRAY2RGB)
        elif frame_redimensionado.shape[2] == 4:
            frame_redimensionado = cv2.cvtColor(frame_redimensionado, cv2.COLOR_BGRA2RGB)
        else:
            frame_redimensionado = cv2.cvtColor(frame_redimensionado, cv2.COLOR_BGR2RGB)
        
        self.buffer_frames.append(frame_redimensionado)
    
    def _preprocesar_frames(self) -> torch.Tensor:
        """Preprocesa los frames del buffer para el modelo"""
        frames = list(self.buffer_frames)
        
        if self.procesador:
            # Usar procesador de Hugging Face
            inputs = self.procesador(
                frames,
                return_tensors="pt"
            )
            return inputs['pixel_values'].to(configuracion.obtener_configuracion_gpu()['device'])
        else:
            # Preprocesamiento manual
            frames_array = np.array(frames)  # [T, H, W, C]
            
            # Normalizar
            frames_array = frames_array.astype(np.float32) / 255.0
            
            # Reorganizar dimensiones según el tipo de modelo
            if self.tipo_modelo == 'torchscript':
                # [B, C, T, H, W]
                frames_array = np.transpose(frames_array, (3, 0, 1, 2))
                frames_array = np.expand_dims(frames_array, 0)
            else:
                # [B, T, C, H, W] 
                frames_array = np.transpose(frames_array, (0, 3, 1, 2))
                frames_array = np.expand_dims(frames_array, 0)
            
            tensor = torch.from_numpy(frames_array).float()
            return tensor.to(configuracion.obtener_configuracion_gpu()['device'])
    
    def detectar(self) -> Dict[str, Any]:
        """Detecta violencia en los frames del buffer"""
        if len(self.buffer_frames) < self.num_frames:
            return {
                'violencia_detectada': False,
                'probabilidad': 0.0,
                'mensaje': 'Buffer incompleto'
            }
        
        try:
            # Preprocesar frames
            input_tensor = self._preprocesar_frames()
            
            # Inferencia
            with torch.no_grad():
                if self.tipo_modelo == 'pytorch':
                    outputs = self.modelo(pixel_values=input_tensor)
                    logits = outputs.logits
                    probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
                elif self.tipo_modelo == 'torchscript':
                    outputs = self.modelo(input_tensor)
                    probs = outputs.cpu().numpy()[0]
                else:
                    raise ValueError(f"Tipo de modelo no soportado: {self.tipo_modelo}")
            
            # Obtener probabilidad de violencia
            prob_violencia = float(probs[1])
            es_violencia = prob_violencia >= self.threshold
            
            # Actualizar estado
            self.probabilidad_violencia = prob_violencia
            
            if es_violencia:
                self.frames_con_violencia += 1
                if not self.violencia_detectada:
                    self.violencia_detectada = True
                    self.inicio_violencia = len(self.buffer_frames)
                    logger.warning(f"Violencia detectada! Probabilidad: {prob_violencia:.2f}")
            else:
                # Si no hay violencia por varios frames, resetear
                if self.violencia_detectada and self.frames_con_violencia > 0:
                    self.frames_con_violencia -= 1
                    if self.frames_con_violencia == 0:
                        self.violencia_detectada = False
                        self.inicio_violencia = None
            
            return {
                'violencia_detectada': es_violencia,
                'probabilidad': prob_violencia,
                'frames_consecutivos': self.frames_con_violencia,
                'mensaje': 'Detección completada'
            }
            
        except Exception as e:
            logger.error(f"Error en detección de violencia: {e}")
            return {
                'violencia_detectada': False,
                'probabilidad': 0.0,
                'mensaje': f'Error: {str(e)}'
            }
    
    def reiniciar(self):
        """Reinicia el detector"""
        self.buffer_frames.clear()
        self.violencia_detectada = False
        self.probabilidad_violencia = 0.0
        self.frames_con_violencia = 0
        self.inicio_violencia = None