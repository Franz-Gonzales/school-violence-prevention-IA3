"""
Modelo de Configuración del Sistema
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ARRAY, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class TipoDato(enum.Enum):
    """Tipos de datos permitidos"""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    JSON = "json"
    FLOAT = "float"

class Categoria(enum.Enum):
    """Categorías de configuración"""
    AI = "ia"
    VIDEO = "video"
    ALMACENAMIENTO = "almacenamiento"
    NOTIFICACIONES = "notificaciones"
    ALARMA = "alarma"


class ConfiguracionSistema(Base):
    """Modelo de configuración del sistema"""
    __tablename__ = "configuracion_sistema"
    
    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(100), unique=True, nullable=False, index=True)
    valor = Column(Text, nullable=False)
    tipo_dato = Column(Enum(TipoDato), nullable=False)
    categoria = Column(Enum(Categoria), nullable=True)
    descripcion = Column(Text, nullable=True)
    es_sensible = Column(Boolean, default=False)
    modificable_por_usuario = Column(Boolean, default=True)
    valor_por_defecto = Column(Text, nullable=True)
    opciones_validas = Column(ARRAY(String), nullable=True)
    ultima_modificacion_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relación
    usuario_modificacion = relationship("Usuario", backref="configuraciones_modificadas")
    
    def __repr__(self):
        return f"<ConfiguracionSistema {self.clave}={self.valor}>"