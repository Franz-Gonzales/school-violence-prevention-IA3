# app/api/websocket/rtc_signaling.py
import json
from fastapi import WebSocket, WebSocketDisconnect
from app.utils.logger import obtener_logger
from app.api.websocket.common import manejador_webrtc
from app.api.websocket.stream_handler import manejador_streaming

logger = obtener_logger(__name__)

async def websocket_endpoint(websocket: WebSocket, cliente_id: str, camara_id: int):
    try:
        await manejador_webrtc.conectar(websocket, cliente_id, camara_id)
        logger.info(f"Cliente {cliente_id} conectado para cámara {camara_id}")

        while True:
            data = await websocket.receive_text()
            try:
                mensaje = json.loads(data)
                logger.info(f"Mensaje recibido: {mensaje}")

                if mensaje.get("tipo") == "offer":
                    sdp_answer = await manejador_streaming.manejar_offer(
                        cliente_id,
                        mensaje.get("sdp"),
                        camara_id,
                        manejador_webrtc,
                        mensaje.get("deteccion_activada", False)
                    )
                    
                    if sdp_answer:
                        await manejador_webrtc.enviar_a_cliente(
                            cliente_id,
                            {
                                "tipo": "answer",
                                "sdp": sdp_answer
                            }
                        )
                        logger.info(f"Respuesta SDP enviada a cliente {cliente_id}")
                else:
                    await manejador_webrtc.manejar_mensaje(cliente_id, mensaje)

            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar JSON: {e}")
                continue
            except Exception as e:
                logger.error(f"Error al procesar mensaje: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"Cliente {cliente_id} desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
    finally:
        await manejador_streaming.cerrar_conexion(cliente_id)
        await manejador_webrtc.desconectar(cliente_id)