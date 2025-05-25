"""
Modelo de Incidente
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, DECIMAL, ARRAY, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
from sqlalchemy.orm import relationship
from app.core.database import Base


class TipoIncidente(enum.Enum):
    """Tipos de incidente detectados"""
    PELEA = "pelea"
    VIOLENCIA_FISICA = "violencia_fisica"
    MULTITUD_AGRESIVA = "multitud_agresiva"

class SeveridadIncidente(enum.Enum):
    """Niveles de severidad"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class EstadoIncidente(enum.Enum):
    """Estados de procesamiento del incidente"""
    NUEVO = "nuevo"
    EN_REVISION = "en_revision"
    CONFIRMADO = "confirmado"
    FALSO_POSITIVO = "falso_positivo"
    RESUELTO = "resuelto"
    ARCHIVADO = "archivado"


class Incidente(Base):
    """Modelo de incidente detectado"""
    __tablename__ = "incidentes"
    
    id = Column(Integer, primary_key=True, index=True)
    camara_id = Column(Integer, ForeignKey("camaras.id", ondelete="SET NULL"), nullable=True)
    tipo_incidente = Column(Enum(TipoIncidente), nullable=False)
    severidad = Column(Enum(SeveridadIncidente), nullable=False)
    probabilidad_violencia = Column(DECIMAL(5, 2), nullable=True)
    fecha_hora_inicio = Column(DateTime(timezone=True), nullable=False, index=True)
    fecha_hora_fin = Column(DateTime(timezone=True), nullable=True)
    duracion_segundos = Column(Integer, nullable=True)
    ubicacion = Column(String(200), nullable=True)
    descripcion = Column(Text, nullable=True)
    numero_personas_involucradas = Column(Integer, default=0)
    ids_personas_detectadas = Column(ARRAY(String), nullable=True)
    video_url = Column(String(500), nullable=True)
    video_evidencia_path = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    estado = Column(Enum(EstadoIncidente), default=EstadoIncidente.NUEVO, index=True)
    atendido_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    notas_seguimiento = Column(Text, nullable=True)
    acciones_tomadas = Column(Text, nullable=True)
    fecha_resolucion = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    camara = relationship("Camara", backref="incidentes")
    usuario_atencion = relationship("Usuario", backref="incidentes_atendidos")
    
    def __repr__(self):
        return f"<Incidente {self.id} - {self.tipo_incidente}>"