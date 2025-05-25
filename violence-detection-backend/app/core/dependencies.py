"""
Dependencias compartidas del sistema
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import obtener_db
from app.core.security import obtener_usuario_actual
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class DependenciasComunes:
    """Clase para agrupar dependencias comunes"""
    
    def __init__(
        self,
        db: AsyncSession = Depends(obtener_db),
        usuario_actual: Optional[dict] = Depends(obtener_usuario_actual)
    ):
        self.db = db
        self.usuario_actual = usuario_actual


async def verificar_sistema_activo():
    """Verifica que el sistema esté activo y funcionando"""
    # Aquí puedes agregar verificaciones del sistema
    # Por ejemplo, verificar que los modelos estén cargados
    return True


async def obtener_configuracion_actual(
    db: AsyncSession = Depends(obtener_db)
) -> dict:
    """Obtiene la configuración actual del sistema desde la base de datos"""
    # Por ahora retornamos configuración por defecto
    return {
        "umbral_violencia": 0.70,
        "duracion_clip": 5,
        "fps_procesamiento": 15,
        "notificaciones_activas": True
    }


def requiere_admin():
    """Dependencia que requiere rol de administrador"""
    async def verificar_admin(
        usuario_actual: dict = Depends(obtener_usuario_actual)
    ):
        if usuario_actual.get("rol") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requiere rol de administrador"
            )
        return usuario_actual
    
    return verificar_admin