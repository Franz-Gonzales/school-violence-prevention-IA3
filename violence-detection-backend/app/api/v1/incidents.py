"""
Endpoints de gestión de incidentes - ACTUALIZADO PARA BASE64
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import obtener_db
from app.core.dependencies import DependenciasComunes
from app.schemas.incident import (
    Incidente, IncidenteCrear, IncidenteActualizar, 
    IncidenteConVideoBase64  # NUEVO SCHEMA
)
from app.services.incident_service import ServicioIncidentes
from app.models.incident import TipoIncidente, SeveridadIncidente, EstadoIncidente
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)
router = APIRouter(prefix="/incidents", tags=["incidentes"])


@router.get("/", response_model=List[Incidente])
async def listar_incidentes(
    estado: Optional[EstadoIncidente] = Query(None, description="Filtrar por estado"),
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


@router.get("/{incidente_id}", response_model=IncidenteConVideoBase64)
async def obtener_incidente_con_video(
    incidente_id: int,
    deps: DependenciasComunes = Depends()
):
    """*** ACTUALIZADO: Obtiene un incidente específico CON VIDEO BASE64 ***"""
    servicio = ServicioIncidentes(deps.db)
    incidente = await servicio.obtener_incidente(incidente_id)
    
    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    print(f"📹 Sirviendo incidente {incidente_id} con Base64")
    
    # Log para debug del Base64
    if incidente.video_base64:
        base64_size = len(incidente.video_base64)
        print(f"🎥 Base64 disponible: {base64_size} caracteres")
        print(f"🎥 Codec: {incidente.video_codec}")
        print(f"🎥 Duración: {incidente.video_duration}s")
        print(f"🎥 Resolución: {incidente.video_resolution}")
    else:
        print(f"⚠️ No hay video Base64 para incidente {incidente_id}")
    
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
    if datos_actualizacion.get("estado") == EstadoIncidente.EN_REVISION:
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
    deps: DependenciasComunes = Depends()
):
    """*** ACTUALIZADO: Finaliza un incidente activo (ya no necesita video_path) ***"""
    servicio = ServicioIncidentes(deps.db)
    
    # Solo necesitamos actualizar el estado, el video ya está en Base64
    incidente = await servicio.actualizar_incidente(
        incidente_id,
        {
            "estado": EstadoIncidente.RESUELTO,
            "fecha_resolucion": datetime.now()
        }
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
async def obtener_info_video_incidente(
    incidente_id: int,
    deps: DependenciasComunes = Depends()
):
    """*** ACTUALIZADO: Obtiene información del video Base64 ***"""
    servicio = ServicioIncidentes(deps.db)
    incidente = await servicio.obtener_incidente(incidente_id)
    
    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    if not incidente.video_base64:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay video disponible para este incidente"
        )
    
    return {
        "has_video": True,
        "video_format": "base64",
        "video_codec": incidente.video_codec or "mp4v",
        "video_duration": float(incidente.video_duration or 0),
        "video_fps": incidente.video_fps or 15,
        "video_resolution": incidente.video_resolution or "640x480",
        "video_file_size": incidente.video_file_size or 0,
        "base64_length": len(incidente.video_base64),
        "base64_size_mb": len(incidente.video_base64) / (1024 * 1024),
        "metadata": incidente.metadata_json
    }


@router.get("/{incidente_id}/video/base64")
async def obtener_video_base64(
    incidente_id: int,
    deps: DependenciasComunes = Depends()
):
    """*** NUEVO: Endpoint específico para obtener solo el Base64 del video ***"""
    servicio = ServicioIncidentes(deps.db)
    incidente = await servicio.obtener_incidente(incidente_id)
    
    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )
    
    if not incidente.video_base64:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay video Base64 disponible para este incidente"
        )
    
    return {
        "video_base64": incidente.video_base64,
        "codec": incidente.video_codec or "mp4v",
        "mime_type": "video/mp4",  # Siempre MP4 después de conversión
        "duration": float(incidente.video_duration or 0),
        "fps": incidente.video_fps or 15,
        "resolution": incidente.video_resolution or "640x480"
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
    """*** CORREGIDO: Manejo optimizado de Base64 grandes ***"""
    try:
        from datetime import datetime
        
        print(f"📝 [INTERNO BASE64] Actualizando incidente {incidente_id}")
        
        # *** VALIDACIÓN DE BASE64 ANTES DE PROCESAR ***
        if 'video_base64' in update_data:
            base64_data = update_data['video_base64']
            base64_size_mb = len(base64_data) / (1024 * 1024)
            
            print(f"🎥 [INTERNO BASE64] Tamaño Base64: {base64_size_mb:.2f} MB")
            
            # Límite preventivo de 50MB
            if base64_size_mb > 50:
                print(f"❌ [INTERNO BASE64] Base64 demasiado grande: {base64_size_mb:.2f} MB")
                return HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Video demasiado grande: {base64_size_mb:.2f} MB. Máximo: 50 MB"
                )
            
            # Validar formato Base64
            try:
                import base64
                decoded_test = base64.b64decode(base64_data[:100])  # Test pequeño
                print(f"✅ [INTERNO BASE64] Formato Base64 válido")
            except Exception as validation_error:
                print(f"❌ [INTERNO BASE64] Base64 inválido: {validation_error}")
                update_data.pop('video_base64')
        
        # *** SEPARAR ACTUALIZACIÓN EN DOS FASES ***
        
        # Fase 1: Campos pequeños
        campos_pequeños = {k: v for k, v in update_data.items() 
                          if k not in ['video_base64']}
        
        # Convertir fecha si es necesario
        if 'fecha_hora_fin' in campos_pequeños and isinstance(campos_pequeños['fecha_hora_fin'], str):
            try:
                campos_pequeños['fecha_hora_fin'] = datetime.fromisoformat(campos_pequeños['fecha_hora_fin'])
            except ValueError:
                campos_pequeños['fecha_hora_fin'] = datetime.now()
        
        # Manejar estado
        if 'estado' in campos_pequeños and isinstance(campos_pequeños['estado'], str):
            from app.models.incident import EstadoIncidente
            try:
                campos_pequeños['estado'] = EstadoIncidente(campos_pequeños['estado'])
            except ValueError:
                campos_pequeños['estado'] = EstadoIncidente.CONFIRMADO
        
        # Actualizar con servicio optimizado
        servicio = ServicioIncidentes(db)
        
        # Actualizar campos pequeños primero
        if campos_pequeños:
            print(f"📝 [INTERNO BASE64] Actualizando campos pequeños: {list(campos_pequeños.keys())}")
            incidente = await servicio.actualizar_incidente(incidente_id, campos_pequeños)
            
            if not incidente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Incidente no encontrado"
                )
        
        # Fase 2: Base64 por separado si existe
        if 'video_base64' in update_data:
            base64_data = update_data['video_base64']
            print(f"🎥 [INTERNO BASE64] Actualizando Base64 por separado...")
            
            try:
                # Actualización SQL directa para Base64
                from sqlalchemy import text
                
                query = text("""
                    UPDATE incidentes 
                    SET video_base64 = :base64_data,
                        fecha_actualizacion = NOW()
                    WHERE id = :incidente_id
                """)
                
                await db.execute(query, {
                    'base64_data': base64_data,
                    'incidente_id': incidente_id
                })
                
                await db.commit()
                print(f"✅ [INTERNO BASE64] Base64 actualizado directamente en BD")
                
            except Exception as base64_error:
                print(f"❌ [INTERNO BASE64] Error con Base64: {base64_error}")
                await db.rollback()
                
                # Continuar sin Base64 pero con éxito en otros campos
                return {
                    "message": "Incidente actualizado parcialmente (sin video Base64)",
                    "incidente_id": incidente_id,
                    "video_format": "error",
                    "error_detail": str(base64_error)
                }
        
        # Respuesta exitosa
        print(f"✅ [INTERNO BASE64] Incidente {incidente_id} actualizado completamente")
        
        return {
            "message": "Incidente actualizado correctamente con Base64",
            "incidente_id": incidente_id,
            "video_format": "base64" if 'video_base64' in update_data else "metadata_only",
            "video_size_mb": len(update_data.get('video_base64', '')) / (1024 * 1024) if 'video_base64' in update_data else 0,
            "campos_actualizados": list(update_data.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [INTERNO BASE64] Error crítico: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )