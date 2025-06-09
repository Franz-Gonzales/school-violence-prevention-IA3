# Archivo: violence-detection-backend/app/api/v1/files.py (NUEVO ARCHIVO)
# Este archivo maneja la descarga/visualización de archivos de evidencia

"""
Endpoints para servir archivos de evidencia
"""
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import obtener_db
from app.core.dependencies import DependenciasComunes
from app.services.incident_service import ServicioIncidentes
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)
router = APIRouter(prefix="/files", tags=["archivos"])


@router.get("/videos/{incidente_id}")
async def obtener_video_evidencia(
    incidente_id: int,
    deps: DependenciasComunes = Depends()
):
    """
    Sirve el video de evidencia de un incidente específico
    """
    try:
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
        
        # Construir la ruta completa del archivo
        video_path = configuracion.VIDEO_EVIDENCE_PATH / incidente.video_evidencia_path
        
        if not video_path.exists():
            logger.error(f"Video no encontrado en: {video_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo de video no encontrado en el servidor"
            )
        
        # Verificar que es un archivo de video válido
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        if video_path.suffix.lower() not in valid_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de archivo no válido"
            )
        
        # Determinar el media type
        media_type_map = {
            '.mp4': 'video/mp4',
            '.avi': 'video/avi', 
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska'
        }
        
        media_type = media_type_map.get(video_path.suffix.lower(), 'video/mp4')
        
        # Retornar el archivo como respuesta
        return FileResponse(
            path=str(video_path),
            media_type=media_type,
            filename=f"evidencia_incidente_{incidente_id}{video_path.suffix}",
            headers={
                "Content-Disposition": f"inline; filename=evidencia_incidente_{incidente_id}{video_path.suffix}",
                "Cache-Control": "max-age=3600",
                "Accept-Ranges": "bytes"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sirviendo video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/videos/{incidente_id}/info")
async def obtener_info_video(
    incidente_id: int,
    deps: DependenciasComunes = Depends()
):
    """
    Obtiene información del video sin descargarlo
    """
    try:
        servicio = ServicioIncidentes(deps.db)
        incidente = await servicio.obtener_incidente(incidente_id)
        
        if not incidente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incidente no encontrado"
            )
        
        if not incidente.video_evidencia_path:
            return {
                "has_video": False,
                "message": "No hay video disponible para este incidente"
            }
        
        video_path = configuracion.VIDEO_EVIDENCE_PATH / incidente.video_evidencia_path
        
        if not video_path.exists():
            return {
                "has_video": False,
                "message": "Archivo de video no encontrado",
                "expected_path": str(video_path)
            }
        
        # Obtener información del archivo
        file_stats = video_path.stat()
        
        return {
            "has_video": True,
            "video_url": incidente.video_url,
            "file_path": incidente.video_evidencia_path,
            "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
            "file_extension": video_path.suffix,
            "created_at": incidente.fecha_creacion.isoformat() if incidente.fecha_creacion else None,
            "incident_duration": incidente.duracion_segundos,
            "metadata": incidente.metadata_json
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo info de video: {e}")
        print(f"❌ Error obteniendo info de video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )