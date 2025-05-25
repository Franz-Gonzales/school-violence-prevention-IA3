"""
Schemas de Usuario
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from app.models.user import RolUser  # Importar el Enum RolUser


class UsuarioBase(BaseModel):
    """Schema base de usuario"""
    nombre_completo: str
    email: EmailStr
    rol: RolUser = RolUser.OPERADOR  # Usar el Enum RolUser
    telefono: Optional[str] = None
    cargo: Optional[str] = None
    activo: bool = True


class UsuarioCrear(UsuarioBase):
    """Schema para crear usuario"""
    password: str
    
    @validator('password')
    def validar_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v


class UsuarioLogin(BaseModel):
    """Schema para login"""
    email: EmailStr
    password: str


class Usuario(UsuarioBase):
    """Schema de usuario completo"""
    id: int
    ultimo_acceso: Optional[datetime]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    
    class Config:
        from_attributes = True