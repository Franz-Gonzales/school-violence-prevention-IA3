"""
Endpoints de generación de informes
"""
from typing import Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from app.core.dependencies import DependenciasComunes
from app.services.report_service import ServicioInformes
from app.services.incident_service import ServicioIncidentes
from app.utils.logger import obtener_logger
import json
from pathlib import Path

logger = obtener_logger(__name__)
router = APIRouter(prefix="/reports", tags=["informes"])


@router.get("/diario")
async def generar_informe_diario(
    fecha: Optional[date] = Query(None, description="Fecha del informe (por defecto hoy)"),
    deps: DependenciasComunes = Depends()
):
    """Genera informe diario de incidentes"""
    servicio = ServicioInformes(deps.db)
    
    fecha_informe = datetime.combine(fecha, datetime.min.time()) if fecha else None
    informe = await servicio.generar_informe_diario(fecha_informe)
    
    return informe


@router.get("/semanal")
async def generar_informe_semanal(
    fecha_fin: Optional[date] = Query(None, description="Fecha final del periodo"),
    deps: DependenciasComunes = Depends()
):
    """Genera informe semanal de incidentes"""
    servicio = ServicioInformes(deps.db)
    
    fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time()) if fecha_fin else None
    informe = await servicio.generar_informe_semanal(fecha_fin_dt)
    
    return informe


@router.get("/mensual")
async def generar_informe_mensual(
    mes: int = Query(..., ge=1, le=12, description="Mes (1-12)"),
    año: int = Query(..., ge=2024, description="Año"),
    deps: DependenciasComunes = Depends()
):
    """Genera informe mensual detallado"""
    servicio = ServicioInformes(deps.db)
    informe = await servicio.generar_informe_mensual(mes, año)
    
    return informe


@router.post("/exportar")
async def exportar_informe(
    tipo: str = Query(..., regex="^(diario|semanal|mensual)$"),
    formato: str = Query("json", regex="^(json|pdf|excel)$"),
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    deps: DependenciasComunes = Depends()
):
    """Exporta un informe en el formato especificado"""
    servicio = ServicioInformes(deps.db)
    
    # Generar informe según tipo
    if tipo == "diario":
        informe = await servicio.generar_informe_diario(
            datetime.combine(fecha_inicio, datetime.min.time()) if fecha_inicio else None
        )
    elif tipo == "semanal":
        informe = await servicio.generar_informe_semanal(
            datetime.combine(fecha_fin, datetime.max.time()) if fecha_fin else None
        )
    else:  # mensual
        if not fecha_inicio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere fecha_inicio para informe mensual"
            )
        informe = await servicio.generar_informe_mensual(
            fecha_inicio.month,
            fecha_inicio.year
        )
    
    # Exportar según formato
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"informe_{tipo}_{timestamp}"
    
    if formato == "json":
        # Guardar como JSON
        filepath = Path(f"/tmp/{filename}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(informe, f, ensure_ascii=False, indent=2, default=str)
        
        return FileResponse(
            path=filepath,
            filename=f"{filename}.json",
            media_type="application/json"
        )
    
    elif formato == "pdf":
        # TODO: Implementar generación de PDF
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Exportación a PDF aún no implementada"
        )
    
    elif formato == "excel":
        # TODO: Implementar generación de Excel
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Exportación a Excel aún no implementada"
        )


@router.get("/dashboard")
async def obtener_datos_dashboard(
    deps: DependenciasComunes = Depends()
):
    """Obtiene datos para el dashboard principal"""
    servicio = ServicioInformes(deps.db)
    servicio_incidentes = ServicioIncidentes(deps.db)
    
    # Obtener estadísticas generales
    estadisticas = await servicio_incidentes.obtener_estadisticas()
    
    # Obtener informe del día
    informe_hoy = await servicio.generar_informe_diario()
    
    # Obtener tendencia semanal
    informe_semanal = await servicio.generar_informe_semanal()
    
    return {
        "estadisticas_generales": estadisticas,
        "resumen_hoy": {
            "total_incidentes": informe_hoy.get("total_incidentes", 0),
            "incidentes_resueltos": informe_hoy.get("incidentes_resueltos", 0),
            "severidad_promedio": informe_hoy.get("severidad_promedio", 0)
        },
        "tendencia_semanal": {
            "tendencia": informe_semanal.get("tendencia", "estable"),
            "promedio_diario": informe_semanal.get("promedio_diario", 0),
            "grafico_datos": informe_semanal.get("incidentes_por_dia", {})
        },
        "alertas_activas": 0,  # TODO: Implementar conteo de alertas activas
        "camaras_activas": 0   # TODO: Implementar conteo de cámaras activas
    }