"""
Schemas de Incidente - ACTUALIZADO para Base64
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, validator
from app.models.incident import TipoIncidente, SeveridadIncidente, EstadoIncidente


class IncidenteBase(BaseModel):
    """Schema base de incidente"""
    tipo_incidente: TipoIncidente
    severidad: SeveridadIncidente
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
    estado: Optional[EstadoIncidente] = None
    atendido_por: Optional[int] = None
    notas_seguimiento: Optional[str] = None
    acciones_tomadas: Optional[str] = None
    fecha_resolucion: Optional[datetime] = None
    
    # *** NUEVOS CAMPOS PARA BASE64 ***
    video_base64: Optional[str] = None
    video_file_size: Optional[int] = None
    video_duration: Optional[Decimal] = None
    video_codec: Optional[str] = None
    video_fps: Optional[int] = None
    video_resolution: Optional[str] = None


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
    
    # *** CAMPOS BASE64 ***
    video_base64: Optional[str]
    video_file_size: Optional[int]
    video_duration: Optional[Decimal]
    video_codec: Optional[str]
    video_fps: Optional[int]
    video_resolution: Optional[str]
    
    # *** CAMPOS DEPRECATED (mantener por compatibilidad) ***
    video_url: Optional[str]
    video_evidencia_path: Optional[str]
    thumbnail_url: Optional[str]
    
    estado: EstadoIncidente
    atendido_por: Optional[int]
    notas_seguimiento: Optional[str]
    acciones_tomadas: Optional[str]
    fecha_resolucion: Optional[datetime]
    metadata_json: Optional[Dict[str, Any]]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    
    class Config:
        from_attributes = True


class IncidenteConVideoBase64(BaseModel):
    """Schema específico para obtener incidente con video Base64"""
    id: int
    tipo_incidente: TipoIncidente
    severidad: SeveridadIncidente
    fecha_hora_inicio: datetime
    ubicacion: Optional[str]
    descripcion: Optional[str]
    probabilidad_violencia: Optional[Decimal]
    numero_personas_involucradas: int
    video_base64: Optional[str]
    video_file_size: Optional[int]
    video_duration: Optional[Decimal]
    video_codec: Optional[str]
    video_fps: Optional[int]
    video_resolution: Optional[str]
    estado: EstadoIncidente
    metadata_json: Optional[Dict[str, Any]]
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True