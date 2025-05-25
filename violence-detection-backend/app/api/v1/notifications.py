"""
Endpoints de notificaciones
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import DependenciasComunes
from app.models.notification import Notificacion, TipoNotificacion, CanalNotificacion, PrioridadNotificacion  # Importar los Enum
from app.schemas.notification import Notificacion as NotificacionSchema
from app.utils.logger import obtener_logger
from datetime import datetime

logger = obtener_logger(__name__)
router = APIRouter(prefix="/notifications", tags=["notificaciones"])


@router.get("/", response_model=List[NotificacionSchema])
async def listar_notificaciones(
    no_leidas: bool = Query(False, description="Solo notificaciones no leídas"),
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    deps: DependenciasComunes = Depends()
):
    """Lista las notificaciones del usuario actual"""
    query = select(Notificacion).where(
        Notificacion.usuario_id == int(deps.usuario_actual["id"])
    )
    
    if no_leidas:
        query = query.where(Notificacion.fecha_lectura.is_(None))
    
    query = query.order_by(Notificacion.fecha_creacion.desc())
    query = query.limit(limite).offset(offset)
    
    resultado = await deps.db.execute(query)
    notificaciones = resultado.scalars().all()
    
    return notificaciones


@router.get("/sin-leer/cantidad")
async def contar_no_leidas(
    deps: DependenciasComunes = Depends()
):
    """Cuenta las notificaciones no leídas del usuario"""
    query = select(Notificacion).where(
        Notificacion.usuario_id == int(deps.usuario_actual["id"]),
        Notificacion.fecha_lectura.is_(None)
    )
    
    resultado = await deps.db.execute(query)
    cantidad = len(resultado.scalars().all())
    
    return {"cantidad": cantidad}


@router.post("/{notificacion_id}/marcar-leida")
async def marcar_como_leida(
    notificacion_id: int,
    deps: DependenciasComunes = Depends()
):
    """Marca una notificación como leída"""
    # Verificar que la notificación pertenece al usuario
    query = select(Notificacion).where(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_id == int(deps.usuario_actual["id"])
    )
    
    resultado = await deps.db.execute(query)
    notificacion = resultado.scalars().first()
    
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    # Marcar como leída
    notificacion.fecha_lectura = datetime.now()
    await deps.db.commit()
    
    return {"mensaje": "Notificación marcada como leída"}


@router.post("/marcar-todas-leidas")
async def marcar_todas_leidas(
    deps: DependenciasComunes = Depends()
):
    """Marca todas las notificaciones del usuario como leídas"""
    stmt = update(Notificacion).where(
        Notificacion.usuario_id == int(deps.usuario_actual["id"]),
        Notificacion.fecha_lectura.is_(None)
    ).values(fecha_lectura=datetime.now())
    
    await deps.db.execute(stmt)
    await deps.db.commit()
    
    return {"mensaje": "Todas las notificaciones marcadas como leídas"}


@router.delete("/{notificacion_id}")
async def eliminar_notificacion(
    notificacion_id: int,
    deps: DependenciasComunes = Depends()
):
    """Elimina una notificación"""
    # Verificar que la notificación pertenece al usuario
    query = select(Notificacion).where(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_id == int(deps.usuario_actual["id"])
    )
    
    resultado = await deps.db.execute(query)
    notificacion = resultado.scalars().first()
    
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    await deps.db.delete(notificacion)
    await deps.db.commit()
    
    return {"mensaje": "Notificación eliminada"}


@router.post("/test")
async def enviar_notificacion_prueba(
    deps: DependenciasComunes = Depends()
):
    """Envía una notificación de prueba al usuario actual"""
    from app.services.notification_service import ServicioNotificaciones
    
    servicio = ServicioNotificaciones(deps.db)
    
    # Crear notificación de prueba
    notificacion = Notificacion(
        usuario_id=int(deps.usuario_actual["id"]),
        tipo_notificacion=TipoNotificacion.ACTUALIZACION_SISTEMA,  # Usar Enum
        canal=CanalNotificacion.WEB,  # Usar Enum
        titulo="Notificación de Prueba",
        mensaje="Esta es una notificación de prueba del sistema",
        prioridad=PrioridadNotificacion.NORMAL,  # Usar Enum
        estado="pendiente"
    )
    
    deps.db.add(notificacion)
    await deps.db.commit()
    
    # Enviar por WebSocket
    from app.api.websocket.notifications_ws import manejador_notificaciones_ws
    await manejador_notificaciones_ws.enviar_a_usuario(
        int(deps.usuario_actual["id"]),
        {
            "tipo": "notificacion",
            "datos": {
                "id": notificacion.id,
                "titulo": notificacion.titulo,
                "mensaje": notificacion.mensaje,
                "timestamp": datetime.now().isoformat()
            }
        }
    )
    
    return {"mensaje": "Notificación de prueba enviada"}