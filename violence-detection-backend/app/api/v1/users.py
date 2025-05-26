"""
Endpoints de gestión de usuarios
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, or_
from app.core.dependencies import DependenciasComunes, requiere_admin
from app.core.security import obtener_hash_password
from app.models.user import Usuario, RolUser  # Importar el Enum RolUser
from app.schemas.user import Usuario as UsuarioSchema, UsuarioCrear
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)
router = APIRouter(prefix="/users", tags=["usuarios"])


@router.get("/", response_model=List[UsuarioSchema])
async def listar_usuarios(
    activos_solo: bool = Query(True, description="Solo usuarios activos"),
    buscar: Optional[str] = Query(None, description="Buscar por nombre o email"),
    rol: Optional[RolUser] = Query(None, description="Filtrar por rol"),  # Usar Enum
    limite: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Lista todos los usuarios (solo administradores)"""
    query = select(Usuario)
    
    # Aplicar filtros
    condiciones = []
    
    if activos_solo:
        condiciones.append(Usuario.activo == True)
    
    if buscar:
        condiciones.append(
            or_(
                Usuario.nombre_completo.ilike(f"%{buscar}%"),
                Usuario.email.ilike(f"%{buscar}%")
            )
        )
    
    if rol:
        condiciones.append(Usuario.rol == rol)  # Comparar con Enum
    
    if condiciones:
        query = query.where(*condiciones)
    
    query = query.order_by(Usuario.nombre_completo)
    query = query.limit(limite).offset(offset)
    
    resultado = await deps.db.execute(query)
    usuarios = resultado.scalars().all()
    
    return usuarios


@router.get("/{usuario_id}", response_model=UsuarioSchema)
async def obtener_usuario(
    usuario_id: int,
    deps: DependenciasComunes = Depends()
):
    """Obtiene un usuario específico"""
    # Verificar permisos (admin o el mismo usuario)
    if (deps.usuario_actual.get("rol") != RolUser.ADMIN.value and  # Comparar con Enum
        int(deps.usuario_actual["id"]) != usuario_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver este usuario"
        )
    
    resultado = await deps.db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = resultado.scalars().first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return usuario


@router.post("/", response_model=UsuarioSchema)
async def crear_usuario(
    usuario_data: UsuarioCrear,
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Crea un nuevo usuario (solo administradores)"""
    # Verificar si el email ya existe
    resultado = await deps.db.execute(
        select(Usuario).where(Usuario.email == usuario_data.email)
    )
    
    if resultado.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Crear usuario
    usuario = Usuario(
        **usuario_data.model_dump(exclude={"password"}),
        password_hash=obtener_hash_password(usuario_data.password)
    )
    
    deps.db.add(usuario)
    await deps.db.commit()
    await deps.db.refresh(usuario)
    
    logger.info(f"Usuario {usuario.email} creado por admin {deps.usuario_actual['id']}")
    print(f"Usuario {usuario.email} creado por admin {deps.usuario_actual['id']}")
    print(f"Usuario {usuario.user_name} creado por admin {deps.usuario_actual['id']}")
    
    return usuario


@router.patch("/{usuario_id}")
async def actualizar_usuario(
    usuario_id: int,
    actualizacion: Dict[str, Any],
    deps: DependenciasComunes = Depends()
):
    """Actualiza un usuario"""
    # Verificar permisos
    es_admin = deps.usuario_actual.get("rol") == RolUser.ADMIN.value  # Comparar con Enum
    es_mismo_usuario = int(deps.usuario_actual["id"]) == usuario_id
    
    if not es_admin and not es_mismo_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar este usuario"
        )
    
    # Buscar usuario
    resultado = await deps.db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = resultado.scalars().first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Restricciones para usuarios no admin
    if not es_admin:
        # No pueden cambiar su rol o estado activo
        actualizacion.pop("rol", None)
        actualizacion.pop("activo", None)
    
    # Actualizar campos
    for campo, valor in actualizacion.items():
        if hasattr(usuario, campo) and campo != "password":
            setattr(usuario, campo, valor)
    
    await deps.db.commit()
    await deps.db.refresh(usuario)
    
    return usuario


@router.post("/{usuario_id}/activar")
async def activar_usuario(
    usuario_id: int,
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Activa un usuario (solo administradores)"""
    resultado = await deps.db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = resultado.scalars().first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    usuario.activo = True
    await deps.db.commit()
    
    return {"mensaje": "Usuario activado"}


@router.post("/{usuario_id}/desactivar")
async def desactivar_usuario(
    usuario_id: int,
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Desactiva un usuario (solo administradores)"""
    # No permitir desactivarse a sí mismo
    if int(deps.usuario_actual["id"]) == usuario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede desactivarse a sí mismo"
        )
    
    resultado = await deps.db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = resultado.scalars().first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    usuario.activo = False
    await deps.db.commit()
    
    return {"mensaje": "Usuario desactivado"}


@router.delete("/{usuario_id}")
async def eliminar_usuario(
    usuario_id: int,
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Elimina un usuario (solo administradores)"""
    # No permitir eliminarse a sí mismo
    if int(deps.usuario_actual["id"]) == usuario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede eliminarse a sí mismo"
        )
    
    resultado = await deps.db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = resultado.scalars().first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    await deps.db.delete(usuario)
    await deps.db.commit()
    
    logger.info(f"Usuario {usuario_id} eliminado por admin {deps.usuario_actual['id']}")
    print(f"Usuario {usuario_id} eliminado por admin {deps.usuario_actual['id']}")
    
    return {"mensaje": "Usuario eliminado"}