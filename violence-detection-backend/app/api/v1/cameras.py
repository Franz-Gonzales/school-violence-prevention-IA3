"""
Endpoints de gestión de cámaras
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import obtener_db
from app.core.dependencies import DependenciasComunes, requiere_admin
from app.schemas.camera import Camara, CamaraCrear, CamaraActualizar
from app.services.camera_service import ServicioCamaras
from app.models.camera import EstadoCamara  # Importar el Enum EstadoCamara
from app.api.websocket.rtc_signaling import websocket_endpoint as rtc_endpoint
from app.api.websocket.stream_handler import manejador_streaming
from app.utils.logger import obtener_logger
import uuid

logger = obtener_logger(__name__)
router = APIRouter(prefix="/cameras", tags=["cámaras"])


@router.get("/", response_model=List[Camara])
async def listar_camaras(
    activas_solo: bool = False,
    limite: int = 100,
    offset: int = 0,
    deps: DependenciasComunes = Depends()
):
    """Lista todas las cámaras"""
    servicio = ServicioCamaras(deps.db)
    return await servicio.listar_camaras(activas_solo, limite, offset)


@router.get("/{camara_id}", response_model=Camara)
async def obtener_camara(
    camara_id: int,
    deps: DependenciasComunes = Depends()
):
    """Obtiene una cámara específica"""
    servicio = ServicioCamaras(deps.db)
    camara = await servicio.obtener_camara(camara_id)
    
    if not camara:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cámara no encontrada"
        )
    
    return camara


@router.post("/", response_model=Camara)
async def crear_camara(
    camara_data: CamaraCrear,
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Crea una nueva cámara"""
    servicio = ServicioCamaras(deps.db)
    return await servicio.crear_camara(camara_data.model_dump())


@router.patch("/{camara_id}", response_model=Camara)
async def actualizar_camara(
    camara_id: int,
    camara_data: CamaraActualizar,
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Actualiza una cámara"""
    servicio = ServicioCamaras(deps.db)
    
    # Filtrar campos no nulos
    datos_actualizacion = {
        k: v for k, v in camara_data.model_dump().items() 
        if v is not None
    }
    
    camara = await servicio.actualizar_configuracion_camara(
        camara_id,
        datos_actualizacion
    )
    
    if not camara:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cámara no encontrada"
        )
    
    return camara


@router.post("/{camara_id}/activar")
async def activar_camara(
    camara_id: int,
    deps: DependenciasComunes = Depends()
):
    """Activa una cámara"""
    servicio = ServicioCamaras(deps.db)
    camara = await servicio.actualizar_estado_camara(camara_id, EstadoCamara.ACTIVA)  # Usar Enum
    
    if not camara:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cámara no encontrada"
        )
    
    # Notificar cambio de estado
    from app.api.websocket.notifications_ws import manejador_notificaciones_ws
    await manejador_notificaciones_ws.notificar_cambio_estado_camara(
        camara_id,
        EstadoCamara.ACTIVA,  # Usar Enum
        camara.nombre
    )
    
    return {"mensaje": "Cámara activada", "camara": camara}


@router.post("/{camara_id}/desactivar")
async def desactivar_camara(
    camara_id: int,
    deps: DependenciasComunes = Depends()
):
    """Desactiva una cámara"""
    servicio = ServicioCamaras(deps.db)
    camara = await servicio.actualizar_estado_camara(camara_id, EstadoCamara.INACTIVA)  # Usar Enum
    
    if not camara:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cámara no encontrada"
        )
    
    # Notificar cambio de estado
    from app.api.websocket.notifications_ws import manejador_notificaciones_ws
    await manejador_notificaciones_ws.notificar_cambio_estado_camara(
        camara_id,
        EstadoCamara.INACTIVA,  # Usar Enum
        camara.nombre
    )
    
    return {"mensaje": "Cámara desactivada", "camara": camara}


@router.websocket("/{camara_id}/stream")
async def websocket_stream(
    websocket: WebSocket,
    camara_id: int
):
    """WebSocket para streaming de cámara con WebRTC"""
    cliente_id = str(uuid.uuid4())
    await rtc_endpoint(websocket, cliente_id, camara_id)


@router.get("/{camara_id}/estadisticas")
async def obtener_estadisticas_camara(
    camara_id: int,
    deps: DependenciasComunes = Depends()
):
    """Obtiene estadísticas de procesamiento de una cámara"""
    # TODO: Implementar obtención de estadísticas desde el pipeline
    return {
        "camara_id": camara_id,
        "frames_procesados": 0,
        "incidentes_detectados": 0,
        "personas_rastreadas": 0,
        "estado_pipeline": "inactivo"
    }


@router.delete("/{camara_id}")
async def eliminar_camara(
    camara_id: int,
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Elimina una cámara"""
    servicio = ServicioCamaras(deps.db)
    
    # Verificar que existe
    camara = await servicio.obtener_camara(camara_id)
    if not camara:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cámara no encontrada"
        )
    
    # Eliminar
    try:
        await deps.db.delete(camara)
        await deps.db.commit()
        
        logger.info(f"Cámara {camara_id} eliminada")
        print(f"Cámara {camara_id} eliminada")
        return {"mensaje": "Cámara eliminada exitosamente"}
        
    except Exception as e:
        logger.error(f"Error al eliminar cámara: {e}")
        print(f"Error al eliminar cámara: {e}")
        await deps.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar cámara"
        )