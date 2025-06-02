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
import threading
import queue

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
        
        # Buffer circular para evidencia con tamaño fijo
        buffer_size = configuracion.DEFAULT_FPS * configuracion.CLIP_DURATION
        self.buffer_evidencia = deque(maxlen=buffer_size)
        
        # Control de grabación de evidencia
        self.grabando_evidencia = False
        self.frames_evidencia = []
        self.max_frames_evidencia = configuracion.DEFAULT_FPS * 10  # Máximo 10 segundos
        
        # Cola para guardar videos de forma asíncrona
        self.cola_guardado = queue.Queue()
        self.hilo_guardado = threading.Thread(target=self._procesar_cola_guardado, daemon=True)
        self.hilo_guardado.start()
        
        # Estadísticas
        self.frames_procesados = 0
        self.incidentes_detectados = 0
        
        # Control de tiempo para evitar spam
        self.ultimo_incidente = 0
        self.cooldown_incidente = 5  # 5 segundos entre incidentes

    async def procesar_frame(self, frame: np.ndarray, camara_id: int, ubicacion: str) -> Dict[str, Any]:
        try:
            self.camara_id = camara_id
            self.ubicacion = ubicacion
            self.frames_procesados += 1
            
            # Crear copia del frame original con dimensiones consistentes
            frame_original = frame.copy()
            altura_original, ancho_original = frame_original.shape[:2]
            
            # Detección de personas con YOLO (asíncrona)
            detecciones = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.detector_personas.detectar, 
                frame_original
            )
            
            # Crear frame procesado para display
            frame_procesado = frame_original.copy()
            
            # Dibujar bounding boxes de forma asíncrona
            if detecciones:
                frame_procesado = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._dibujar_detecciones,
                    frame_procesado,
                    detecciones
                )

            resultado = {
                'frame_procesado': frame_procesado,
                'personas_detectadas': detecciones,
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0
            }

            # Agregar frame al buffer de evidencia (siempre)
            frame_para_buffer = {
                'frame': frame_procesado.copy(),
                'timestamp': datetime.now(),
                'detecciones': detecciones
            }
            self.buffer_evidencia.append(frame_para_buffer)

            # Solo procesar con TimesFormer si hay personas detectadas
            if detecciones:
                # Agregar frame para detección de violencia
                self.detector_violencia.agregar_frame(frame_original.copy())
                
                # Procesar cada N frames
                if self.frames_procesados % configuracion.TIMESFORMER_CONFIG["num_frames"] == 0:
                    # Detección de violencia de forma asíncrona
                    deteccion = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.detector_violencia.detectar
                    )
                    
                    resultado.update(deteccion)

                    if deteccion['violencia_detectada']:
                        current_time = datetime.now().timestamp()
                        
                        # Control de cooldown para evitar múltiples incidentes
                        if current_time - self.ultimo_incidente > self.cooldown_incidente:
                            # Activar alarma de forma asíncrona
                            asyncio.create_task(self._activar_alarma())
                            
                            # Agregar alerta al frame
                            frame_procesado = await asyncio.get_event_loop().run_in_executor(
                                None,
                                self.procesador_video.agregar_texto_alerta,
                                frame_procesado,
                                f"¡ALERTA! Violencia detectada ({deteccion['probabilidad']:.1%})",
                                (0, 0, 255),
                                1.2
                            )
                            
                            resultado['frame_procesado'] = frame_procesado
                            
                            # Iniciar grabación de evidencia si no está activa
                            if not self.grabando_evidencia:
                                self.grabando_evidencia = True
                                # Copiar buffer actual como inicio de evidencia
                                self.frames_evidencia = [item['frame'].copy() for item in list(self.buffer_evidencia)]
                                
                                # Crear incidente de forma asíncrona
                                asyncio.create_task(self._crear_incidente(detecciones, deteccion['probabilidad']))
                                self.ultimo_incidente = current_time
                            
                            # Continuar grabando evidencia
                            if self.grabando_evidencia and len(self.frames_evidencia) < self.max_frames_evidencia:
                                self.frames_evidencia.append(frame_procesado.copy())
                    else:
                        # Si no hay violencia y estábamos grabando, finalizar grabación
                        if self.grabando_evidencia:
                            self._finalizar_grabacion_evidencia()

            return resultado

        except Exception as e:
            print(f"Error en pipeline: {str(e)}")
            return {
                'frame_procesado': frame,
                'personas_detectadas': [],
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0
            }

    def _dibujar_detecciones(self, frame: np.ndarray, detecciones: List[Dict]) -> np.ndarray:
        """Dibuja las detecciones en el frame"""
        for deteccion in detecciones:
            frame = self.procesador_video.dibujar_bounding_box(
                frame,
                deteccion['bbox'],
                label=f"Persona ({deteccion['confianza']:.2f})"
            )
        return frame

    def _finalizar_grabacion_evidencia(self):
        """Finaliza la grabación y envía a la cola de guardado"""
        if self.frames_evidencia:
            print(f"Finalizando grabación con {len(self.frames_evidencia)} frames")
            
            # Enviar a cola de guardado asíncrono
            datos_guardado = {
                'frames': self.frames_evidencia.copy(),
                'camara_id': self.camara_id,
                'timestamp': datetime.now(),
                'incidente_id': getattr(self, 'incidente_actual_id', None)
            }
            
            try:
                self.cola_guardado.put_nowait(datos_guardado)
            except queue.Full:
                print("Cola de guardado llena, descartando video")
            
            # Limpiar
            self.frames_evidencia.clear()
            self.grabando_evidencia = False

    def _procesar_cola_guardado(self):
        """Procesa la cola de guardado en hilo separado"""
        while True:
            try:
                datos = self.cola_guardado.get(timeout=1)
                self._guardar_evidencia_sincrono(datos)
                self.cola_guardado.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error en hilo de guardado: {e}")

    def _guardar_evidencia_sincrono(self, datos: Dict[str, Any]):
        """Guarda evidencia de forma síncrona en hilo separado"""
        try:
            frames = datos['frames']
            camara_id = datos['camara_id']
            timestamp = datos['timestamp']
            incidente_id = datos.get('incidente_id')
            
            if not frames:
                print("No hay frames para guardar evidencia")
                return

            # Crear directorio
            ruta_base = configuracion.VIDEO_EVIDENCE_PATH / "clips"
            ruta_base.mkdir(parents=True, exist_ok=True)

            # Generar nombre de archivo
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"evidencia_camara{camara_id}_{timestamp_str}.mp4"
            ruta_evidencia = ruta_base / nombre_archivo

            # Obtener dimensiones del primer frame
            height, width = frames[0].shape[:2]
            
            # FPS consistente para el video
            fps_video = 15  # FPS fijo para evidencia
            
            # Crear video writer
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            video_writer = cv2.VideoWriter(
                str(ruta_evidencia),
                fourcc,
                fps_video,
                (width, height)
            )

            if not video_writer.isOpened():
                print(f"Error: No se pudo crear VideoWriter para {ruta_evidencia}")
                return

            # Escribir frames con control de calidad
            frames_escritos = 0
            for i, frame in enumerate(frames):
                try:
                    # Asegurar dimensiones consistentes
                    if frame.shape[:2] != (height, width):
                        frame = cv2.resize(frame, (width, height))
                    
                    video_writer.write(frame)
                    frames_escritos += 1
                    
                except Exception as e:
                    print(f"Error escribiendo frame {i}: {e}")
                    continue

            video_writer.release()

            # Verificar que el archivo se creó correctamente
            if ruta_evidencia.exists() and frames_escritos > 0:
                tamano_archivo = ruta_evidencia.stat().st_size / (1024 * 1024)
                print(f"Video guardado: {ruta_evidencia} ({tamano_archivo:.2f} MB, {frames_escritos} frames)")
                
                # Actualizar incidente si existe (de forma asíncrona)
                if incidente_id:
                    asyncio.run_coroutine_threadsafe(
                        self._actualizar_incidente_con_video(incidente_id, str(ruta_evidencia)),
                        asyncio.get_event_loop()
                    )
            else:
                print(f"Error: No se pudo crear el archivo de video o no hay frames")

        except Exception as e:
            print(f"Error al guardar evidencia: {e}")
            import traceback
            print(traceback.format_exc())

    async def _actualizar_incidente_con_video(self, incidente_id: int, ruta_video: str):
        """Actualiza el incidente con la ruta del video"""
        try:
            await self.servicio_incidentes.actualizar_incidente(
                incidente_id,
                {
                    'video_evidencia_path': ruta_video,
                    'fecha_hora_fin': datetime.now()
                }
            )
            print(f"Incidente {incidente_id} actualizado con video")
        except Exception as e:
            print(f"Error actualizando incidente con video: {e}")

    async def _activar_alarma(self):
        """Activa la alarma de forma asíncrona"""
        try:
            await self.servicio_alarma.activar_alarma(duracion=5)
        except Exception as e:
            print(f"Error al activar alarma: {e}")

    async def _enviar_notificaciones(self, personas_involucradas: List[Dict[str, Any]]):
        """Envía notificaciones de forma asíncrona"""
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
        """Crea un incidente de forma asíncrona"""
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
            import traceback
            print(traceback.format_exc())

    def _calcular_severidad(self, probabilidad: float) -> SeveridadIncidente:
        """Calcula la severidad basada en la probabilidad"""
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
            'personas_rastreadas': 0,
            'violencia_activa': self.detector_violencia.violencia_detectada,
            'probabilidad_actual': self.detector_violencia.probabilidad_violencia,
            'grabando_evidencia': self.grabando_evidencia,
            'frames_en_buffer': len(self.buffer_evidencia),
            'frames_evidencia': len(self.frames_evidencia) if self.frames_evidencia else 0
        }

    def reiniciar(self):
        """Reinicia el estado del pipeline"""
        # Finalizar grabación si está activa
        if self.grabando_evidencia:
            self._finalizar_grabacion_evidencia()
        
        # Reiniciar detector de violencia
        self.detector_violencia.reiniciar()
        
        # Limpiar buffers
        self.buffer_evidencia.clear()
        self.frames_evidencia = []
        self.grabando_evidencia = False
        
        # Reiniciar contadores
        self.frames_procesados = 0
        self.ultimo_incidente = 0
        
        print("Pipeline reiniciado")

    def __del__(self):
        """Destructor para limpiar recursos"""
        try:
            if self.grabando_evidencia:
                self._finalizar_grabacion_evidencia()
        except:
            pass