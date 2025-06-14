"""
Endpoints de generación de informes - CORREGIDO para estadísticas reales
"""
from typing import Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from app.core.dependencies import DependenciasComunes
from app.services.report_service import ServicioInformes
from app.services.incident_service import ServicioIncidentes
from app.services.camera_service import ServicioCamaras
from app.models.incident import EstadoIncidente
from app.models.camera import EstadoCamara
from app.utils.logger import obtener_logger
import json
from pathlib import Path
from sqlalchemy import select, func, and_

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
    """*** CORREGIDO: Obtiene datos REALES para el dashboard principal ***"""
    try:
        # Importar modelos necesarios
        from app.models.incident import Incidente
        from app.models.camera import Camara
        
        # Calcular fechas para "hoy"
        hoy = datetime.now().date()
        inicio_dia = datetime.combine(hoy, datetime.min.time())
        fin_dia = datetime.combine(hoy, datetime.max.time())
        
        # *** 1. CONTAR INCIDENTES DE HOY (REAL) ***
        query_incidentes_hoy = select(func.count(Incidente.id)).where(
            and_(
                Incidente.fecha_hora_inicio >= inicio_dia,
                Incidente.fecha_hora_inicio <= fin_dia
            )
        )
        resultado_incidentes = await deps.db.execute(query_incidentes_hoy)
        total_incidentes_hoy = resultado_incidentes.scalar() or 0
        
        # *** 2. CONTAR CÁMARAS ACTIVAS (REAL) ***
        query_camaras_activas = select(func.count(Camara.id)).where(
            Camara.estado == EstadoCamara.ACTIVA
        )
        resultado_camaras = await deps.db.execute(query_camaras_activas)
        total_camaras_activas = resultado_camaras.scalar() or 0
        
        # *** 3. OBTENER INCIDENTES RESUELTOS HOY ***
        query_incidentes_resueltos = select(func.count(Incidente.id)).where(
            and_(
                Incidente.fecha_hora_inicio >= inicio_dia,
                Incidente.fecha_hora_inicio <= fin_dia,
                Incidente.estado == EstadoIncidente.RESUELTO
            )
        )
        resultado_resueltos = await deps.db.execute(query_incidentes_resueltos)
        incidentes_resueltos_hoy = resultado_resueltos.scalar() or 0
        
        # *** 4. OBTENER TENDENCIA SEMANAL ***
        servicio_informes = ServicioInformes(deps.db)
        informe_semanal = await servicio_informes.generar_informe_semanal()
        
        # *** 5. ESTADÍSTICAS ADICIONALES ***
        # Total de cámaras (activas + inactivas)
        query_total_camaras = select(func.count(Camara.id))
        resultado_total_camaras = await deps.db.execute(query_total_camaras)
        total_camaras = resultado_total_camaras.scalar() or 0
        
        logger.info(f"Dashboard - Incidentes hoy: {total_incidentes_hoy}, Cámaras activas: {total_camaras_activas}")
        print(f"📊 Dashboard stats - Incidentes hoy: {total_incidentes_hoy}, Cámaras activas: {total_camaras_activas}")
        
        return {
            "estadisticas_generales": {
                "total_incidentes": total_incidentes_hoy,
                "total_camaras": total_camaras,
                "camaras_activas": total_camaras_activas,
                "incidentes_resueltos": incidentes_resueltos_hoy
            },
            "resumen_hoy": {
                "total_incidentes": total_incidentes_hoy,
                "incidentes_resueltos": incidentes_resueltos_hoy,
                "tasa_resolucion": (
                    (incidentes_resueltos_hoy / total_incidentes_hoy * 100) 
                    if total_incidentes_hoy > 0 else 0
                )
            },
            "tendencia_semanal": {
                "tendencia": informe_semanal.get("tendencia", "estable"),
                "promedio_diario": informe_semanal.get("promedio_diario", 0),
                "grafico_datos": informe_semanal.get("incidentes_por_dia", {})
            },
            "sistema": {
                "timestamp": datetime.now().isoformat(),
                "estado": "operativo"
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos del dashboard: {e}")
        print(f"❌ Error obteniendo datos del dashboard: {e}")
        
        # Retornar datos por defecto en caso de error
        return {
            "estadisticas_generales": {
                "total_incidentes": 0,
                "total_camaras": 0,
                "camaras_activas": 0,
                "incidentes_resueltos": 0
            },
            "resumen_hoy": {
                "total_incidentes": 0,
                "incidentes_resueltos": 0,
                "tasa_resolucion": 0
            },
            "tendencia_semanal": {
                "tendencia": "sin_datos",
                "promedio_diario": 0,
                "grafico_datos": {}
            },
            "sistema": {
                "timestamp": datetime.now().isoformat(),
                "estado": "error"
            }
        }