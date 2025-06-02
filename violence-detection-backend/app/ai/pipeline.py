import cv2
import numpy as np
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque
from app.ai.yolo_detector import DetectorPersonas
from app.ai.violence_detector import DetectorViolencia
from app.services.alarm_service import ServicioAlarma
from app.services.notification_service import ServicioNotificaciones
from app.services.incident_service import ServicioIncidentes
from app.models.incident import TipoIncidente, SeveridadIncidente, EstadoIncidente
from app.utils.video_utils import ProcesadorVideo
from app.utils.logger import obtener_logger
from app.config import configuracion
from sqlalchemy.ext.asyncio import AsyncSession
import os

logger = obtener_logger(__name__)

class PipelineDeteccion:
    def __init__(
        self,
        detector_personas: DetectorPersonas,
        detector_violencia: DetectorViolencia,
        servicio_alarma: ServicioAlarma,
        servicio_notificaciones: ServicioNotificaciones,
        servicio_incidentes: ServicioIncidentes,
        session: AsyncSession
    ):
        self.detector_personas = detector_personas
        self.detector_violencia = detector_violencia
        self.servicio_alarma = servicio_alarma
        self.servicio_notificaciones = servicio_notificaciones
        self.servicio_incidentes = servicio_incidentes
        self.session = session
        
        self.procesador_video = ProcesadorVideo()
        self.activo = False
        self.camara_id = None
        self.ubicacion = None
        
        self.buffer_evidencia = deque(maxlen=configuracion.DEFAULT_FPS * configuracion.CLIP_DURATION)
        self.grabando_evidencia = False
        self.frames_evidencia = []
        
        self.frames_procesados = 0
        self.incidentes_detectados = 0

    async def procesar_frame(self, frame: np.ndarray, camara_id: int, ubicacion: str) -> Dict[str, Any]:
        try:
            self.camara_id = camara_id
            self.ubicacion = ubicacion
            self.frames_procesados += 1
            
            # Detección de personas con YOLO
            detecciones, frame_procesado = self.detector_personas.detectar_con_procesamiento(frame)
            
            # Dibujar bounding boxes
            for deteccion in detecciones:
                frame_procesado = self.procesador_video.dibujar_bounding_box(
                    frame_procesado,
                    deteccion['bbox'],
                    label=f"Persona ({deteccion['confianza']:.2f})"
                )

            resultado = {
                'frame_procesado': frame_procesado,
                'personas_detectadas': detecciones,
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0
            }

            # Solo procesar con TimeSformer si hay personas detectadas
            if detecciones:
                self.detector_violencia.agregar_frame(frame_procesado.copy())
                
                if self.frames_procesados % configuracion.TIMESFORMER_CONFIG["num_frames"] == 0:
                    deteccion = self.detector_violencia.detectar()
                    resultado.update(deteccion)

                    if deteccion['violencia_detectada']:
                        await self._activar_alarma()
                        
                        frame_procesado = self.procesador_video.agregar_texto_alerta(
                            frame_procesado,
                            f"¡ALERTA! Violencia detectada ({deteccion['probabilidad']:.1%})",
                            color=(0, 0, 255),
                            tamano=1.2
                        )
                        
                        resultado['frame_procesado'] = frame_procesado
                        
                        if not self.grabando_evidencia:
                            self.grabando_evidencia = True
                            self.frames_evidencia = list(self.buffer_evidencia)
                            await self._crear_incidente(detecciones, deteccion['probabilidad'])
                        
                        if self.grabando_evidencia:
                            self.frames_evidencia.append(frame_procesado)
                    else:
                        if self.grabando_evidencia:
                            self.grabando_evidencia = False
                            await self._guardar_evidencia()
                            self.frames_evidencia.clear()

            self.buffer_evidencia.append(frame_procesado.copy())
            
            return resultado

        except Exception as e:
            print(f"Error en pipeline: {str(e)}")
            return {
                'frame_procesado': frame,
                'personas_detectadas': [],
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0
            }

    async def _activar_alarma(self):
        try:
            await self.servicio_alarma.activar_alarma(duracion=5)
        except Exception as e:
            print(f"Error al activar alarma: {e}")

    async def _enviar_notificaciones(self, personas_involucradas: List[Dict[str, Any]]):
        try:
            num_personas = len(personas_involucradas)
            await self.servicio_notificaciones.enviar_notificacion_violencia(
                camara_id=self.camara_id,
                ubicacion=self.ubicacion,
                num_personas=num_personas
            )
        except Exception as e:
            print(f"Error al enviar notificaciones: {e}")

    async def _crear_incidente(self, personas_involucradas: List[Dict[str, Any]], probabilidad: float):
        try:
            if not self.servicio_incidentes:
                print("Servicio de incidentes no inicializado")
                return
                
            incidente_data = {
                'camara_id': self.camara_id,
                'tipo_incidente': TipoIncidente.VIOLENCIA_FISICA,
                'severidad': self._calcular_severidad(probabilidad),
                'probabilidad_violencia': probabilidad,
                'fecha_hora_inicio': datetime.now(),
                'ubicacion': self.ubicacion,
                'numero_personas_involucradas': len(personas_involucradas),
                'ids_personas_detectadas': [],
                'estado': EstadoIncidente.NUEVO,
                'descripcion': f"Violencia detectada con probabilidad {probabilidad:.2%}"
            }
            
            incidente = await self.servicio_incidentes.crear_incidente(incidente_data)
            
            if incidente and hasattr(incidente, 'id'):
                self.incidente_actual_id = incidente.id
                self.incidentes_detectados += 1
                print(f"Nuevo incidente registrado ID: {incidente.id}")

        except Exception as e:
            print(f"Error al crear incidente: {str(e)}")

    async def _guardar_evidencia(self):
        try:
            if not self.frames_evidencia:
                print("No hay frames para guardar evidencia")
                return

            ruta_base = configuracion.VIDEO_EVIDENCE_PATH / "clips"
            ruta_base.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"evidencia_camara{self.camara_id}_{timestamp}.mp4"
            ruta_evidencia = ruta_base / nombre_archivo

            height, width = self.frames_evidencia[0].shape[:2]
            fps = 15

            video_writer = cv2.VideoWriter(
                str(ruta_evidencia),
                cv2.VideoWriter_fourcc(*'avc1'),
                fps,
                (width, height)
            )

            if not video_writer.isOpened():
                raise RuntimeError("No se pudo crear el VideoWriter")

            frames_escritos = 0
            for frame in self.frames_evidencia:
                video_writer.write(frame)
                frames_escritos += 1

            video_writer.release()

            if not ruta_evidencia.exists():
                raise FileNotFoundError(f"No se pudo crear el archivo de video: {ruta_evidencia}")

            tamano_archivo = ruta_evidencia.stat().st_size / (1024 * 1024)
            print(f"Video guardado: {ruta_evidencia} ({tamano_archivo:.2f} MB)")

            if hasattr(self, 'incidente_actual_id') and self.incidente_actual_id:
                await self.servicio_incidentes.actualizar_incidente(
                    self.incidente_actual_id,
                    {
                        'video_evidencia_path': str(ruta_evidencia),
                        'fecha_hora_fin': datetime.now()
                    }
                )
                print(f"Incidente {self.incidente_actual_id} actualizado con video")

            return str(ruta_evidencia)

        except Exception as e:
            print(f"Error al guardar evidencia: {e}")
            return None

    def _calcular_severidad(self, probabilidad: float) -> SeveridadIncidente:
        if probabilidad >= 0.9:
            return SeveridadIncidente.CRITICA
        elif probabilidad >= 0.8:
            return SeveridadIncidente.ALTA
        elif probabilidad >= 0.7:
            return SeveridadIncidente.MEDIA
        else:
            return SeveridadIncidente.BAJA

    def obtener_estadisticas(self) -> Dict[str, Any]:
        return {
            'frames_procesados': self.frames_procesados,
            'incidentes_detectados': self.incidentes_detectados,
            'personas_rastreadas': 0,
            'violencia_activa': self.detector_violencia.violencia_detectada,
            'probabilidad_actual': self.detector_violencia.probabilidad_violencia
        }

    def reiniciar(self):
        self.detector_violencia.reiniciar()
        self.buffer_evidencia.clear()
        self.frames_evidencia = []
        self.grabando_evidencia = False
        self.frames_procesados = 0
        print("Pipeline reiniciado")

