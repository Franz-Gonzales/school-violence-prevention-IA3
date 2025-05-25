"""
Schemas de Notificación
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from app.models.notification import TipoNotificacion, CanalNotificacion, PrioridadNotificacion  # Importar los Enum


class NotificacionBase(BaseModel):
    """Schema base de notificación"""
    tipo_notificacion: TipoNotificacion  # Usar el Enum TipoNotificacion
    canal: CanalNotificacion  # Usar el Enum CanalNotificacion
    titulo: str
    mensaje: str
    prioridad: PrioridadNotificacion = PrioridadNotificacion.NORMAL  # Usar el Enum PrioridadNotificacion


class NotificacionCrear(NotificacionBase):
    """Schema para crear notificación"""
    incidente_id: Optional[int] = None
    usuario_id: int
    metadata_json: Optional[Dict[str, Any]] = None


class NotificacionActualizar(BaseModel):
    """Schema para actualizar notificación"""
    estado: Optional[str] = None
    fecha_envio: Optional[datetime] = None
    fecha_lectura: Optional[datetime] = None
    intentos_envio: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None


class Notificacion(NotificacionBase):
    """Schema de notificación completo"""
    id: int
    incidente_id: Optional[int]
    usuario_id: int
    estado: str
    fecha_envio: Optional[datetime]
    fecha_lectura: Optional[datetime]
    intentos_envio: int
    metadata_json: Optional[Dict[str, Any]]
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True