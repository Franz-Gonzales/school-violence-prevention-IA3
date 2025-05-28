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
from app.models.incident import TipoIncidente, SeveridadIncidente, EstadoIncidente
from app.models.incident import EstadoIncidente
from app.utils.video_utils import ProcesadorVideo
from app.utils.logger import obtener_logger
from app.config import configuracion
from sqlalchemy.ext.asyncio import AsyncSession

import os

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
        servicio_incidentes: ServicioIncidentes,
        session: AsyncSession
    ):
        self.detector_personas = detector_personas
        self.tracker_personas = tracker_personas
        self.detector_violencia = detector_violencia
        self.servicio_alarma = servicio_alarma
        self.servicio_notificaciones = servicio_notificaciones
        self.servicio_incidentes = servicio_incidentes
        self.session = session 
        
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
        
    async def procesar_frame(self, frame: np.ndarray, camara_id: int, ubicacion: str) -> Dict[str, Any]:
        """Procesa un frame a través del pipeline completo"""
        try:
            self.camara_id = camara_id
            self.ubicacion = ubicacion
            self.frames_procesados += 1
            
            # 1. Detección de personas con YOLO
            detecciones, frame_procesado = self.detector_personas.detectar_con_procesamiento(frame)
            
            # 2. Tracking con DeepSORT
            personas_rastreadas = self.tracker_personas.actualizar(frame, detecciones)
            
            # 3. Dibujar bounding boxes
            for persona in personas_rastreadas:
                frame_procesado = self.procesador_video.dibujar_bounding_box(
                    frame_procesado,
                    persona['bbox'],
                    persona['id']
                )

            # 4. Buffer circular para detección de violencia
            self.detector_violencia.agregar_frame(frame_procesado.copy())
            
            resultado = {
                'frame_procesado': frame_procesado,
                'personas_detectadas': personas_rastreadas,
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0
            }

            # Detectar violencia cada N frames
            if self.frames_procesados % configuracion.TIMESFORMER_CONFIG["num_frames"] == 0:
                deteccion = self.detector_violencia.detectar()
                # resultado.update(deteccion)
                resultado = {**resultado, **deteccion}

                if deteccion['violencia_detectada']:
                    
                    # Activar alarma - Agregamos esta línea
                    await self._activar_alarma()
                    
                    # Agregar alerta visual
                    frame_procesado = self.procesador_video.agregar_texto_alerta(
                        frame_procesado,
                        f"¡ALERTA! Violencia detectada ({deteccion['probabilidad']:.1%})",
                        color=(0, 0, 255),
                        tamano=1.2
                    )
                    
                    # Actualizar resultado
                    resultado['frame_procesado'] = frame_procesado
                    
                    # Si no está grabando evidencia, iniciar grabación
                    if not self.grabando_evidencia:
                        self.grabando_evidencia = True
                        self.frames_evidencia = list(self.buffer_evidencia)
                        # Crear registro de incidente
                        await self._crear_incidente(personas_rastreadas, deteccion['probabilidad'])
                    
                    # Agregar frame actual a evidencia
                    if self.grabando_evidencia:
                        self.frames_evidencia.append(frame_procesado)
                else:
                    # Si ya no hay violencia pero estaba grabando, guardar video
                    if self.grabando_evidencia:
                        self.grabando_evidencia = False
                        await self._guardar_evidencia()
                        self.frames_evidencia.clear()

            # Agregar frame al buffer circular
            self.buffer_evidencia.append(frame_procesado.copy())
            
            return resultado

        except Exception as e:
            logger.error(f"Error en pipeline: {e}")
            return {
                'frame_procesado': frame,
                'personas_detectadas': [],
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0
            }
    
    async def _activar_alarma(self):
        """Activa la alarma Tuya"""
        try:
            await self.servicio_alarma.activar_alarma(duracion=5)
        except Exception as e:
            logger.error(f"Error al activar alarma: {e}")
            print(f"Error al activar alarma: {e}")
    
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
            print(f"Error al enviar notificaciones: {e}")
    
    async def _crear_incidente(
        self,
        personas_involucradas: List[Dict[str, Any]],
        probabilidad: float
    ):
        """Crea un registro de incidente"""
        try:
            if not self.servicio_incidentes:
                logger.error("❌ Servicio de incidentes no inicializado")
                print("❌ Servicio de incidentes no inicializado")
                return
                
            # Debug para verificar servicio y sesión
            logger.info("⏳ Verificando servicio de incidentes y sesión...")
            print("⏳ Verificando servicio de incidentes y sesión...")
            
            ids_personas = [str(p['id']) for p in personas_involucradas]
            
            incidente_data = {
                'camara_id': self.camara_id,
                'tipo_incidente': TipoIncidente.VIOLENCIA_FISICA,  # Quitar .value
                'severidad': self._calcular_severidad(probabilidad),  # Quitar .value
                'probabilidad_violencia': probabilidad,
                'fecha_hora_inicio': datetime.now(),
                'ubicacion': self.ubicacion,
                'numero_personas_involucradas': len(personas_involucradas),
                'ids_personas_detectadas': ids_personas,
                'estado': EstadoIncidente.NUEVO,  # Quitar .value
                'descripcion': f"Violencia detectada con probabilidad {probabilidad:.2%}"
            }
            
            logger.info(f"⏳ Creando incidente con datos: {incidente_data}")
            print(f"⏳ Creando incidente con datos: {incidente_data}")
            
            incidente = await self.servicio_incidentes.crear_incidente(incidente_data)
            
            if incidente and hasattr(incidente, 'id'):
                self.incidente_actual_id = incidente.id
                self.incidentes_detectados += 1
                logger.info(f"✅ Nuevo incidente registrado ID: {incidente.id}")
                print(f"✅ Nuevo incidente registrado ID: {incidente.id}")
            else:
                logger.error("❌ Error: Incidente creado pero sin ID")
                print("❌ Error: Incidente creado pero sin ID")
                
        except Exception as e:
            logger.error(f"❌ Error al crear incidente: {str(e)}")
            print(f"❌ Error al crear incidente: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    async def _guardar_evidencia(self):
        """Guarda el clip de video de evidencia"""
        try:
            if not self.frames_evidencia:
                logger.warning("❌ No hay frames para guardar evidencia")
                print("❌ No hay frames para guardar evidencia")
                return

            # 1. Crear directorios si no existen
            ruta_base = configuracion.VIDEO_EVIDENCE_PATH / "clips"
            ruta_base.mkdir(parents=True, exist_ok=True)

            # 2. Generar nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"evidencia_camara{self.camara_id}_{timestamp}.mp4"
            ruta_evidencia = ruta_base / nombre_archivo

            logger.info(f"⏳ Iniciando guardado de video con {len(self.frames_evidencia)} frames")
            print(f"⏳ Iniciando guardado de video con {len(self.frames_evidencia)} frames")

            # 3. Obtener dimensiones del primer frame
            if not self.frames_evidencia:
                raise ValueError("No hay frames para guardar")
                
            height, width = self.frames_evidencia[0].shape[:2]
            
            # 5. Crear el video writer
            fps = configuracion.DEFAULT_FPS

            # Modificar esta parte del código
            if os.name == 'nt':  # Windows
                # Intentar diferentes codecs en orden
                codecs = [
                    ('avc1', cv2.VideoWriter_fourcc(*'avc1')),
                    ('mp4v', cv2.VideoWriter_fourcc(*'mp4v')),
                    ('XVID', cv2.VideoWriter_fourcc(*'XVID')),
                    ('MJPG', cv2.VideoWriter_fourcc(*'MJPG'))
                ]
                
                video_writer = None
                for codec_name, fourcc in codecs:
                    try:
                        video_writer = cv2.VideoWriter(
                            str(ruta_evidencia),
                            fourcc,
                            fps,
                            (width, height)
                        )
                        if video_writer.isOpened():
                            logger.info(f"✅ Usando codec: {codec_name}")
                            print(f"✅ Usando codec: {codec_name}")
                            break
                    except Exception:
                        continue
                        
                if not video_writer or not video_writer.isOpened():
                    raise RuntimeError("No se pudo crear el VideoWriter con ningún codec")
            else:
                # Linux/Mac
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(
                    str(ruta_evidencia),
                    fourcc,
                    fps,
                    (width, height)
                )

            # 6. Escribir frames
            frames_escritos = 0
            for frame in self.frames_evidencia:
                video_writer.write(frame)
                frames_escritos += 1
                
                # Log cada 30 frames
                if frames_escritos % 30 == 0:
                    logger.info(f"⏳ Guardando frame {frames_escritos}/{len(self.frames_evidencia)}")
                    print(f"⏳ Guardando frame {frames_escritos}/{len(self.frames_evidencia)}")

            # 7. Liberar recursos
            video_writer.release()

            # 8. Verificar que el archivo se creó correctamente
            if not ruta_evidencia.exists():
                raise FileNotFoundError(f"❌ No se pudo crear el archivo de video: {ruta_evidencia}")

            tamano_archivo = ruta_evidencia.stat().st_size / (1024 * 1024)  # Tamaño en MB
            logger.info(f"✅ Video guardado exitosamente: {ruta_evidencia} ({tamano_archivo:.2f} MB)")
            print(f"✅ Video guardado exitosamente: {ruta_evidencia} ({tamano_archivo:.2f} MB)")

            # 9. Actualizar incidente con la ruta del video
            if hasattr(self, 'incidente_actual_id') and self.incidente_actual_id:
                try:
                    await self.servicio_incidentes.actualizar_incidente(
                        self.incidente_actual_id,
                        {
                            'video_evidencia_path': str(ruta_evidencia),
                            'fecha_hora_fin': datetime.now()
                        }
                    )
                    logger.info(f"✅ Incidente {self.incidente_actual_id} actualizado con video")
                    print(f"✅ Incidente {self.incidente_actual_id} actualizado con video")
                except Exception as e:
                    logger.error(f"❌ Error actualizando incidente con video: {e}")
                    print(f"❌ Error actualizando incidente con video: {e}")

            return str(ruta_evidencia)

        except Exception as e:
            logger.error(f"❌ Error al guardar evidencia: {e}")
            print(f"❌ Error al guardar evidencia: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    
    
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
        print("Pipeline reiniciado")