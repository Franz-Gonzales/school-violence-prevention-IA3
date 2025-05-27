# app/api/websocket/common.py
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)

class ManejadorWebRTC:
    """Maneja las conexiones WebRTC y señalización"""
    
    def __init__(self):
        self.conexiones: Dict[str, WebSocket] = {}
        self.salas: Dict[int, Set[str]] = {}
        
    async def conectar(self, websocket: WebSocket, cliente_id: str, camara_id: int):
        await websocket.accept()
        self.conexiones[cliente_id] = websocket
        if camara_id not in self.salas:
            self.salas[camara_id] = set()
        self.salas[camara_id].add(cliente_id)
        logger.info(f"Cliente {cliente_id} conectado a cámara {camara_id}")
        print(f"Cliente {cliente_id} conectado a cámara {camara_id}")
        await self.broadcast_a_sala(
            camara_id,
            {
                "tipo": "nuevo_cliente",
                "cliente_id": cliente_id
            },
            excluir=cliente_id
        )
    
    async def desconectar(self, cliente_id: str):
        if cliente_id in self.conexiones:
            del self.conexiones[cliente_id]
        for camara_id, clientes in list(self.salas.items()):
            if cliente_id in clientes:
                clientes.remove(cliente_id)
                if not clientes:
                    del self.salas[camara_id]
                else:
                    await self.broadcast_a_sala(
                        camara_id,
                        {
                            "tipo": "cliente_desconectado",
                            "cliente_id": cliente_id
                        }
                    )
        logger.info(f"Cliente {cliente_id} desconectado")
        print(f"Cliente {cliente_id} desconectado")
    
    async def manejar_mensaje(self, cliente_id: str, mensaje: Dict):
        tipo_mensaje = mensaje.get("tipo")
        logger.info(f"Manejando mensaje de tipo {tipo_mensaje} para cliente {cliente_id}")
        print(f"Manejando mensaje de tipo {tipo_mensaje} para cliente {cliente_id}")
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
            print(f"Tipo de mensaje desconocido: {tipo_mensaje}")
    
    async def _manejar_offer(self, cliente_id: str, mensaje: Dict):
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
        camara_id = mensaje.get("camara_id")
        logger.info(f"Procesando iniciar_stream con camara_id: {camara_id}")
        print(f"Procesando iniciar_stream con camara_id: {camara_id}")
        if camara_id is None:
            logger.error(f"Error: camara_id no especificado en mensaje iniciar_stream: {mensaje}")
            print(f"Error: camara_id no especificado en mensaje iniciar_stream: {mensaje}")
            return
        try:
            camara_id = int(camara_id)  # Asegurarse de que camara_id sea un entero
            await self.broadcast_a_sala(
                camara_id,
                {
                    "tipo": "stream_disponible",
                    "camara_id": camara_id,
                    "streamer_id": cliente_id
                },
                excluir=cliente_id
            )
        except ValueError as e:
            logger.error(f"Error: camara_id no es un entero válido: {camara_id}, mensaje: {mensaje}")
            print(f"Error: camara_id no es un entero válido: {camara_id}, mensaje: {mensaje}")
    
    async def _manejar_detener_stream(self, cliente_id: str, mensaje: Dict):
        camara_id = mensaje.get("camara_id")
        logger.info(f"Procesando detener_stream con camara_id: {camara_id}")
        print(f"Procesando detener_stream con camara_id: {camara_id}")
        if camara_id is None:
            logger.error(f"Error: camara_id no especificado en mensaje detener_stream: {mensaje}")
            print(f"Error: camara_id no especificado en mensaje detener_stream: {mensaje}")
            return
        try:
            camara_id = int(camara_id)
            await self.broadcast_a_sala(
                camara_id,
                {
                    "tipo": "stream_detenido",
                    "camara_id": camara_id
                }
            )
        except ValueError as e:
            logger.error(f"Error: camara_id no es un entero válido: {camara_id}, mensaje: {mensaje}")
            print(f"Error: camara_id no es un entero válido: {camara_id}, mensaje: {mensaje}")
    
    async def enviar_a_cliente(self, cliente_id: str, mensaje: Dict):
        if cliente_id in self.conexiones:
            websocket = self.conexiones[cliente_id]
            try:
                await websocket.send_json(mensaje)
            except Exception as e:
                logger.error(f"Error al enviar mensaje a {cliente_id}: {e}")
                print(f"Error al enviar mensaje a {cliente_id}: {e}")
                await self.desconectar(cliente_id)
    
    async def broadcast_a_sala(self, camara_id: int, mensaje: Dict, excluir: Optional[str] = None):
        if camara_id is None:
            logger.error(f"Error: camara_id es None al intentar broadcast_a_sala, mensaje: {mensaje}")
            print(f"Error: camara_id es None al intentar broadcast_a_sala, mensaje: {mensaje}")
            return
        if camara_id in self.salas:
            logger.info(f"Broadcasting a sala {camara_id} con mensaje: {mensaje}")
            print(f"Broadcasting a sala {camara_id} con mensaje: {mensaje}")
            for cliente_id in self.salas[camara_id]:
                if cliente_id != excluir:
                    await self.enviar_a_cliente(cliente_id, mensaje)
        else:
            logger.warning(f"No hay clientes en la sala {camara_id} para broadcast")
            print(f"No hay clientes en la sala {camara_id} para broadcast")

# Instancia global del manejador
manejador_webrtc = ManejadorWebRTC()