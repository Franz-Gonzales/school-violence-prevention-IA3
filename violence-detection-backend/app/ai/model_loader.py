"""
Cargador de modelos de IA
"""
import torch
import onnxruntime as ort
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Union
from ultralytics import YOLO
from app.config import configuracion
from app.utils.logger import obtener_logger


logger = obtener_logger(__name__)


class CargadorModelos:
    """Clase para cargar y gestionar modelos de IA"""
    
    def __init__(self):
        self.device = self._configurar_dispositivo()
        self.modelos = {}
    
    def _configurar_dispositivo(self) -> str:
        """Configura el dispositivo (GPU/CPU)"""
        if configuracion.USE_GPU and torch.cuda.is_available():
            device = f"cuda:{configuracion.GPU_DEVICE}"
            logger.info(f"Usando GPU: {torch.cuda.get_device_name(configuracion.GPU_DEVICE)}")
            print(f"Usando GPU: {torch.cuda.get_device_name(configuracion.GPU_DEVICE)}")
        else:
            device = "cpu"
            logger.warning("GPU no disponible, usando CPU")
            print("GPU no disponible, usando CPU")
        
        return device
    
    def cargar_yolo(self, ruta_modelo: Optional[Path] = None) -> YOLO:
        """Carga el modelo YOLO para detección de personas"""
        try:
            if ruta_modelo is None:
                ruta_modelo = configuracion.obtener_ruta_modelo(configuracion.YOLO_MODEL)
            
            logger.info(f"Cargando modelo YOLO desde: {ruta_modelo}")
            print(f"Cargando modelo YOLO desde: {ruta_modelo}")
            
            # Cargar modelo
            modelo = YOLO(str(ruta_modelo))
            modelo.to(self.device)
            
            # Configurar para solo detectar personas (clase 0)
            modelo.model.names = {0: 'persona'}
            
            self.modelos['yolo'] = modelo
            logger.info("Modelo YOLO cargado exitosamente")
            print("Modelo YOLO cargado exitosamente")
            
            return modelo
            
        except Exception as e:
            logger.error(f"Error al cargar modelo YOLO: {e}")
            print(f"Error al cargar modelo YOLO: {e}")
            raise
    
    def cargar_timesformer(
        self, 
        ruta_modelo: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Carga el modelo TimesFormer ONNX"""
        try:
            if ruta_modelo is None:
                ruta_modelo = configuracion.obtener_ruta_modelo(configuracion.TIMESFORMER_MODEL)
            
            logger.info(f"Cargando modelo TimesFormer desde: {ruta_modelo}")
            print(f"Cargando modelo TimesFormer desde: {ruta_modelo}")
            
            # Configurar ONNX Runtime
            opciones = ort.SessionOptions()
            opciones.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            opciones.intra_op_num_threads = 4
            
            # Seleccionar provider según disponibilidad de GPU
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] \
                if configuracion.USE_GPU else ['CPUExecutionProvider']
            
            # Cargar modelo ONNX
            modelo = ort.InferenceSession(
                str(ruta_modelo),
                providers=providers,
                sess_options=opciones
            )
            
            resultado = {
                'modelo': modelo,
                'tipo': 'onnx',
                'config': configuracion.TIMESFORMER_CONFIG
            }
            
            self.modelos['timesformer'] = resultado
            logger.info("✅ Modelo TimesFormer ONNX cargado exitosamente")
            print("✅ Modelo TimesFormer ONNX cargado exitosamente")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error al cargar modelo TimesFormer: {e}")
            raise
    
    def cargar_todos_los_modelos(self):
        """Carga todos los modelos necesarios"""
        logger.info("Cargando todos los modelos...")
        print("Cargando todos los modelos...")
        
        try:
            # Cargar YOLO
            yolo = self.cargar_yolo()
            print("✅ Modelo YOLO cargado")
            
            # Cargar TimesFormer
            timesformer = self.cargar_timesformer()
            print("✅ Modelo TimesFormer cargado")
            
            if not yolo or not timesformer:
                raise RuntimeError("Error cargando modelos")
                
            logger.info("✅ Todos los modelos cargados exitosamente")
            print("✅ Todos los modelos cargados exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelos: {e}")
            print(f"❌ Error cargando modelos: {e}")
            raise
    
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
            print("Memoria GPU liberada")


# Instancia global del cargador
cargador_modelos = CargadorModelos()