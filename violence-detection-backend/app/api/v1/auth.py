"""
Endpoints de autenticación
"""
from datetime import timedelta, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import obtener_db
from app.core.security import (
    verificar_password,
    crear_token_acceso,
    obtener_hash_password,
    obtener_usuario_actual
)
from app.models.user import Usuario, RolUser  # Importar el Enum RolUser
from app.schemas.user import Usuario as UsuarioSchema, UsuarioCrear, UsuarioLogin
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)
router = APIRouter(prefix="/auth", tags=["autenticación"])


@router.post("/registro", response_model=UsuarioSchema)
async def registrar_usuario(
    usuario_data: UsuarioCrear,
    db: AsyncSession = Depends(obtener_db)
):
    """Registra un nuevo usuario"""
    try:
        # Verificar si el email ya existe
        resultado = await db.execute(
            select(Usuario).where(Usuario.email == usuario_data.email)
        )
        if resultado.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Crear nuevo usuario
        usuario = Usuario(
            nombre_completo=usuario_data.nombre_completo,
            user_name=usuario_data.user_name,
            email=usuario_data.email,
            password_hash=obtener_hash_password(usuario_data.password),
            rol=usuario_data.rol,  # Usar Enum RolUser
            telefono=usuario_data.telefono,
            cargo=usuario_data.cargo,
            activo=usuario_data.activo
        )
        
        db.add(usuario)
        await db.commit()
        await db.refresh(usuario)
        
        print(f"Usuario registrado: {usuario.email}")
        print(f"Usuario registrado: {usuario.email}")
        return usuario
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al registrar usuario: {e}")
        print(f"Error al registrar usuario: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al registrar usuario"
        )


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(obtener_db)
):
    """Inicia sesión y retorna token de acceso"""
    try:
        # Buscar usuario
        resultado = await db.execute(
            select(Usuario).where(Usuario.user_name == form_data.username)
        )
        usuario = resultado.scalars().first()
        
        # Verificar credenciales
        if not usuario or not verificar_password(form_data.password, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verificar si el usuario está activo
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        
        # Actualizar último acceso
        usuario.ultimo_acceso = datetime.now()
        await db.commit()
        
        # Crear token
        access_token_expires = timedelta(minutes=configuracion.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = crear_token_acceso(
            data={
                "sub": str(usuario.id),
                "email": usuario.email,
                "rol": usuario.rol.value  # Convertir Enum a cadena
            },
            expires_delta=access_token_expires
        )
        
        print(f"Usuario {usuario.email} inició sesión")
        print(f"Usuario {usuario.email} inició sesión")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "usuario": {
                "id": usuario.id,
                "email": usuario.email,
                "nombre": usuario.nombre_completo,
                "user_name": usuario.user_name,
                "rol": usuario.rol.value  # Convertir Enum a cadena
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en login: {e}")
        print(f"Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al iniciar sesión"
        )

# Agregar este endpoint después del login

@router.post("/refresh")
async def refresh_token(
    usuario_actual: dict = Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(obtener_db)
):
    """Renueva el token de acceso"""
    try:
        # Crear nuevo token con tiempo extendido
        access_token_expires = timedelta(minutes=configuracion.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = crear_token_acceso(
            data={
                "sub": str(usuario_actual["id"]),
                "email": usuario_actual["email"], 
                "rol": usuario_actual.get("rol", "admin")
            },
            expires_delta=access_token_expires
        )
        
        print(f"Token renovado para usuario {usuario_actual['email']}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": configuracion.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except Exception as e:
        print(f"Error renovando token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al renovar token"
        )

@router.get("/verify")
async def verify_token(
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """Verifica si el token actual es válido"""
    return {
        "valid": True,
        "user_id": usuario_actual["id"],
        "email": usuario_actual["email"],
        "timestamp": datetime.now().isoformat()
    }

@router.get("/perfil", response_model=UsuarioSchema)
async def obtener_perfil(
    usuario_actual: dict = Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(obtener_db)
):
    """Obtiene el perfil del usuario actual"""
    try:
        resultado = await db.execute(
            select(Usuario).where(Usuario.id == int(usuario_actual["id"]))
        )
        usuario = resultado.scalars().first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return usuario
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al obtener perfil: {e}")
        print(f"Error al obtener perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener perfil"
        )


@router.post("/logout")
async def logout(
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """Cierra sesión del usuario"""
    print(f"Usuario {usuario_actual['email']} cerró sesión")
    print(f"Usuario {usuario_actual['email']} cerró sesión")
    return {"mensaje": "Sesión cerrada exitosamente"}


@router.post("/cambiar-password")
async def cambiar_password(
    password_actual: str,
    password_nuevo: str,
    usuario_actual: dict = Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(obtener_db)
):
    """Cambia la contraseña del usuario"""
    try:
        # Obtener usuario
        resultado = await db.execute(
            select(Usuario).where(Usuario.id == int(usuario_actual["id"]))
        )
        usuario = resultado.scalars().first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar contraseña actual
        if not verificar_password(password_actual, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )
        
        # Actualizar contraseña
        usuario.password_hash = obtener_hash_password(password_nuevo)
        await db.commit()
        
        print(f"Usuario {usuario.email} cambió su contraseña")
        print(f"Usuario {usuario.email} cambió su contraseña")
        print(f"Usuario {usuario.user_name} cambió su contraseña")
        return {"mensaje": "Contraseña actualizada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al cambiar contraseña: {e}")
        print(f"Error al cambiar contraseña: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cambiar contraseña"
        )