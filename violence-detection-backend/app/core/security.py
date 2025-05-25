"""
Funciones de seguridad y autenticación
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import configuracion
from app.core.database import obtener_db

# Contexto para hash de contraseñas
contexto_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def verificar_password(password_plano: str, password_hash: str) -> bool:
    """Verifica si la contraseña coincide con el hash"""
    return contexto_pwd.verify(password_plano, password_hash)


def obtener_hash_password(password: str) -> str:
    """Genera el hash de una contraseña"""
    return contexto_pwd.hash(password)


def crear_token_acceso(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        configuracion.SECRET_KEY, 
        algorithm=configuracion.ALGORITHM
    )
    
    return encoded_jwt


async def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(obtener_db)
) -> dict:
    """Obtiene el usuario actual desde el token"""
    credenciales_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            configuracion.SECRET_KEY, 
            algorithms=[configuracion.ALGORITHM]
        )
        usuario_id: str = payload.get("sub")
        
        if usuario_id is None:
            raise credenciales_exception
            
    except JWTError:
        raise credenciales_exception
    
    # Aquí deberías buscar el usuario en la base de datos
    # Por ahora retornamos un usuario de ejemplo
    return {"id": usuario_id, "email": payload.get("email")}


def verificar_rol(rol_requerido: str):
    """Decorador para verificar roles de usuario"""
    async def verificador_rol(
        usuario_actual: dict = Depends(obtener_usuario_actual)
    ):
        if usuario_actual.get("rol") != rol_requerido:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes"
            )
        return usuario_actual
    
    return verificador_rol