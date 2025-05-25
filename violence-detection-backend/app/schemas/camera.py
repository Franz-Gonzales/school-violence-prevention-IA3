"""
Schemas de Cámara
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator
from app.models.camera import TipoCamara, EstadoCamara  # Importar los Enum


class CamaraBase(BaseModel):
    """Schema base de cámara"""
    nombre: str
    ubicacion: str
    descripcion: Optional[str] = None
    tipo_camara: TipoCamara = TipoCamara.USB  # Usar el Enum TipoCamara
    resolucion_ancho: int = 1280
    resolucion_alto: int = 720
    fps: int = 15

    @validator('fps')
    def validar_fps(cls, v):
        if v < 1 or v > 60:
            raise ValueError('FPS debe estar entre 1 y 60')
        return v


class CamaraCrear(CamaraBase):
    """Schema para crear cámara"""
    url_conexion: Optional[str] = None
    configuracion_json: Optional[Dict[str, Any]] = None


class CamaraActualizar(BaseModel):
    """Schema para actualizar cámara"""
    nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[EstadoCamara] = None  # Usar el Enum EstadoCamara
    configuracion_json: Optional[Dict[str, Any]] = None


class Camara(CamaraBase):
    """Schema de cámara completo"""
    id: int
    url_conexion: Optional[str]
    estado: EstadoCamara = EstadoCamara.INACTIVA  # Usar el Enum EstadoCamara
    configuracion_json: Optional[Dict[str, Any]]
    fecha_instalacion: Optional[datetime]
    ultima_actividad: Optional[datetime]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    
    class Config:
        from_attributes = True