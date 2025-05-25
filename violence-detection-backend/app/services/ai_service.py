"""
Servicio principal de IA que coordina todos los modelos
"""
from typing import Dict, Any, Optional
import asyncio
import cv2
import numpy as np
from app.ai.model_loader import cargador_modelos
from app.ai.pipeline import PipelineDeteccion
from app.ai.yolo_detector import DetectorPersonas
from app.ai.deep_sort_tracker import TrackerPersonas
from app.ai.violence_detector import DetectorViolencia
from app.services.alarm_service import ServicioAlarma
from app.services.notification_service import ServicioNotificaciones
from app.services.incident_service import ServicioIncidentes
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class ServicioIA:
    """Servicio que coordina el procesamiento de IA"""
    
    def __init__(self):
        self.pipelines: Dict[int, PipelineDeteccion] = {}
        self.activo = False
        
    async def inicializar(self, db_session):
        """Inicializa el servicio de IA"""
        try:
            # Cargar modelos si no están cargados
            if not cargador_modelos.modelos:
                logger.info("Cargando modelos de IA...")
                cargador_modelos.cargar_todos_los_modelos()
            
            # Crear servicios necesarios
            self.servicio_alarma = ServicioAlarma()
            self.servicio_notificaciones = ServicioNotificaciones(db_session)
            self.servicio_incidentes = ServicioIncidentes(db_session)
            
            self.activo = True
            logger.info("Servicio de IA inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar servicio IA: {e}")
            self.activo = False
            raise
    
    def crear_pipeline(self, camara_id: int) -> PipelineDeteccion:
        """Crea un pipeline de procesamiento para una cámara"""
        if camara_id in self.pipelines:
            return self.pipelines[camara_id]
        
        # Crear componentes del pipeline
        detector_personas = DetectorPersonas(
            cargador_modelos.obtener_modelo('yolo')
        )
        tracker_personas = TrackerPersonas()
        detector_violencia = DetectorViolencia(
            cargador_modelos.obtener_modelo('timesformer')
        )
        
        # Crear pipeline
        pipeline = PipelineDeteccion(
            detector_personas,
            tracker_personas,
            detector_violencia,
            self.servicio_alarma,
            self.servicio_notificaciones,
            self.servicio_incidentes
        )
        
        self.pipelines[camara_id] = pipeline
        logger.info(f"Pipeline creado para cámara {camara_id}")
        
        return pipeline
    
    async def procesar_frame_camara(
        self,
        camara_id: int,
        frame: np.ndarray,
        ubicacion: str
    ) -> Dict[str, Any]:
        """Procesa un frame de una cámara específica"""
        if not self.activo:
            raise RuntimeError("Servicio de IA no está activo")
        
        # Obtener o crear pipeline
        pipeline = self.crear_pipeline(camara_id)
        
        # Procesar frame
        resultado = await pipeline.procesar_frame(frame, camara_id, ubicacion)
        
        return resultado
    
    def obtener_estadisticas(self, camara_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtiene estadísticas de procesamiento"""
        if camara_id:
            if camara_id in self.pipelines:
                return self.pipelines[camara_id].obtener_estadisticas()
            else:
                return {"error": "Pipeline no encontrado para esta cámara"}
        
        # Estadísticas globales
        estadisticas = {
            "pipelines_activos": len(self.pipelines),
            "servicio_activo": self.activo,
            "camaras": {}
        }
        
        for cam_id, pipeline in self.pipelines.items():
            estadisticas["camaras"][cam_id] = pipeline.obtener_estadisticas()
        
        return estadisticas
    
    def detener_pipeline(self, camara_id: int):
        """Detiene y elimina un pipeline"""
        if camara_id in self.pipelines:
            self.pipelines[camara_id].reiniciar()
            del self.pipelines[camara_id]
            logger.info(f"Pipeline detenido para cámara {camara_id}")
    
    def detener_todos(self):
        """Detiene todos los pipelines"""
        for camara_id in list(self.pipelines.keys()):
            self.detener_pipeline(camara_id)
        
        self.activo = False
        logger.info("Todos los pipelines detenidos")


# Instancia global del servicio
servicio_ia = ServicioIA()