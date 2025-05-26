"""
WebSocket para notificaciones en tiempo real
"""
import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from app.utils.logger import obtener_logger
from app.models.incident import TipoIncidente, SeveridadIncidente  # Importar los Enum
from app.models.camera import EstadoCamara  # Importar el Enum

logger = obtener_logger(__name__)


class ManejadorNotificacionesWS:
    """Maneja las conexiones WebSocket para notificaciones"""
    
    def __init__(self):
        # Conexiones activas por usuario
        self.conexiones_usuario: Dict[int, Set[WebSocket]] = {}
        # Cola de notificaciones pendientes
        self.cola_notificaciones = asyncio.Queue()
        
    async def conectar_usuario(
        self,
        websocket: WebSocket,
        usuario_id: int
    ):
        """Conecta un usuario al sistema de notificaciones"""
        await websocket.accept()
        
        # Agregar conexión
        if usuario_id not in self.conexiones_usuario:
            self.conexiones_usuario[usuario_id] = set()
        
        self.conexiones_usuario[usuario_id].add(websocket)
        
        logger.info(f"Usuario {usuario_id} conectado a notificaciones")
        print(f"Usuario {usuario_id} conectado a notificaciones")
        
        # Enviar mensaje de bienvenida
        await self.enviar_a_usuario(
            usuario_id,
            {
                "tipo": "conexion",
                "mensaje": "Conectado al sistema de notificaciones"
            }
        )
    
    async def desconectar_usuario(
        self,
        websocket: WebSocket,
        usuario_id: int
    ):
        """Desconecta un usuario del sistema"""
        if usuario_id in self.conexiones_usuario:
            self.conexiones_usuario[usuario_id].discard(websocket)
            
            # Si no quedan conexiones, eliminar entrada
            if not self.conexiones_usuario[usuario_id]:
                del self.conexiones_usuario[usuario_id]
        
        logger.info(f"Usuario {usuario_id} desconectado de notificaciones")
        print(f"Usuario {usuario_id} desconectado de notificaciones")
    
    async def enviar_a_usuario(
        self,
        usuario_id: int,
        mensaje: Dict
    ):
        """Envía una notificación a un usuario específico"""
        if usuario_id in self.conexiones_usuario:
            # Copia del conjunto para evitar modificación durante iteración
            conexiones = list(self.conexiones_usuario[usuario_id])
            
            for websocket in conexiones:
                try:
                    await websocket.send_json(mensaje)
                except Exception as e:
                    logger.error(f"Error enviando a usuario {usuario_id}: {e}")
                    print(f"Error enviando a usuario {usuario_id}: {e}")
                    # Remover conexión problemática
                    await self.desconectar_usuario(websocket, usuario_id)
    
    async def broadcast_administradores(self, mensaje: Dict):
        """Envía notificación a todos los administradores"""
        # TODO: Implementar lógica para identificar administradores
        # Por ahora enviamos a todos los usuarios conectados
        for usuario_id in list(self.conexiones_usuario.keys()):
            await self.enviar_a_usuario(usuario_id, mensaje)
    
    async def notificar_incidente(
        self,
        incidente_id: int,
        tipo: TipoIncidente,  # Usar Enum
        ubicacion: str,
        severidad: SeveridadIncidente,  # Usar Enum
        detalles: Dict
    ):
        """Notifica sobre un nuevo incidente"""
        mensaje = {
            "tipo": "incidente",
            "datos": {
                "id": incidente_id,
                "tipo_incidente": tipo.value,  # Convertir Enum a cadena
                "ubicacion": ubicacion,
                "severidad": severidad.value,  # Convertir Enum a cadena
                "timestamp": detalles.get("timestamp"),
                "mensaje": f"Incidente detectado en {ubicacion}"
            }
        }
        
        # Enviar a todos los administradores
        await self.broadcast_administradores(mensaje)
    
    async def notificar_cambio_estado_camara(
        self,
        camara_id: int,
        estado: EstadoCamara,  # Usar Enum
        nombre: str
    ):
        """Notifica cambio de estado de cámara"""
        mensaje = {
            "tipo": "estado_camara",
            "datos": {
                "camara_id": camara_id,
                "estado": estado.value,  # Convertir Enum a cadena
                "nombre": nombre,
                "mensaje": f"Cámara {nombre} ahora está {estado.value}"
            }
        }
        
        await self.broadcast_administradores(mensaje)
    
    async def procesar_cola(self):
        """Procesa la cola de notificaciones"""
        while True:
            try:
                notificacion = await self.cola_notificaciones.get()
                
                # Determinar destinatarios
                if notificacion.get("broadcast"):
                    await self.broadcast_administradores(notificacion["mensaje"])
                else:
                    usuario_id = notificacion.get("usuario_id")
                    if usuario_id:
                        await self.enviar_a_usuario(usuario_id, notificacion["mensaje"])
                
            except Exception as e:
                logger.error(f"Error procesando notificación: {e}")
                print(f"Error procesando notificación: {e}")
            
            await asyncio.sleep(0.1)


# Instancia global
manejador_notificaciones_ws = ManejadorNotificacionesWS()


async def websocket_notificaciones(
    websocket: WebSocket,
    usuario_id: int
):
    """Endpoint WebSocket para notificaciones"""
    await manejador_notificaciones_ws.conectar_usuario(websocket, usuario_id)
    
    try:
        while True:
            # Mantener conexión abierta
            # Podríamos recibir comandos del cliente aquí
            data = await websocket.receive_text()
            mensaje = json.loads(data)
            
            # Procesar comandos del cliente si es necesario
            if mensaje.get("tipo") == "ping":
                await websocket.send_json({"tipo": "pong"})
            
    except WebSocketDisconnect:
        await manejador_notificaciones_ws.desconectar_usuario(websocket, usuario_id)
    except Exception as e:
        logger.error(f"Error en WebSocket de notificaciones: {e}")
        print(f"Error en WebSocket de notificaciones: {e}")
        await manejador_notificaciones_ws.desconectar_usuario(websocket, usuario_id)