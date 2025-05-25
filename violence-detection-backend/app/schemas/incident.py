"""
Schemas de Incidente
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, validator
from app.models.incident import TipoIncidente, SeveridadIncidente, EstadoIncidente  # Importar los Enum


class IncidenteBase(BaseModel):
    """Schema base de incidente"""
    tipo_incidente: TipoIncidente  # Usar el Enum TipoIncidente
    severidad: SeveridadIncidente  # Usar el Enum SeveridadIncidente
    ubicacion: Optional[str] = None
    descripcion: Optional[str] = None


class IncidenteCrear(IncidenteBase):
    """Schema para crear incidente"""
    camara_id: int
    probabilidad_violencia: Decimal
    fecha_hora_inicio: datetime
    numero_personas_involucradas: int = 0
    ids_personas_detectadas: Optional[List[str]] = None
    metadata_json: Optional[Dict[str, Any]] = None


class IncidenteActualizar(BaseModel):
    """Schema para actualizar incidente"""
    estado: Optional[EstadoIncidente] = None  # Usar el Enum EstadoIncidente
    atendido_por: Optional[int] = None
    notas_seguimiento: Optional[str] = None
    acciones_tomadas: Optional[str] = None
    fecha_resolucion: Optional[datetime] = None


class Incidente(IncidenteBase):
    """Schema de incidente completo"""
    id: int
    camara_id: Optional[int]
    probabilidad_violencia: Optional[Decimal]
    fecha_hora_inicio: datetime
    fecha_hora_fin: Optional[datetime]
    duracion_segundos: Optional[int]
    numero_personas_involucradas: int
    ids_personas_detectadas: Optional[List[str]]
    video_url: Optional[str]
    video_evidencia_path: Optional[str]
    thumbnail_url: Optional[str]
    estado: EstadoIncidente  # Usar el Enum EstadoIncidente
    atendido_por: Optional[int]
    notas_seguimiento: Optional[str]
    acciones_tomadas: Optional[str]
    fecha_resolucion: Optional[datetime]
    metadata_json: Optional[Dict[str, Any]]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    
    class Config:
        from_attributes = True