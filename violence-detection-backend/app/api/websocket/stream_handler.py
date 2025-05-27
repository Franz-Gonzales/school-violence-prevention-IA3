# app/api/websocket/stream_handler.py
import cv2
from typing import Optional, Dict, Any
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from app.ai.model_loader import cargador_modelos
from app.ai.pipeline import PipelineDeteccion
from app.config import configuracion
from app.utils.logger import obtener_logger
from app.api.websocket.common import ManejadorWebRTC, manejador_webrtc

from app.ai.yolo_detector import DetectorPersonas
from app.ai.deep_sort_tracker import TrackerPersonas
from app.ai.violence_detector import DetectorViolencia
from app.services.alarm_service import ServicioAlarma
from app.services.notification_service import ServicioNotificaciones
from app.services.incident_service import ServicioIncidentes

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer



logger = obtener_logger(__name__)

class VideoTrackProcesado(VideoStreamTrack):
    def __init__(self, source: int, pipeline: PipelineDeteccion, manejador_webrtc: ManejadorWebRTC, cliente_id: str, camara_id: int, deteccion_activada: bool = False):
        super().__init__()
        self.source = source
        self.pipeline = pipeline
        self.manejador_webrtc = manejador_webrtc
        self.cliente_id = cliente_id
        self.camara_id = camara_id
        self.deteccion_activada = deteccion_activada
        self.cap = None
        self._start()
        
    def _start(self):
        """Inicializa la captura de video"""
        print(f"Iniciando cámara {self.source}...")
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara {self.source}")
        
        # Configurar resolución y FPS
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, configuracion.DEFAULT_RESOLUTION[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, configuracion.DEFAULT_RESOLUTION[1])
        self.cap.set(cv2.CAP_PROP_FPS, configuracion.DEFAULT_FPS)
        logger.info(f"Cámara {self.source} iniciada exitosamente")
        print(f"Cámara {self.source} iniciada exitosamente")

    async def recv(self):
        try:
            pts, time_base = await self.next_timestamp()

            if self.cap is None or not self.cap.isOpened():
                self._start()

            ret, frame = self.cap.read()
            if not ret:
                logger.error("Error al leer frame de la cámara")
                return None

            # Procesar frame si la detección está activada
            if self.deteccion_activada:
                resultado = await self.pipeline.procesar_frame(
                    frame,
                    camara_id=self.camara_id,
                    ubicacion="Principal"
                )
                if resultado.get('violencia_detectada'):
                    await self.manejador_webrtc.enviar_a_cliente(
                        self.cliente_id,
                        {
                            "tipo": "deteccion_violencia",
                            "violencia_detectada": resultado['violencia_detectada'],
                            "probabilidad": resultado['probabilidad_violencia'],
                            "personas_involucradas": len(resultado['personas_detectadas'])
                        }
                    )
                frame = resultado.get('frame_procesado', frame)

            # Convertir BGR a RGB para WebRTC
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Crear VideoFrame
            from av import VideoFrame
            video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
            video_frame.pts = pts
            video_frame.time_base = time_base

            return video_frame

        except Exception as e:
            logger.error(f"Error en recv: {str(e)}")
            print(f"Error en recv: {str(e)}")
            return None
        
    def stop(self):
        """Libera recursos"""
        if self.cap:
            self.cap.release()
            self.cap = None


class ManejadorStreaming:
    def __init__(self):
        self.conexiones_peer: Dict[str, RTCPeerConnection] = {}
        self.pipelines: Dict[str, PipelineDeteccion] = {}
        self.deteccion_activada: Dict[str, bool] = {}
        self.servicio_alarma = ServicioAlarma()
        

    async def crear_conexion_peer(
        self,
        cliente_id: str,
        camara_id: int,
        manejador_webrtc: ManejadorWebRTC,
        deteccion_activada: bool = False
    ) -> RTCPeerConnection:
        try:
            if cliente_id in self.conexiones_peer:
                await self.cerrar_conexion(cliente_id)

            # Configuración simplificada de RTCPeerConnection
            config = RTCConfiguration(
                iceServers=[
                    RTCIceServer(
                        urls=["stun:stun.l.google.com:19302"]
                    )
                ]
            )

            pc = RTCPeerConnection(configuration=config)
            
            self.conexiones_peer[cliente_id] = pc
            self.deteccion_activada[cliente_id] = deteccion_activada

            # Crear pipeline si no existe
            if cliente_id not in self.pipelines:
                pipeline = self.crear_pipeline(cliente_id)
                self.pipelines[cliente_id] = pipeline

            # Crear y agregar video track
            video_track = VideoTrackProcesado(
                source=1,
                pipeline=self.pipelines[cliente_id],
                manejador_webrtc=manejador_webrtc,
                cliente_id=cliente_id,
                camara_id=camara_id,
                deteccion_activada=deteccion_activada
            )
            pc.addTrack(video_track)

            # Manejar eventos de conexión
            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                logger.info(f"Estado de conexión {cliente_id}: {pc.connectionState}")
                print(f"Estado de conexión {cliente_id}: {pc.connectionState}")
                if pc.connectionState == "failed":
                    await self.cerrar_conexion(cliente_id)

            # Manejar negociación
            @pc.on("negotiationneeded")
            async def on_negotiationneeded():
                logger.info(f"Negociación necesaria para cliente {cliente_id}")
                print(f"Negociación necesaria para cliente {cliente_id}")

            return pc

        except Exception as e:
            logger.error(f"Error al crear conexión peer: {e}")
            print(f"Error al crear conexión peer: {e}")
            await self.cerrar_conexion(cliente_id)
            raise

    async def manejar_offer(
        self,
        cliente_id: str,
        sdp: str, 
        camara_id: int,
        manejador_webrtc: ManejadorWebRTC,
        deteccion_activada: bool = False
    ) -> str:
        try:
            if not sdp:
                raise ValueError("SDP no puede estar vacío")

            pc = await self.crear_conexion_peer(
                cliente_id, 
                camara_id, 
                manejador_webrtc, 
                deteccion_activada
            )

            # Crear y establecer oferta remota
            offer = RTCSessionDescription(sdp=sdp, type="offer")
            await pc.setRemoteDescription(offer)

            # Crear respuesta
            answer = await pc.createAnswer()
            if not answer:
                raise ValueError("No se pudo crear respuesta")

            # Establecer descripción local
            await pc.setLocalDescription(answer)

            if not pc.localDescription or not pc.localDescription.sdp:
                raise ValueError("SDP de respuesta vacío")

            logger.info(f"Respuesta SDP creada para cliente {cliente_id}")
            print(f"Respuesta SDP creada para cliente {cliente_id}")
            return pc.localDescription.sdp

        except Exception as e:
            logger.error(f"Error en manejar_offer: {str(e)}")
            print(f"Error en manejar_offer: {str(e)}")
            await self.cerrar_conexion(cliente_id)
            raise
    
    async def manejar_comando(self, cliente_id: str, mensaje: dict):
        if mensaje.get("tipo") == "iniciar_deteccion":
            self.deteccion_activada[cliente_id] = True
        elif mensaje.get("tipo") == "detener_deteccion":
            self.deteccion_activada[cliente_id] = False
    
    async def cerrar_conexion(self, cliente_id: str):
        """Cierra y limpia recursos de una conexión"""
        try:
            if cliente_id in self.conexiones_peer:
                pc = self.conexiones_peer[cliente_id]
                await pc.close()
                del self.conexiones_peer[cliente_id]
            
            if cliente_id in self.pipelines:
                try:
                    self.pipelines[cliente_id].reiniciar()
                except Exception as e:
                    logger.error(f"Error al reiniciar pipeline: {e}")
                    print(f"Error al reiniciar pipeline: {e}")
                finally:
                    del self.pipelines[cliente_id]
            
            if cliente_id in self.deteccion_activada:
                del self.deteccion_activada[cliente_id]
            
            logger.info(f"Conexión cerrada para cliente {cliente_id}")
            print(f"Conexión cerrada para cliente {cliente_id}")
            
        except Exception as e:
            logger.error(f"Error al cerrar conexión: {e}")
            print(f"Error al cerrar conexión: {e}")
    
    async def manejar_ice_candidate(
        self,
        cliente_id: str,
        candidate: Dict[str, Any]
    ):
        if cliente_id in self.conexiones_peer:
            pc = self.conexiones_peer[cliente_id]
            from aiortc import RTCIceCandidate
            
            ice_candidate = RTCIceCandidate(
                foundation=candidate.get("foundation"),
                component=candidate.get("component"),
                protocol=candidate.get("protocol"),
                priority=candidate.get("priority"),
                ip=candidate.get("ip"),
                port=candidate.get("port"),
                type=candidate.get("type"),
                tcpType=candidate.get("tcpType"),
                relatedAddress=candidate.get("relatedAddress"),
                relatedPort=candidate.get("relatedPort"),
                sdpMLineIndex=candidate.get("sdpMLineIndex"),
                sdpMid=candidate.get("sdpMid")
            )
            
            await pc.addIceCandidate(ice_candidate)
    
    def obtener_estadisticas_stream(self, cliente_id: str) -> Optional[Dict[str, Any]]:
        if cliente_id in self.pipelines:
            return self.pipelines[cliente_id].obtener_estadisticas()
        return None
    
    def crear_pipeline(self, cliente_id: str) -> PipelineDeteccion:
        """Crea un nuevo pipeline de procesamiento"""
        try:
            # Crear detectores
            detector_personas = DetectorPersonas(
                cargador_modelos.obtener_modelo('yolo')
            )
            tracker_personas = TrackerPersonas()
            detector_violencia = DetectorViolencia()

            # Crear pipeline
            pipeline = PipelineDeteccion(
                detector_personas=detector_personas,
                tracker_personas=tracker_personas,
                detector_violencia=detector_violencia,
                servicio_alarma=self.servicio_alarma,
                servicio_notificaciones=None,  # Por ahora None
                servicio_incidentes=None       # Por ahora None
            )

            logger.info(f"Pipeline creado para cliente {cliente_id}")
            print(f"Pipeline creado para cliente {cliente_id}")
            return pipeline

        except Exception as e:
            logger.error(f"Error creando pipeline: {e}")
            print(f"Error creando pipeline: {e}")
            raise

manejador_streaming = ManejadorStreaming()