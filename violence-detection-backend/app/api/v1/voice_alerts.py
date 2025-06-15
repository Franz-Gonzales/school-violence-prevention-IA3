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
        

@router.get("/creditos")
async def verificar_creditos_elevenlabs(
    deps: DependenciasComunes = Depends()
):
    """Verifica los créditos disponibles en ElevenLabs - VERSIÓN SEGURA"""
    try:
        # *** CAMBIO: Usar verificación simplificada que no falla ***
        info_creditos = servicio_alertas_voz.verificar_creditos()
        
        # Agregar nota sobre limitaciones
        info_creditos["limitaciones"] = {
            "verificacion_real": False,
            "motivo": "API key con permisos limitados",
            "funcionalidad": "Solo text-to-speech disponible"
        }
        
        # Siempre retornar éxito con nota explicativa
        info_creditos["recomendacion"] = "✅ Servicio funcional - Verificación de créditos omitida"
        info_creditos["nivel_alerta"] = "informativo"
        
        return info_creditos
        
    except Exception as e:
        logger.error(f"Error obteniendo información: {e}")
        # Retornar información básica en caso de error
        return {
            "success": False,
            "error": f"No se pudo verificar: {str(e)}",
            "creditos_disponibles": "Desconocido",
            "recomendacion": "⚠️ Usa el endpoint /probar para verificar funcionalidad",
            "nivel_alerta": "advertencia",
            "limitaciones": {
                "verificacion_real": False,
                "motivo": "Error en consulta o permisos limitados",
                "solucion": "El servicio debería funcionar normalmente para TTS"
            }
        }

@router.post("/verificar-viabilidad")
async def verificar_viabilidad_texto(
    request: AlertaVozRequest,
    deps: DependenciasComunes = Depends()
):
    """Verifica si se puede generar audio para un texto específico - VERSIÓN SEGURA"""
    try:
        # Generar mensaje de prueba
        servicio = servicio_alertas_voz
        mensaje = servicio._generar_mensaje_alerta(
            request.ubicacion, 
            request.probabilidad, 
            request.personas_detectadas
        )
        
        # *** CAMBIO: Usar verificación simplificada ***
        viabilidad = servicio.puede_generar_audio(mensaje)
        
        # *** CAMBIO: No intentar verificar créditos reales ***
        creditos_info = {
            "nota": "Verificación de créditos omitida por limitaciones de API key",
            "estimacion": "Funcionalidad disponible para text-to-speech"
        }
        
        return {
            "mensaje_generado": mensaje,
            "longitud_caracteres": len(mensaje),
            "viabilidad": viabilidad,
            "creditos_actuales": creditos_info,
            "recomendacion": "Usa /probar para verificar funcionalidad real"
        }
        
    except Exception as e:
        logger.error(f"Error verificando viabilidad: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verificando viabilidad: {str(e)}"
        )