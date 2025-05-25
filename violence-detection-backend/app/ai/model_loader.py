"""
Cargador de modelos de IA
"""
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Union
from ultralytics import YOLO
from transformers import AutoImageProcessor, TimesformerForVideoClassification
from app.config import configuracion
from app.utils.logger import obtener_logger


logger = obtener_logger(__name__)


class CargadorModelos:
    """Clase para cargar y gestionar modelos de IA"""
    
    def __init__(self):
        self.device = self._configurar_dispositivo()
        self.modelos = {}
        self.procesadores = {}
        
    def _configurar_dispositivo(self) -> str:
        """Configura el dispositivo (GPU/CPU)"""
        if configuracion.USE_GPU and torch.cuda.is_available():
            device = f"cuda:{configuracion.GPU_DEVICE}"
            logger.info(f"Usando GPU: {torch.cuda.get_device_name(configuracion.GPU_DEVICE)}")
        else:
            device = "cpu"
            logger.warning("GPU no disponible, usando CPU")
        
        return device
    
    def cargar_yolo(self, ruta_modelo: Optional[Path] = None) -> YOLO:
        """Carga el modelo YOLO para detección de personas"""
        try:
            if ruta_modelo is None:
                ruta_modelo = configuracion.obtener_ruta_modelo(configuracion.YOLO_MODEL)
            
            logger.info(f"Cargando modelo YOLO desde: {ruta_modelo}")
            
            # Cargar modelo
            modelo = YOLO(str(ruta_modelo))
            modelo.to(self.device)
            
            # Configurar para solo detectar personas (clase 0)
            modelo.model.names = {0: 'persona'}
            
            self.modelos['yolo'] = modelo
            logger.info("Modelo YOLO cargado exitosamente")
            
            return modelo
            
        except Exception as e:
            logger.error(f"Error al cargar modelo YOLO: {e}")
            raise
    
    def cargar_timesformer(
        self, 
        ruta_modelo: Optional[Path] = None,
        ruta_procesador: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Carga el modelo TimesFormer para detección de violencia"""
        try:
            if ruta_modelo is None:
                ruta_modelo = configuracion.obtener_ruta_modelo(configuracion.TIMESFORMER_MODEL)
            
            if ruta_procesador is None:
                ruta_procesador = Path(configuracion.PROCESSOR_PATH)
            
            logger.info(f"Cargando modelo TimesFormer desde: {ruta_modelo}")
            
            # Determinar tipo de modelo
            if str(ruta_modelo).endswith('.pt'):
                if 'scripted' in str(ruta_modelo):
                    # Modelo TorchScript
                    modelo = torch.jit.load(ruta_modelo, map_location=self.device)
                    modelo.eval()
                    tipo_modelo = 'torchscript'
                else:
                    # Modelo PyTorch estándar
                    checkpoint = torch.load(ruta_modelo, map_location=self.device)
                    
                    # Crear modelo desde configuración
                    modelo = TimesformerForVideoClassification.from_pretrained(
                        "facebook/timesformer-base-finetuned-k400",
                        num_labels=2,
                        num_frames=8,
                        ignore_mismatched_sizes=True
                    )
                    
                    # Cargar pesos
                    modelo.load_state_dict(checkpoint['model_state_dict'])
                    modelo.to(self.device)
                    modelo.eval()
                    tipo_modelo = 'pytorch'
            else:
                raise ValueError(f"Formato de modelo no soportado: {ruta_modelo}")
            
            # Cargar procesador
            procesador = None
            if ruta_procesador.exists():
                procesador = AutoImageProcessor.from_pretrained(str(ruta_procesador))
            
            resultado = {
                'modelo': modelo,
                'tipo': tipo_modelo,
                'procesador': procesador,
                'config': {
                    'num_frames': 8,
                    'image_size': 224,
                    'threshold': configuracion.VIOLENCE_THRESHOLD
                }
            }
            
            self.modelos['timesformer'] = resultado
            logger.info(f"Modelo TimesFormer cargado exitosamente (tipo: {tipo_modelo})")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error al cargar modelo TimesFormer: {e}")
            raise
    
    def cargar_todos_los_modelos(self):
        """Carga todos los modelos necesarios"""
        logger.info("Cargando todos los modelos...")
        
        # Cargar YOLO
        self.cargar_yolo()
        
        # Cargar TimesFormer
        self.cargar_timesformer()
        
        logger.info("Todos los modelos cargados exitosamente")
    
    def obtener_modelo(self, nombre: str) -> Any:
        """Obtiene un modelo cargado"""
        if nombre not in self.modelos:
            raise ValueError(f"Modelo '{nombre}' no está cargado")
        
        return self.modelos[nombre]
    
    def liberar_memoria(self):
        """Libera memoria de GPU"""
        if self.device.startswith('cuda'):
            torch.cuda.empty_cache()
            logger.info("Memoria GPU liberada")


# Instancia global del cargador
cargador_modelos = CargadorModelos()