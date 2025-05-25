"""
Modelo de Notificación
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Enum
import enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TipoNotificacion(enum.Enum):
    """Tipos de notificación"""
    INCIDENTE_VIOLENCIA = "incidente_violencia"
    CAMARA_DESCONECTADA = "camara_desconectada"
    SISTEMA_ERROR = "sistema_error"
    MANTENIMIENTO_REQUERIDO = "mantenimiento_requerido"
    ACTUALIZACION_SISTEMA = "actualizacion_sistema"
    REPORTE_DIARIO = "reporte_diario"

class PrioridadNotificacion(enum.Enum):
    """Prioridades de notificación"""
    BAJA = "baja"
    NORMAL = "normal"
    ALTA = "alta"
    URGENTE = "urgente"

class CanalNotificacion(enum.Enum):
    """Canales de envío"""
    WEB = "web"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class Notificacion(Base):
    """Modelo de notificación del sistema"""
    __tablename__ = "notificaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True)
    tipo_notificacion = Column(Enum(TipoNotificacion), nullable=False)
    canal = Column(Enum(CanalNotificacion), nullable=False)
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    prioridad = Column(Enum(PrioridadNotificacion), default=PrioridadNotificacion.NORMAL, nullable=False)
    estado = Column(String(50), default="pendiente")
    fecha_envio = Column(DateTime(timezone=True), nullable=True)
    fecha_lectura = Column(DateTime(timezone=True), nullable=True)
    intentos_envio = Column(Integer, default=0)
    metadata_json = Column(JSON, nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    incidente = relationship("Incidente", backref="notificaciones")
    usuario = relationship("Usuario", backref="notificaciones")
    
    def __repr__(self):
        return f"<Notificacion {self.id} - {self.tipo_notificacion}>"