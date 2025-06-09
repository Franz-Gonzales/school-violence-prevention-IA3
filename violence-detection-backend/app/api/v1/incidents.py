"""
Endpoints de gestión de incidentes  
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import obtener_db
from app.core.dependencies import DependenciasComunes
from app.schemas.incident import Incidente, IncidenteCrear, IncidenteActualizar
from app.services.incident_service import ServicioIncidentes
from app.models.incident import TipoIncidente, SeveridadIncidente, EstadoIncidente  # Importar los Enum
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)
router = APIRouter(prefix="/incidents", tags=["incidentes"])


@router.get("/", response_model=List[Incidente])
async def listar_incidentes(
    estado: Optional[EstadoIncidente] = Query(None, description="Filtrar por estado"),  # Usar Enum
    camara_id: Optional[int] = Query(None, description="Filtrar por cámara"),
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin"),
    limite: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    deps: DependenciasComunes = Depends()
):
    """Lista incidentes con filtros opcionales"""
    servicio = ServicioIncidentes(deps.db)
    return await servicio.listar_incidentes(
        limite=limite,
        offset=offset,
        estado=estado,
        camara_id=camara_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )


@router.get("/estadisticas")
async def obtener_estadisticas(
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin: Optional[datetime] = Query(None),
    deps: DependenciasComunes = Depends()
):
    """Obtiene estadísticas de incidentes"""
    servicio = ServicioIncidentes(deps.db)
    return await servicio.obtener_estadisticas(fecha_inicio, fecha_fin)


@router.get("/{incidente_id}", response_model=Incidente)
async def obtener_incidente(
    incidente_id: int,
    deps: DependenciasComunes = Depends()
):
    """Obtiene un incidente específico"""
    servicio = ServicioIncidentes(deps.db)
    incidente = await servicio.obtener_incidente(incidente_id)
    
    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    return incidente


@router.post("/", response_model=Incidente)
async def crear_incidente(
    incidente_data: IncidenteCrear,
    deps: DependenciasComunes = Depends()
):
    """Crea un nuevo incidente"""
    servicio = ServicioIncidentes(deps.db)
    
    try:
        incidente = await servicio.crear_incidente(incidente_data.model_dump())
        
        # Notificar sobre nuevo incidente
        from app.api.websocket.notifications_ws import manejador_notificaciones_ws
        await manejador_notificaciones_ws.notificar_incidente(
            incidente.id,
            incidente.tipo_incidente,
            incidente.ubicacion or "Sin ubicación",
            incidente.severidad,
            {
                "timestamp": incidente.fecha_hora_inicio.isoformat(),
                "personas_involucradas": incidente.numero_personas_involucradas
            }
        )
        
        return incidente
        
    except Exception as e:
        logger.error(f"Error al crear incidente: {e}")
        print(f"Error al crear incidente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear incidente"
        )


@router.patch("/{incidente_id}", response_model=Incidente)
async def actualizar_incidente(
    incidente_id: int,
    actualizacion: IncidenteActualizar,
    deps: DependenciasComunes = Depends()
):
    """Actualiza un incidente"""
    servicio = ServicioIncidentes(deps.db)
    
    # Si se está atendiendo, asignar usuario actual
    datos_actualizacion = actualizacion.model_dump(exclude_unset=True)
    if datos_actualizacion.get("estado") == EstadoIncidente.EN_REVISION:  # Usar Enum
        datos_actualizacion["atendido_por"] = deps.usuario_actual["id"]
    
    incidente = await servicio.actualizar_incidente(
        incidente_id,
        datos_actualizacion
    )
    
    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    return incidente


@router.post("/{incidente_id}/finalizar")
async def finalizar_incidente(
    incidente_id: int,
    video_path: Optional[str] = None,
    thumbnail_path: Optional[str] = None,
    deps: DependenciasComunes = Depends()
):
    """Finaliza un incidente activo"""
    servicio = ServicioIncidentes(deps.db)
    
    incidente = await servicio.finalizar_incidente(
        incidente_id,
        video_path,
        thumbnail_path
    )
    
    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    return {
        "mensaje": "Incidente finalizado",
        "incidente": incidente
    }


@router.get("/{incidente_id}/video")
async def obtener_video_incidente(
    incidente_id: int,
    deps: DependenciasComunes = Depends()
):
    """Obtiene la URL del video de evidencia"""
    servicio = ServicioIncidentes(deps.db)
    incidente = await servicio.obtener_incidente(incidente_id)
    
    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    if not incidente.video_evidencia_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay video disponible para este incidente"
        )
    
    # TODO: Implementar servicio de archivos para servir el video
    return {
        "video_url": f"/api/v1/files/videos/{incidente_id}",
        "thumbnail_url": incidente.thumbnail_url
    }


@router.delete("/{incidente_id}")
async def eliminar_incidente(
    incidente_id: int,
    deps: DependenciasComunes = Depends()
):
    """Elimina un incidente (solo administradores)"""
    from app.core.dependencies import requiere_admin
    await requiere_admin()(deps.usuario_actual)
    
    servicio = ServicioIncidentes(deps.db)
    incidente = await servicio.obtener_incidente(incidente_id)
    
    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    try:
        await deps.db.delete(incidente)
        await deps.db.commit()
        
        logger.info(f"Incidente {incidente_id} eliminado por usuario {deps.usuario_actual['id']}")
        print(f"Incidente {incidente_id} eliminado por usuario {deps.usuario_actual['id']}")
        return {"mensaje": "Incidente eliminado exitosamente"}
        
    except Exception as e:
        logger.error(f"Error al eliminar incidente: {e}")
        print(f"Error al eliminar incidente: {e}")
        await deps.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar incidente"
        )


@router.patch("/{incidente_id}/internal", include_in_schema=False)
async def actualizar_incidente_interno(
    incidente_id: int,
    update_data: Dict[str, Any],
    db: AsyncSession = Depends(obtener_db)
):
    """
    MEJORADO: Actualiza un incidente internamente desde el pipeline
    Este endpoint es usado exclusivamente por el sistema interno
    """
    try:
        from datetime import datetime
        
        print(f"📝 [INTERNO] Actualizando incidente {incidente_id}")
        print(f"📝 [INTERNO] Datos recibidos: {list(update_data.keys())}")
        
        # Convertir strings de fecha de vuelta a datetime si es necesario
        if 'fecha_hora_fin' in update_data and isinstance(update_data['fecha_hora_fin'], str):
            try:
                update_data['fecha_hora_fin'] = datetime.fromisoformat(update_data['fecha_hora_fin'])
                print(f"📝 [INTERNO] Fecha convertida: {update_data['fecha_hora_fin']}")
            except ValueError as e:
                logger.error(f"Error parsing fecha_hora_fin: {e}")
                update_data['fecha_hora_fin'] = datetime.now()
        
        # Manejar estado correctamente
        if 'estado' in update_data:
            if isinstance(update_data['estado'], str):
                from app.models.incident import EstadoIncidente
                try:
                    update_data['estado'] = EstadoIncidente(update_data['estado'])
                    print(f"📝 [INTERNO] Estado convertido: {update_data['estado']}")
                except ValueError:
                    update_data['estado'] = EstadoIncidente.CONFIRMADO
            print(f"📝 [INTERNO] Estado final: {update_data['estado']}")
        
        # Log de los campos más importantes
        if 'video_url' in update_data:
            print(f"🔗 [INTERNO] URL del video: {update_data['video_url']}")
        if 'video_evidencia_path' in update_data:
            print(f"📂 [INTERNO] Ruta del archivo: {update_data['video_evidencia_path']}")
        
        # Actualizar usando el servicio
        servicio = ServicioIncidentes(db)
        incidente = await servicio.actualizar_incidente(incidente_id, update_data)
        
        if not incidente:
            print(f"❌ [INTERNO] Incidente {incidente_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incidente no encontrado"
            )
        
        print(f"✅ [INTERNO] Incidente {incidente_id} actualizado correctamente")
        print(f"✅ [INTERNO] video_url guardado: {incidente.video_url}")
        print(f"✅ [INTERNO] video_evidencia_path guardado: {incidente.video_evidencia_path}")
        
        return {
            "message": "Incidente actualizado correctamente", 
            "incidente_id": incidente_id,
            "video_url": incidente.video_url,
            "video_path": incidente.video_evidencia_path,
            "estado": incidente.estado.value if incidente.estado else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [INTERNO] Error en actualización: {e}")
        print(f"❌ [INTERNO] Error en actualización: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en actualización"
        )