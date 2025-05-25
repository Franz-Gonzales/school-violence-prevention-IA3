"""
Pipeline completo de procesamiento de IA
"""
import cv2
import numpy as np
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque
from app.ai.yolo_detector import DetectorPersonas
from app.ai.deep_sort_tracker import TrackerPersonas
from app.ai.violence_detector import DetectorViolencia
from app.services.alarm_service import ServicioAlarma
from app.services.notification_service import ServicioNotificaciones
from app.services.incident_service import ServicioIncidentes
from app.utils.video_utils import ProcesadorVideo
from app.utils.logger import obtener_logger
from app.config import configuracion
from app.models.incident import TipoIncidente, SeveridadIncidente  # Importar los Enum

logger = obtener_logger(__name__)


class PipelineDeteccion:
    """Pipeline completo de detección de violencia"""
    
    def __init__(
        self,
        detector_personas: DetectorPersonas,
        tracker_personas: TrackerPersonas,
        detector_violencia: DetectorViolencia,
        servicio_alarma: ServicioAlarma,
        servicio_notificaciones: ServicioNotificaciones,
        servicio_incidentes: ServicioIncidentes
    ):
        self.detector_personas = detector_personas
        self.tracker_personas = tracker_personas
        self.detector_violencia = detector_violencia
        self.servicio_alarma = servicio_alarma
        self.servicio_notificaciones = servicio_notificaciones
        self.servicio_incidentes = servicio_incidentes
        
        # Procesador de video
        self.procesador_video = ProcesadorVideo()
        
        # Estado del pipeline
        self.activo = False
        self.camara_id = None
        self.ubicacion = None
        
        # Buffer para clips de evidencia
        self.buffer_evidencia = deque(maxlen=configuracion.DEFAULT_FPS * configuracion.CLIP_DURATION)
        self.grabando_evidencia = False
        self.frames_evidencia = []
        
        # Contadores y estadísticas
        self.frames_procesados = 0
        self.incidentes_detectados = 0
        
    async def procesar_frame(
        self,
        frame: np.ndarray,
        camara_id: int,
        ubicacion: str
    ) -> Dict[str, Any]:
        """
        Procesa un frame a través del pipeline completo
        
        Returns:
            Diccionario con resultados del procesamiento
        """
        self.camara_id = camara_id
        self.ubicacion = ubicacion
        self.frames_procesados += 1
        
        resultado = {
            'frame_procesado': None,
            'personas_detectadas': [],
            'violencia_detectada': False,
            'probabilidad_violencia': 0.0,
            'incidente_creado': False,
            'alarma_activada': False
        }
        
        try:
            # 1. Detección de personas con YOLO
            detecciones, frame_procesado = self.detector_personas.detectar_con_procesamiento(frame)
            
            # 2. Tracking con DeepSORT
            personas_rastreadas = self.tracker_personas.actualizar(frame, detecciones)
            resultado['personas_detectadas'] = personas_rastreadas
            
            # 3. Dibujar bounding boxes con IDs
            for persona in personas_rastreadas:
                frame_procesado = self.procesador_video.dibujar_bounding_box(
                    frame_procesado,
                    persona['bbox'],
                    persona['id'],
                    color=(0, 255, 0)
                )
            
            # 4. Agregar frame al detector de violencia
            self.detector_violencia.agregar_frame(frame)
            
            # 5. Agregar frame al buffer de evidencia
            self.buffer_evidencia.append(frame_procesado.copy())
            
            # 6. Detectar violencia cada N frames
            if self.frames_procesados % 8 == 0:  # Cada 8 frames
                deteccion_violencia = self.detector_violencia.detectar()
                resultado['violencia_detectada'] = deteccion_violencia['violencia_detectada']
                resultado['probabilidad_violencia'] = deteccion_violencia['probabilidad']
                
                # Si se detecta violencia
                if deteccion_violencia['violencia_detectada']:
                    logger.warning(f"Violencia detectada en cámara {camara_id}")
                    
                    # Agregar alerta visual al frame
                    frame_procesado = self.procesador_video.agregar_texto_alerta(
                        frame_procesado,
                        f"ALERTA: VIOLENCIA DETECTADA ({deteccion_violencia['probabilidad']:.2%})",
                        posicion=(50, 50),
                        color=(0, 0, 255),
                        tamano=1.2
                    )
                    
                    # Iniciar grabación de evidencia si no está activa
                    if not self.grabando_evidencia:
                        self.grabando_evidencia = True
                        self.frames_evidencia = list(self.buffer_evidencia)
                        
                        # Ejecutar acciones en paralelo
                        await asyncio.gather(
                            self._activar_alarma(),
                            self._enviar_notificaciones(personas_rastreadas),
                            self._crear_incidente(personas_rastreadas, deteccion_violencia['probabilidad'])
                        )
                        
                        resultado['incidente_creado'] = True
                        resultado['alarma_activada'] = True
                
                # Si estamos grabando evidencia
                elif self.grabando_evidencia:
                    self.frames_evidencia.append(frame_procesado.copy())
                    
                    # Si han pasado suficientes frames sin violencia, detener grabación
                    if len(self.frames_evidencia) >= configuracion.DEFAULT_FPS * configuracion.CLIP_DURATION:
                        await self._guardar_evidencia()
                        self.grabando_evidencia = False
                        self.frames_evidencia = []
            
            resultado['frame_procesado'] = frame_procesado
            
        except Exception as e:
            logger.error(f"Error en pipeline de procesamiento: {e}")
        
        return resultado
    
    async def _activar_alarma(self):
        """Activa la alarma Tuya"""
        try:
            await self.servicio_alarma.activar_alarma(duracion=10)
        except Exception as e:
            logger.error(f"Error al activar alarma: {e}")
    
    async def _enviar_notificaciones(self, personas_involucradas: List[Dict[str, Any]]):
        """Envía notificaciones del incidente"""
        try:
            num_personas = len(personas_involucradas)
            await self.servicio_notificaciones.enviar_notificacion_violencia(
                camara_id=self.camara_id,
                ubicacion=self.ubicacion,
                num_personas=num_personas
            )
        except Exception as e:
            logger.error(f"Error al enviar notificaciones: {e}")
    
    async def _crear_incidente(
        self,
        personas_involucradas: List[Dict[str, Any]],
        probabilidad: float
    ):
        """Crea un registro de incidente"""
        try:
            ids_personas = [str(p['id']) for p in personas_involucradas]
            
            incidente_data = {
                'camara_id': self.camara_id,
                'tipo_incidente': TipoIncidente.VIOLENCIA_FISICA,  # Usar Enum
                'severidad': self._calcular_severidad(probabilidad),  # Usar Enum
                'probabilidad_violencia': probabilidad,
                'fecha_hora_inicio': datetime.now(),
                'ubicacion': self.ubicacion,
                'numero_personas_involucradas': len(personas_involucradas),
                'ids_personas_detectadas': ids_personas
            }
            
            await self.servicio_incidentes.crear_incidente(incidente_data)
            self.incidentes_detectados += 1
            
        except Exception as e:
            logger.error(f"Error al crear incidente: {e}")
    
    async def _guardar_evidencia(self):
        """Guarda el clip de video de evidencia"""
        try:
            if not self.frames_evidencia:
                return
            
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"evidencia_camara{self.camara_id}_{timestamp}.mp4"
            ruta_evidencia = configuracion.VIDEO_EVIDENCE_PATH / "clips" / nombre_archivo
            
            # Guardar video
            await self.procesador_video.guardar_clip_video(
                self.frames_evidencia,
                ruta_evidencia,
                fps=configuracion.DEFAULT_FPS
            )
            
            logger.info(f"Evidencia guardada: {ruta_evidencia}")
            
        except Exception as e:
            logger.error(f"Error al guardar evidencia: {e}")
    
    def _calcular_severidad(self, probabilidad: float) -> SeveridadIncidente:
        """Calcula la severidad del incidente basada en la probabilidad"""
        if probabilidad >= 0.9:
            return SeveridadIncidente.CRITICA
        elif probabilidad >= 0.8:
            return SeveridadIncidente.ALTA
        elif probabilidad >= 0.7:
            return SeveridadIncidente.MEDIA
        else:
            return SeveridadIncidente.BAJA
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del pipeline"""
        return {
            'frames_procesados': self.frames_procesados,
            'incidentes_detectados': self.incidentes_detectados,
            'personas_rastreadas': len(self.tracker_personas.tracker.tracker.tracks),
            'violencia_activa': self.detector_violencia.violencia_detectada,
            'probabilidad_actual': self.detector_violencia.probabilidad_violencia
        }
    
    def reiniciar(self):
        """Reinicia el pipeline"""
        self.tracker_personas.reiniciar()
        self.detector_violencia.reiniciar()
        self.buffer_evidencia.clear()
        self.frames_evidencia = []
        self.grabando_evidencia = False
        self.frames_procesados = 0
        logger.info("Pipeline reiniciado")