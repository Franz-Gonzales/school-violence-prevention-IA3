"""
Modelo de Cámara
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class EstadoCamara(enum.Enum):
    """Estados posibles de una cámara"""
    ACTIVA = "activa"
    INACTIVA = "inactiva"
    MANTENIMIENTO = "mantenimiento"
    ERROR = "error"

class TipoCamara(enum.Enum):
    """Tipos de cámara soportados"""
    USB = "usb"
    IP = "ip"
    RTSP = "rtsp"

class Camara(Base):
    """Modelo de cámara del sistema"""
    __tablename__ = "camaras"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    url_conexion = Column(String(255), nullable=True)
    tipo_camara = Column(Enum(TipoCamara), default=TipoCamara.USB, nullable=False)
    resolucion_ancho = Column(Integer, default=1280)
    resolucion_alto = Column(Integer, default=720)
    fps = Column(Integer, default=15)
    estado = Column(Enum(EstadoCamara), default=EstadoCamara.INACTIVA, nullable=False)
    configuracion_json = Column(JSON, nullable=True)
    fecha_instalacion = Column(DateTime(timezone=True), nullable=True)
    ultima_actividad = Column(DateTime(timezone=True), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Camara {self.nombre} - {self.ubicacion}>"