"""
Señalización WebRTC para streaming de video
"""
import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class ManejadorWebRTC:
    """Maneja las conexiones WebRTC y señalización"""
    
    def __init__(self):
        # Almacenar conexiones activas
        self.conexiones: Dict[str, WebSocket] = {}
        # Salas de streaming por cámara
        self.salas: Dict[int, Set[str]] = {}
        
    async def conectar(
        self,
        websocket: WebSocket,
        cliente_id: str,
        camara_id: int
    ):
        """Acepta una nueva conexión WebRTC"""
        await websocket.accept()
        
        # Almacenar conexión
        self.conexiones[cliente_id] = websocket
        
        # Agregar a sala de cámara
        if camara_id not in self.salas:
            self.salas[camara_id] = set()
        self.salas[camara_id].add(cliente_id)
        
        logger.info(f"Cliente {cliente_id} conectado a cámara {camara_id}")
        print(f"Cliente {cliente_id} conectado a cámara {camara_id}")
        
        # Notificar a otros clientes en la sala
        await self.broadcast_a_sala(
            camara_id,
            {
                "tipo": "nuevo_cliente",
                "cliente_id": cliente_id
            },
            excluir=cliente_id
        )
    
    async def desconectar(self, cliente_id: str):
        """Maneja la desconexión de un cliente"""
        if cliente_id in self.conexiones:
            del self.conexiones[cliente_id]
        
        # Remover de todas las salas
        for camara_id, clientes in self.salas.items():
            if cliente_id in clientes:
                clientes.remove(cliente_id)
                
                # Notificar a otros clientes
                await self.broadcast_a_sala(
                    camara_id,
                    {
                        "tipo": "cliente_desconectado",
                        "cliente_id": cliente_id
                    }
                )
        
        logger.info(f"Cliente {cliente_id} desconectado")
        print(f"Cliente {cliente_id} desconectado")
    
    async def manejar_mensaje(
        self,
        cliente_id: str,
        mensaje: Dict
    ):
        """Maneja mensajes de señalización WebRTC"""
        tipo_mensaje = mensaje.get("tipo")
        
        if tipo_mensaje == "offer":
            await self._manejar_offer(cliente_id, mensaje)
        elif tipo_mensaje == "answer":
            await self._manejar_answer(cliente_id, mensaje)
        elif tipo_mensaje == "ice_candidate":
            await self._manejar_ice_candidate(cliente_id, mensaje)
        elif tipo_mensaje == "iniciar_stream":
            await self._manejar_iniciar_stream(cliente_id, mensaje)
        elif tipo_mensaje == "detener_stream":
            await self._manejar_detener_stream(cliente_id, mensaje)
        else:
            logger.warning(f"Tipo de mensaje desconocido: {tipo_mensaje}")
    
    async def _manejar_offer(self, cliente_id: str, mensaje: Dict):
        """Maneja ofertas SDP"""
        destino_id = mensaje.get("destino_id")
        if destino_id and destino_id in self.conexiones:
            await self.enviar_a_cliente(
                destino_id,
                {
                    "tipo": "offer",
                    "origen_id": cliente_id,
                    "sdp": mensaje.get("sdp")
                }
            )
    
    async def _manejar_answer(self, cliente_id: str, mensaje: Dict):
        """Maneja respuestas SDP"""
        destino_id = mensaje.get("destino_id")
        if destino_id and destino_id in self.conexiones:
            await self.enviar_a_cliente(
                destino_id,
                {
                    "tipo": "answer",
                    "origen_id": cliente_id,
                    "sdp": mensaje.get("sdp")
                }
            )
    
    async def _manejar_ice_candidate(self, cliente_id: str, mensaje: Dict):
        """Maneja candidatos ICE"""
        destino_id = mensaje.get("destino_id")
        if destino_id and destino_id in self.conexiones:
            await self.enviar_a_cliente(
                destino_id,
                {
                    "tipo": "ice_candidate",
                    "origen_id": cliente_id,
                    "candidate": mensaje.get("candidate")
                }
            )
    
    async def _manejar_iniciar_stream(self, cliente_id: str, mensaje: Dict):
        """Maneja solicitud de inicio de streaming"""
        camara_id = mensaje.get("camara_id")
        
        # Notificar que el streaming está disponible
        await self.broadcast_a_sala(
            camara_id,
            {
                "tipo": "stream_disponible",
                "camara_id": camara_id,
                "streamer_id": cliente_id
            },
            excluir=cliente_id
        )
    
    async def _manejar_detener_stream(self, cliente_id: str, mensaje: Dict):
        """Maneja solicitud de detención de streaming"""
        camara_id = mensaje.get("camara_id")
        
        # Notificar que el streaming se detuvo
        await self.broadcast_a_sala(
            camara_id,
            {
                "tipo": "stream_detenido",
                "camara_id": camara_id
            }
        )
    
    async def enviar_a_cliente(
        self,
        cliente_id: str,
        mensaje: Dict
    ):
        """Envía un mensaje a un cliente específico"""
        if cliente_id in self.conexiones:
            websocket = self.conexiones[cliente_id]
            try:
                await websocket.send_json(mensaje)
            except Exception as e:
                logger.error(f"Error al enviar mensaje a {cliente_id}: {e}")
                print(f"Error al enviar mensaje a {cliente_id}: {e}")
                await self.desconectar(cliente_id)
    
    async def broadcast_a_sala(
        self,
        camara_id: int,
        mensaje: Dict,
        excluir: Optional[str] = None
    ):
        """Envía un mensaje a todos los clientes en una sala"""
        if camara_id in self.salas:
            for cliente_id in self.salas[camara_id]:
                if cliente_id != excluir:
                    await self.enviar_a_cliente(cliente_id, mensaje)


# Instancia global del manejador
manejador_webrtc = ManejadorWebRTC()


async def websocket_endpoint(
    websocket: WebSocket,
    cliente_id: str,
    camara_id: int
):
    """Endpoint principal de WebSocket para WebRTC"""
    await manejador_webrtc.conectar(websocket, cliente_id, camara_id)
    
    try:
        while True:
            # Recibir mensajes del cliente
            data = await websocket.receive_text()
            mensaje = json.loads(data)
            
            # Procesar mensaje
            await manejador_webrtc.manejar_mensaje(cliente_id, mensaje)
            
    except WebSocketDisconnect:
        await manejador_webrtc.desconectar(cliente_id)
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
        print(f"Error en WebSocket: {e}")
        await manejador_webrtc.desconectar(cliente_id)