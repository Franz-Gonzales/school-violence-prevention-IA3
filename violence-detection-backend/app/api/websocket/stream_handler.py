"""
Manejador de streaming de video
"""
import cv2
import asyncio
import numpy as np
from typing import Optional, Dict, Any
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer
from app.ai.model_loader import cargador_modelos
from app.ai.pipeline import PipelineDeteccion
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class VideoTrackProcesado(VideoStreamTrack):
    """Track de video procesado con IA"""
    
    def __init__(self, source: str, pipeline: PipelineDeteccion):
        super().__init__()
        self.source = source
        self.pipeline = pipeline
        self.cap = None
        
    async def recv(self):
        """Recibe y procesa el siguiente frame"""
        pts, time_base = await self.next_timestamp()
        
        # Abrir cámara si no está abierta
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.source)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, configuracion.DEFAULT_RESOLUTION[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, configuracion.DEFAULT_RESOLUTION[1])
            self.cap.set(cv2.CAP_PROP_FPS, configuracion.DEFAULT_FPS)
        
        # Leer frame
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Procesar frame con pipeline de IA
        resultado = await self.pipeline.procesar_frame(
            frame,
            camara_id=1,  # TODO: Obtener ID real
            ubicacion="Principal"  # TODO: Obtener ubicación real
        )
        
        # Obtener frame procesado
        frame_procesado = resultado.get('frame_procesado', frame)
        
        # Convertir a formato compatible con WebRTC
        from av import VideoFrame
        video_frame = VideoFrame.from_ndarray(frame_procesado, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        
        return video_frame


class ManejadorStreaming:
    """Maneja el streaming de video con procesamiento IA"""
    
    def __init__(self):
        self.conexiones_peer: Dict[str, RTCPeerConnection] = {}
        self.pipelines: Dict[str, PipelineDeteccion] = {}
        
    async def crear_conexion_peer(
        self,
        cliente_id: str,
        camara_id: int
    ) -> RTCPeerConnection:
        """Crea una nueva conexión peer"""
        pc = RTCPeerConnection()
        self.conexiones_peer[cliente_id] = pc
        
        # Crear pipeline de detección si no existe
        if cliente_id not in self.pipelines:
            # Cargar modelos necesarios
            from app.ai.yolo_detector import DetectorPersonas
            from app.ai.deep_sort_tracker import TrackerPersonas
            from app.ai.violence_detector import DetectorViolencia
            from app.services.alarm_service import ServicioAlarma
            from app.services.notification_service import ServicioNotificaciones
            from app.services.incident_service import ServicioIncidentes
            
            # Inicializar componentes
            detector_personas = DetectorPersonas(
                cargador_modelos.obtener_modelo('yolo')
            )
            tracker_personas = TrackerPersonas()
            detector_violencia = DetectorViolencia(
                cargador_modelos.obtener_modelo('timesformer')
            )
            
            # TODO: Inyectar servicios reales
            servicio_alarma = ServicioAlarma()
            servicio_notificaciones = None  # Necesita DB
            servicio_incidentes = None  # Necesita DB
            
            # Crear pipeline
            pipeline = PipelineDeteccion(
                detector_personas,
                tracker_personas,
                detector_violencia,
                servicio_alarma,
                servicio_notificaciones,
                servicio_incidentes
            )
            
            self.pipelines[cliente_id] = pipeline
        
        # Agregar track de video
        if camara_id == 0:  # Cámara USB local
            video_track = VideoTrackProcesado(
                source=0,  # Índice de cámara USB
                pipeline=self.pipelines[cliente_id]
            )
            pc.addTrack(video_track)
        
        # Configurar eventos
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Estado de conexión {cliente_id}: {pc.connectionState}")
            if pc.connectionState == "failed":
                await self.cerrar_conexion(cliente_id)
        
        return pc
    
    async def manejar_offer(
        self,
        cliente_id: str,
        sdp: str,
        camara_id: int
    ) -> str:
        """Maneja una oferta SDP y retorna respuesta"""
        # Crear conexión peer si no existe
        if cliente_id not in self.conexiones_peer:
            pc = await self.crear_conexion_peer(cliente_id, camara_id)
        else:
            pc = self.conexiones_peer[cliente_id]
        
        # Establecer descripción remota
        offer = RTCSessionDescription(sdp=sdp, type="offer")
        await pc.setRemoteDescription(offer)
        
        # Crear respuesta
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        return pc.localDescription.sdp
    
    async def manejar_ice_candidate(
        self,
        cliente_id: str,
        candidate: Dict[str, Any]
    ):
        """Maneja un candidato ICE"""
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
    
    async def cerrar_conexion(self, cliente_id: str):
        """Cierra una conexión peer"""
        if cliente_id in self.conexiones_peer:
            pc = self.conexiones_peer[cliente_id]
            await pc.close()
            del self.conexiones_peer[cliente_id]
        
        if cliente_id in self.pipelines:
            self.pipelines[cliente_id].reiniciar()
            del self.pipelines[cliente_id]
        
        logger.info(f"Conexión cerrada para cliente {cliente_id}")
    
    def obtener_estadisticas_stream(self, cliente_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene estadísticas del stream"""
        if cliente_id in self.pipelines:
            return self.pipelines[cliente_id].obtener_estadisticas()
        return None


# Instancia global del manejador
manejador_streaming = ManejadorStreaming()