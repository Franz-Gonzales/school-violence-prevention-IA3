import cv2
import numpy as np
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import threading
import queue
import time
import traceback
import concurrent.futures

from app.ai.yolo_detector import DetectorPersonas
from app.ai.violence_detector import DetectorViolencia
from app.services.alarm_service import ServicioAlarma
from app.services.notification_service import ServicioNotificaciones
from app.services.incident_service import ServicioIncidentes
from app.models.incident import TipoIncidente, SeveridadIncidente, EstadoIncidente
from app.utils.video_utils import ProcesadorVideo
from app.utils.logger import obtener_logger
from app.config import configuracion
from app.tasks.video_recorder import evidence_recorder
from sqlalchemy.ext.asyncio import AsyncSession

logger = obtener_logger(__name__)

class FrameBuffer:
    """Buffer inteligente para frames con timestamps precisos"""
    def __init__(self, max_duration_seconds=30):
        self.frames = deque()
        self.max_duration = max_duration_seconds
        
    def add_frame(self, frame, timestamp, detecciones=None, violencia_info=None):
        """Agrega un frame con timestamp preciso y información de violencia"""
        frame_data = {
            'frame': frame.copy(),
            'timestamp': timestamp,
            'detecciones': detecciones or [],
            'violencia_info': violencia_info,
            'processed': False
        }
        self.frames.append(frame_data)
        
        # Limpiar frames antiguos
        current_time = timestamp
        while self.frames and (current_time - self.frames[0]['timestamp']).total_seconds() > self.max_duration:
            self.frames.popleft()
    
    def get_frames_in_range(self, start_time, end_time):
        """Obtiene frames en un rango de tiempo específico"""
        return [f for f in self.frames 
                if start_time <= f['timestamp'] <= end_time]
    
    def get_recent_frames(self, duration_seconds):
        """Obtiene frames recientes basado en duración"""
        if not self.frames:
            return []
        
        latest_time = self.frames[-1]['timestamp']
        start_time = latest_time - timedelta(seconds=duration_seconds)
        return self.get_frames_in_range(start_time, latest_time)

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
        
        # Buffer inteligente para evidencia
        self.buffer_evidencia = FrameBuffer(max_duration_seconds=30)
        
        # Control de grabación de evidencia
        self.grabando_evidencia = False
        self.tiempo_inicio_violencia = None
        self.tiempo_fin_violencia = None
        self.duracion_evidencia_pre = 6
        self.duracion_evidencia_post = 8
        
        # Cola para guardar videos de forma asíncrona
        self.cola_guardado = queue.Queue()
        self.hilo_guardado = threading.Thread(target=self._procesar_cola_guardado, daemon=True)
        self.hilo_guardado.start()
        
        # POOL DE HILOS PARA UPDATES DE DB - SOLUCIÓN PRINCIPAL
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="db_update")
        
        # Estadísticas
        self.frames_procesados = 0
        self.incidentes_detectados = 0
        
        # Control de tiempo para evitar spam
        self.ultimo_incidente = 0
        self.cooldown_incidente = 5
        
        # FPS target para evidencia
        self.target_fps_evidencia = 15
        
        # Control para evidencia
        self.frame_feed_interval = 1.0 / 25
        self.last_evidence_feed = 0

        # Inicializar recorder de evidencia
        evidence_recorder.start_processing()

    async def procesar_frame(self, frame: np.ndarray, camara_id: int, ubicacion: str) -> Dict[str, Any]:
        try:
            self.camara_id = camara_id
            self.ubicacion = ubicacion
            self.frames_procesados += 1
            
            # Timestamp preciso para este frame
            timestamp_actual = datetime.now()
            
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
                'probabilidad_violencia': 0.0,
                'timestamp': timestamp_actual
            }

            # Variable para información de violencia
            violencia_info = None

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
                        current_time = timestamp_actual.timestamp()
                        
                        # Preparar información de violencia para el frame
                        violencia_info = {
                            'detectada': True,
                            'probabilidad': deteccion.get('probabilidad', 0.0),
                            'timestamp': timestamp_actual
                        }
                        
                        # Control de cooldown para evitar múltiples incidentes
                        if current_time - self.ultimo_incidente > self.cooldown_incidente:
                            # Marcar inicio de violencia
                            if not self.grabando_evidencia:
                                self.tiempo_inicio_violencia = timestamp_actual
                                self.grabando_evidencia = True
                                print(f"🚨 INICIO DE VIOLENCIA DETECTADA: {self.tiempo_inicio_violencia}")
                            
                            # Activar alarma de forma asíncrona
                            asyncio.create_task(self._activar_alarma())
                            
                            # Agregar alerta al frame CON PROBABILIDAD CORRECTA
                            probabilidad_texto = f"¡ALERTA! Violencia detectada ({deteccion.get('probabilidad', 0.0):.1%})"
                            frame_procesado = await asyncio.get_event_loop().run_in_executor(
                                None,
                                self.procesador_video.agregar_texto_alerta,
                                frame_procesado,
                                probabilidad_texto,
                                (0, 0, 255),
                                1.2
                            )
                            
                            resultado['frame_procesado'] = frame_procesado
                            
                            # Crear incidente si es el primer frame de violencia
                            if not hasattr(self, 'incidente_actual_id'):
                                asyncio.create_task(self._crear_incidente(detecciones, deteccion.get('probabilidad', 0.0)))
                                self.ultimo_incidente = current_time
                            
                            # Actualizar tiempo de fin de violencia
                            self.tiempo_fin_violencia = timestamp_actual
                    else:
                        # Si no hay violencia y estábamos grabando, finalizar después de un delay
                        if self.grabando_evidencia and self.tiempo_fin_violencia:
                            tiempo_transcurrido = (timestamp_actual - self.tiempo_fin_violencia).total_seconds()
                            if tiempo_transcurrido >= self.duracion_evidencia_post:
                                await self._finalizar_grabacion_evidencia()

            # Agregar frame al buffer MÁS AGRESIVAMENTE
            current_time = time.time()
            if current_time - self.last_evidence_feed >= self.frame_feed_interval:
                self.buffer_evidencia.add_frame(
                    frame_procesado, 
                    timestamp_actual, 
                    detecciones,
                    violencia_info
                )
                evidence_recorder.add_frame(frame_original, detecciones, violencia_info)
                self.last_evidence_feed = current_time
            
            return resultado

        except Exception as e:
            print(f"Error en pipeline: {str(e)}")
            return {
                'frame_procesado': frame,
                'personas_detectadas': [],
                'violencia_detectada': False,
                'probabilidad_violencia': 0.0,
                'timestamp': datetime.now()
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

    async def _finalizar_grabacion_evidencia(self):
        """Finaliza la grabación y envía a la cola de guardado con timestamps precisos"""
        if not self.tiempo_inicio_violencia:
            return
            
        print(f"📹 Finalizando grabación de evidencia...")
        
        # Calcular tiempos para el clip de evidencia
        tiempo_inicio_clip = self.tiempo_inicio_violencia - timedelta(seconds=self.duracion_evidencia_pre)
        tiempo_fin_clip = self.tiempo_fin_violencia + timedelta(seconds=self.duracion_evidencia_post)
        
        # Obtener frames del rango de tiempo específico
        frames_evidencia = self.buffer_evidencia.get_frames_in_range(
            tiempo_inicio_clip, 
            tiempo_fin_clip
        )
        
        if frames_evidencia:
            duracion_total = (tiempo_fin_clip - tiempo_inicio_clip).total_seconds()
            print(f"📹 Extraídos {len(frames_evidencia)} frames para evidencia")
            print(f"📹 Duración del clip: {duracion_total:.2f} segundos")
            
            # GARANTIZAR MÍNIMO 5 SEGUNDOS
            if len(frames_evidencia) < (5 * self.target_fps_evidencia) or duracion_total < 5.0:
                print(f"⚠️ Video muy corto ({duracion_total:.1f}s), extendiendo con frames recientes...")
                frames_evidencia = self.buffer_evidencia.get_recent_frames(12)
                print(f"📹 Frames extendidos: {len(frames_evidencia)}")
            
            # Enviar a cola de guardado asíncrono
            datos_guardado = {
                'frames': frames_evidencia,
                'camara_id': self.camara_id,
                'tiempo_inicio': tiempo_inicio_clip,
                'tiempo_fin': tiempo_fin_clip,
                'incidente_id': getattr(self, 'incidente_actual_id', None),
                'fps_target': self.target_fps_evidencia
            }
            
            try:
                self.cola_guardado.put_nowait(datos_guardado)
                print("📹 Evidencia enviada a cola de guardado")
            except queue.Full:
                print("❌ Cola de guardado llena, descartando video")
        
        # Limpiar estado
        self.grabando_evidencia = False
        self.tiempo_inicio_violencia = None
        self.tiempo_fin_violencia = None
        if hasattr(self, 'incidente_actual_id'):
            delattr(self, 'incidente_actual_id')

    def _procesar_cola_guardado(self):
        """Procesa la cola de guardado en hilo separado"""
        while True:
            try:
                datos = self.cola_guardado.get(timeout=1)
                self._guardar_evidencia_mejorado(datos)
                self.cola_guardado.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error en hilo de guardado: {e}")

    def _guardar_evidencia_mejorado(self, datos: Dict[str, Any]):
        """Guarda evidencia con overlay de violencia - MANTENER FUNCIONAL"""
        try:
            frames_data = datos['frames']
            camara_id = datos['camara_id']
            tiempo_inicio = datos['tiempo_inicio']
            fps_target = datos['fps_target']
            incidente_id = datos.get('incidente_id')
            
            if not frames_data:
                print("❌ No hay frames para guardar evidencia")
                return

            # Crear directorio
            ruta_base = configuracion.VIDEO_EVIDENCE_PATH / "clips"
            ruta_base.mkdir(parents=True, exist_ok=True)

            # Generar nombre de archivo con timestamp
            timestamp_str = tiempo_inicio.strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"evidencia_camara{camara_id}_{timestamp_str}.mp4"
            ruta_evidencia = ruta_base / nombre_archivo

            # Obtener dimensiones del primer frame
            primer_frame = frames_data[0]['frame']
            height, width = primer_frame.shape[:2]
            
            print(f"📹 Guardando video: {nombre_archivo}")
            print(f"📹 Dimensiones: {width}x{height}")
            print(f"📹 FPS objetivo: {fps_target}")
            print(f"📹 Frames disponibles: {len(frames_data)}")
            
            # DUPLICAR/INTERPOLAR FRAMES PARA GARANTIZAR 5+ SEGUNDOS
            frames_minimos = int(5.0 * fps_target)
            if len(frames_data) < frames_minimos:
                frames_expandidos = self._expandir_frames_para_duracion(frames_data, frames_minimos)
                print(f"📹 Frames expandidos de {len(frames_data)} a {len(frames_expandidos)} para 5+ segundos")
                frames_data = frames_expandidos
            
            # USAR MP4V COMO CODEC PRINCIPAL
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(
                str(ruta_evidencia),
                fourcc,
                fps_target,
                (width, height)
            )

            if not video_writer.isOpened():
                print(f"❌ Error: No se pudo crear VideoWriter para {ruta_evidencia}")
                return

            # ESCRIBIR FRAMES CON OVERLAY DE VIOLENCIA
            frames_escritos = 0
            for i, frame_data in enumerate(frames_data):
                try:
                    frame = frame_data['frame'].copy()
                    
                    # Asegurar dimensiones consistentes
                    if frame.shape[:2] != (height, width):
                        frame = cv2.resize(frame, (width, height))
                    
                    # AGREGAR OVERLAY DE VIOLENCIA EN ROJO SI ESTÁ PRESENTE
                    violencia_info = frame_data.get('violencia_info')
                    if violencia_info and violencia_info.get('detectada'):
                        frame = self._agregar_overlay_violencia(frame, violencia_info)
                    
                    video_writer.write(frame)
                    frames_escritos += 1
                    
                except Exception as e:
                    print(f"❌ Error escribiendo frame {i}: {e}")
                    continue

            video_writer.release()

            # Verificar que el archivo se creó correctamente
            if ruta_evidencia.exists() and frames_escritos > 0:
                tamano_archivo = ruta_evidencia.stat().st_size / (1024 * 1024)
                duracion_real = frames_escritos / fps_target
                print(f"✅ Video guardado: {ruta_evidencia}")
                print(f"📹 Tamaño: {tamano_archivo:.2f} MB")
                print(f"📹 Frames: {frames_escritos}")
                print(f"📹 Duración: {duracion_real:.2f} segundos")
                
                # ACTUALIZAR INCIDENTE SIN CREAR CONFLICTOS DE LOOP
                if incidente_id:
                    self._actualizar_incidente_thread_safe(incidente_id, str(ruta_evidencia))
            else:
                print(f"❌ Error: No se pudo crear el archivo de video o no hay frames")

        except Exception as e:
            print(f"❌ Error al guardar evidencia: {e}")
            import traceback
            traceback.print_exc()

    def _expandir_frames_para_duracion(self, frames_data: List[Dict], frames_objetivo: int) -> List[Dict]:
        """Expande/duplica frames para garantizar duración mínima"""
        if len(frames_data) >= frames_objetivo:
            return frames_data
        
        frames_expandidos = []
        factor_expansion = frames_objetivo / len(frames_data)
        
        for i, frame_data in enumerate(frames_data):
            # Agregar frame original
            frames_expandidos.append(frame_data)
            
            # Calcular cuántas copias agregar
            copias_a_agregar = int(factor_expansion) - 1
            if i < (frames_objetivo % len(frames_data)):
                copias_a_agregar += 1
            
            # Agregar copias del frame
            for _ in range(copias_a_agregar):
                frame_copia = {
                    'frame': frame_data['frame'].copy(),
                    'timestamp': frame_data['timestamp'],
                    'detecciones': frame_data.get('detecciones', []),
                    'violencia_info': frame_data.get('violencia_info')
                }
                frames_expandidos.append(frame_copia)
        
        return frames_expandidos[:frames_objetivo]

    def _agregar_overlay_violencia(self, frame: np.ndarray, violencia_info: Dict) -> np.ndarray:
        """Agrega overlay rojo de violencia al frame"""
        height, width = frame.shape[:2]
        probabilidad = violencia_info.get('probabilidad', 0.0)
        
        # Crear overlay semitransparente rojo
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (width-10, 100), (0, 0, 255), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # Texto principal de VIOLENCIA DETECTADA
        texto_principal = "VIOLENCIA DETECTADA"
        cv2.putText(
            frame, 
            texto_principal, 
            (20, 40), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.0, 
            (255, 255, 255), 
            3,
            cv2.LINE_AA
        )
        
        # Texto de probabilidad EN ROJO BRILLANTE
        texto_probabilidad = f"Probabilidad: {probabilidad:.1%}"
        cv2.putText(
            frame, 
            texto_probabilidad, 
            (20, 75), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (255, 255, 255), 
            2,
            cv2.LINE_AA
        )
        
        # Timestamp
        timestamp_str = violencia_info.get('timestamp', datetime.now()).strftime("%H:%M:%S")
        cv2.putText(
            frame, 
            f"Tiempo: {timestamp_str}", 
            (20, 95), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5, 
            (255, 255, 255), 
            1,
            cv2.LINE_AA
        )
        
        return frame

    def _actualizar_incidente_thread_safe(self, incidente_id: int, ruta_video: str):
        """SOLUCIÓN PRINCIPAL: Actualiza incidente usando ThreadPoolExecutor para evitar conflictos de loop"""
        try:
            def update_sync():
                """Función síncrona que se ejecuta en el pool de hilos"""
                try:
                    # Usar requests HTTP en lugar de conexión directa a DB para evitar conflictos
                    import requests
                    import json
                    
                    # URL del endpoint de actualización INTERNO ⭐ AQUÍ ES DONDE VA EL CAMBIO ⭐
                    api_url = "http://localhost:8000/api/v1/incidents"
                    update_url = f"{api_url}/{incidente_id}/internal"  # ⭐ ESTA LÍNEA ⭐
                    
                    # Datos de actualizaciónq
                    update_data = {
                        "video_evidencia_path": ruta_video
                    }
                    
                    # Headers básicos
                    headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                    
                    # Realizar petición HTTP PATCH
                    response = requests.patch(
                        update_url,
                        json=update_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Incidente {incidente_id} actualizado con video: {ruta_video}")
                    else:
                        print(f"⚠️ Respuesta HTTP {response.status_code} al actualizar incidente {incidente_id}")
                        # Fallback: Log para revisión manual
                        print(f"📝 MANUAL UPDATE NEEDED: Incidente {incidente_id} -> {ruta_video}")
                        
                except Exception as e:
                    print(f"❌ Error en update_sync: {e}")
                    # Fallback: Log para revisión manual
                    print(f"📝 MANUAL UPDATE NEEDED: Incidente {incidente_id} -> {ruta_video}")
            
            # Ejecutar en pool de hilos dedicado SIN crear nuevos loops
            future = self.executor.submit(update_sync)
            
            # Opcional: agregar callback para manejar resultado
            def handle_result(fut):
                try:
                    fut.result(timeout=5)  # Timeout de 5 segundos
                except Exception as e:
                    print(f"❌ Error en future result: {e}")
            
            future.add_done_callback(handle_result)
            
        except Exception as e:
            print(f"❌ Error en actualización thread-safe: {e}")
            # Fallback final
            print(f"📝 MANUAL UPDATE NEEDED: Incidente {incidente_id} -> {ruta_video}")

    async def _activar_alarma(self):
        """Activa la alarma de forma asíncrona"""
        try:
            await self.servicio_alarma.activar_alarma(5)
        except Exception as e:
            print(f"Error activando alarma: {e}")

    async def _crear_incidente(self, personas_involucradas: List[Dict[str, Any]], probabilidad: float):
        """Crea un incidente de forma asíncrona"""
        try:
            datos_incidente = {
                'camara_id': self.camara_id,
                'tipo_incidente': TipoIncidente.VIOLENCIA_FISICA,
                'severidad': self._calcular_severidad(probabilidad),
                'probabilidad_violencia': probabilidad,
                'fecha_hora_inicio': self.tiempo_inicio_violencia,
                'ubicacion': self.ubicacion,
                'numero_personas_involucradas': len(personas_involucradas),
                'ids_personas_detectadas': [],
                'estado': EstadoIncidente.NUEVO,
                'descripcion': f"Violencia detectada con probabilidad {probabilidad:.2%}"
            }
            
            incidente = await self.servicio_incidentes.crear_incidente(datos_incidente)
            self.incidente_actual_id = incidente.id
            self.incidentes_detectados += 1
            
            print(f"📊 Nuevo incidente registrado ID: {incidente.id}")
            
        except Exception as e:
            print(f"Error creando incidente: {e}")
            import traceback
            traceback.print_exc()

    def _calcular_severidad(self, probabilidad: float) -> SeveridadIncidente:
        """Calcula la severidad basada en la probabilidad"""
        if probabilidad >= 0.9:
            return SeveridadIncidente.CRITICA
        elif probabilidad >= 0.8:
            return SeveridadIncidente.ALTA
        elif probabilidad >= 0.6:
            return SeveridadIncidente.MEDIA
        else:
            return SeveridadIncidente.BAJA

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del pipeline"""
        return {
            'frames_procesados': self.frames_procesados,
            'incidentes_detectados': self.incidentes_detectados,
            'activo': self.activo,
            'grabando_evidencia': self.grabando_evidencia,
            'buffer_size': len(self.buffer_evidencia.frames)
        }

    def reiniciar(self):
        """Reinicia el pipeline"""
        self.detector_violencia.reiniciar()
        self.frames_procesados = 0
        self.activo = False
        self.grabando_evidencia = False
        self.tiempo_inicio_violencia = None
        self.tiempo_fin_violencia = None
        print("🔄 Pipeline reiniciado")

    def __del__(self):
        """Limpieza al destruir el objeto"""
        try:
            if hasattr(self, 'hilo_guardado') and self.hilo_guardado.is_alive():
                self.cola_guardado.put(None)
            
            # Cerrar pool de hilos
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
        except:
            pass
