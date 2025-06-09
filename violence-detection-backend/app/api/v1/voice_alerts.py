# app/api/v1/voice_alerts.py - Nuevo archivo para endpoints de alertas de voz

"""
Endpoints para control de alertas de voz
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from app.core.dependencies import DependenciasComunes, requiere_admin
from app.services.voice_alert_service import servicio_alertas_voz
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)
router = APIRouter(prefix="/voice-alerts", tags=["alertas-de-voz"])


class AlertaVozRequest(BaseModel):
    """Schema para solicitud de alerta de voz"""
    ubicacion: str
    probabilidad: float = 0.85
    personas_detectadas: int = 0
    forzar: bool = False


class ConfiguracionVozRequest(BaseModel):
    """Schema para configurar alertas de voz"""
    cooldown_segundos: int = 15
    habilitado: bool = True


@router.get("/estado")
async def obtener_estado_alertas_voz(
    deps: DependenciasComunes = Depends()
):
    """Obtiene el estado actual del sistema de alertas de voz"""
    return servicio_alertas_voz.obtener_estado()


@router.post("/probar")
async def probar_alerta_voz(
    request: AlertaVozRequest,
    deps: DependenciasComunes = Depends()
):
    """Prueba el sistema de alertas de voz"""
    try:
        success = await servicio_alertas_voz.emitir_alerta_violencia(
            ubicacion=request.ubicacion,
            probabilidad=request.probabilidad,
            personas_detectadas=request.personas_detectadas,
            forzar=request.forzar
        )
        
        return {
            "success": success,
            "mensaje": "Alerta de voz emitida correctamente" if success else "No se pudo emitir la alerta",
            "ubicacion": request.ubicacion
        }
        
    except Exception as e:
        logger.error(f"Error en prueba de alerta de voz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al emitir alerta de voz: {str(e)}"
        )


@router.post("/configurar")
async def configurar_alertas_voz(
    config: ConfiguracionVozRequest,
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Configura el sistema de alertas de voz (solo administradores)"""
    try:
        # Configurar cooldown
        servicio_alertas_voz.configurar_cooldown(config.cooldown_segundos)
        
        # Nota: Para habilitar/deshabilitar completamente, se necesitaría 
        # una configuración más profunda que puede requerir reinicio
        
        return {
            "mensaje": "Configuración actualizada",
            "cooldown_segundos": config.cooldown_segundos,
            "estado_actual": servicio_alertas_voz.obtener_estado()
        }
        
    except Exception as e:
        logger.error(f"Error configurando alertas de voz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al configurar alertas de voz: {str(e)}"
        )


@router.post("/prueba-rapida")
async def prueba_rapida_voz(
    deps: DependenciasComunes = Depends()
):
    """Prueba rápida del sistema de alertas de voz"""
    try:
        success = await servicio_alertas_voz.probar_alerta("Área de Prueba")
        
        return {
            "success": success,
            "mensaje": "Prueba completada",
            "estado": servicio_alertas_voz.obtener_estado()
        }
        
    except Exception as e:
        logger.error(f"Error en prueba rápida: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en prueba de alerta: {str(e)}"
        )


@router.get("/diagnostico")
async def diagnostico_sistema_voz(
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Diagnóstico completo del sistema de alertas de voz"""
    try:
        estado = servicio_alertas_voz.obtener_estado()
        
        # Verificaciones adicionales
        diagnostico = {
            "estado_servicio": estado,
            "dependencias": {
                "elevenlabs_disponible": True,
                "sounddevice_disponible": True,
                "numpy_disponible": True
            },
            "configuracion": {
                "api_key_configurada": estado["cliente_conectado"],
                "voice_id": estado["voice_id"],
                "cooldown": estado["cooldown_segundos"]
            }
        }
        
        # Verificar dependencias
        try:
            import elevenlabs
            diagnostico["dependencias"]["elevenlabs_version"] = elevenlabs.__version__
        except ImportError:
            diagnostico["dependencias"]["elevenlabs_disponible"] = False
        
        try:
            import sounddevice as sd
            # Obtener dispositivos de audio disponibles
            devices = sd.query_devices()
            diagnostico["audio_devices"] = len(devices)
        except ImportError:
            diagnostico["dependencias"]["sounddevice_disponible"] = False
        
        return diagnostico
        
    except Exception as e:
        logger.error(f"Error en diagnóstico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en diagnóstico: {str(e)}"
        )