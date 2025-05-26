"""
Servicio de notificaciones
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notificacion, CanalNotificacion, TipoNotificacion, PrioridadNotificacion  # Importar los Enum
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class ServicioNotificaciones:
    """Servicio para gestión de notificaciones"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cola_notificaciones = asyncio.Queue()
        
    async def enviar_notificacion_violencia(
        self,
        camara_id: int,
        ubicacion: str,
        num_personas: int
    ):
        """Envía notificación de violencia detectada"""
        try:
            # Crear notificación en base de datos
            notificacion = Notificacion(
                tipo_notificacion=TipoNotificacion.INCIDENTE_VIOLENCIA,  # Usar Enum
                canal=CanalNotificacion.WEB,  # Usar Enum
                titulo='¡ALERTA! Violencia Detectada',
                mensaje=f'Se detectó violencia en {ubicacion}. {num_personas} personas involucradas.',
                prioridad=PrioridadNotificacion.ALTA,  # Usar Enum
                estado='pendiente',
                metadata_json={
                    'camara_id': camara_id,
                    'ubicacion': ubicacion,
                    'num_personas': num_personas,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            self.db.add(notificacion)
            await self.db.commit()
            
            # Agregar a cola para procesamiento
            await self.cola_notificaciones.put(notificacion)
            
            logger.info(f"Notificación de violencia creada para cámara {camara_id}")
            print(f"Notificación de violencia creada para cámara {camara_id}")
            
        except Exception as e:
            logger.error(f"Error al enviar notificación: {e}")
            print(f"Error al enviar notificación: {e}")
            await self.db.rollback()
    
    async def procesar_cola_notificaciones(self):
        """Procesa la cola de notificaciones pendientes"""
        while True:
            try:
                notificacion = await self.cola_notificaciones.get()
                await self._enviar_notificacion(notificacion)
            except Exception as e:
                logger.error(f"Error procesando cola de notificaciones: {e}")
                print(f"Error procesando cola de notificaciones: {e}")
            
            await asyncio.sleep(0.1)
    
    async def _enviar_notificacion(self, notificacion: Notificacion):
        """Envía una notificación específica"""
        try:
            # Aquí implementarías el envío real según el canal
            if notificacion.canal == CanalNotificacion.WEB:  # Usar Enum
                await self._enviar_web_push(notificacion)
            elif notificacion.canal == CanalNotificacion.EMAIL:  # Usar Enum
                await self._enviar_email(notificacion)
            elif notificacion.canal == CanalNotificacion.SMS:  # Usar Enum
                await self._enviar_sms(notificacion)
            
            # Actualizar estado
            notificacion.estado = 'enviado'
            notificacion.fecha_envio = datetime.now()
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error al enviar notificación {notificacion.id}: {e}")
            print(f"Error al enviar notificación {notificacion.id}: {e}")
            notificacion.intentos_envio += 1
            await self.db.commit()
    
    async def _enviar_web_push(self, notificacion: Notificacion):
        """Envía notificación web push"""
        # Implementar lógica de web push
        logger.info(f"Web push enviado: {notificacion.titulo}")
        print(f"Web push enviado: {notificacion.titulo}")
    
    async def _enviar_email(self, notificacion: Notificacion):
        """Envía notificación por email"""
        # Implementar lógica de email
        logger.info(f"Email enviado: {notificacion.titulo}")
        print(f"Email enviado: {notificacion.titulo}")
    
    async def _enviar_sms(self, notificacion: Notificacion):
        """Envía notificación por SMS"""
        # Implementar lógica de SMS con Twilio
        logger.info(f"SMS enviado: {notificacion.titulo}")
        print(f"SMS enviado: {notificacion.titulo}")
    
    async def marcar_como_leida(self, notificacion_id: int):
        """Marca una notificación como leída"""
        try:
            notificacion = await self.db.get(Notificacion, notificacion_id)
            if notificacion:
                notificacion.fecha_lectura = datetime.now()
                await self.db.commit()
        except Exception as e:
            logger.error(f"Error al marcar notificación como leída: {e}")
            print(f"Error al marcar notificación como leída: {e}")