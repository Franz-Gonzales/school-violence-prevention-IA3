"""
Servicio de generación de informes
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.incident import Incidente, EstadoIncidente, TipoIncidente, SeveridadIncidente  # Importar los Enum
from app.models.camera import Camara
from app.utils.logger import obtener_logger
import json

logger = obtener_logger(__name__)


class ServicioInformes:
    """Servicio para generación de informes"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def generar_informe_diario(
        self,
        fecha: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Genera informe diario de incidentes"""
        try:
            # if not fecha:
            #     fecha = datetime.now().date()
            # else:
            #     fecha = fecha.date()
            # fecha = datetime.now().date() if not fecha else fecha.date()
            fecha = fecha.date() if fecha else datetime.now().date()
            
            fecha_inicio = datetime.combine(fecha, datetime.min.time())
            fecha_fin = datetime.combine(fecha, datetime.max.time())
            
            # Obtener incidentes del día
            query = select(Incidente).where(
                and_(
                    Incidente.fecha_hora_inicio >= fecha_inicio,
                    Incidente.fecha_hora_inicio <= fecha_fin
                )
            )
            
            resultado = await self.db.execute(query)
            incidentes = resultado.scalars().all()
            
            # Procesar estadísticas
            total_incidentes = len(incidentes)
            # incidentes_resueltos = sum(1 for i in incidentes if i.estado == EstadoIncidente.RESUELTO)
            incidentes_resueltos = sum(i.estado == EstadoIncidente.RESUELTO for i in incidentes)
            
            # Agrupar por ubicación
            incidentes_por_ubicacion = {}
            for incidente in incidentes:
                ubicacion = incidente.ubicacion or 'Sin ubicación'
                if ubicacion not in incidentes_por_ubicacion:
                    incidentes_por_ubicacion[ubicacion] = 0
                incidentes_por_ubicacion[ubicacion] += 1
            
            # Calcular severidad promedio
            severidades = {
                SeveridadIncidente.BAJA: 1,
                SeveridadIncidente.MEDIA: 2,
                SeveridadIncidente.ALTA: 3,
                SeveridadIncidente.CRITICA: 4
            }
            severidad_promedio = 0
            if incidentes:
                suma_severidad = sum(
                    severidades.get(i.severidad, 2) for i in incidentes
                )
                severidad_promedio = suma_severidad / total_incidentes
            
            return {
                'fecha': fecha.isoformat(),
                'total_incidentes': total_incidentes,
                'incidentes_resueltos': incidentes_resueltos,
                'tasa_resolucion': (
                    incidentes_resueltos / total_incidentes 
                    if total_incidentes > 0 else 0
                ),
                'severidad_promedio': severidad_promedio,
                'incidentes_por_ubicacion': incidentes_por_ubicacion,
                'detalles_incidentes': [
                    {
                        'id': i.id,
                        'hora': i.fecha_hora_inicio.strftime('%H:%M:%S'),
                        'ubicacion': i.ubicacion,
                        'severidad': i.severidad.value,  # Usar Enum
                        'estado': i.estado.value  # Usar Enum
                    }
                    for i in incidentes
                ]
            }
            
        except Exception as e:
            logger.error(f"Error al generar informe diario: {e}")
            return {}
    
    async def generar_informe_semanal(
        self,
        fecha_fin: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Genera informe semanal de incidentes"""
        try:
            if not fecha_fin:
                fecha_fin = datetime.now()
            
            fecha_inicio = fecha_fin - timedelta(days=7)
            
            # Obtener incidentes de la semana
            query = select(Incidente).where(
                and_(
                    Incidente.fecha_hora_inicio >= fecha_inicio,
                    Incidente.fecha_hora_inicio <= fecha_fin
                )
            )
            
            resultado = await self.db.execute(query)
            incidentes = resultado.scalars().all()
            
            # Agrupar por día
            incidentes_por_dia = {}
            for i in range(7):
                dia = fecha_inicio + timedelta(days=i)
                dia_str = dia.strftime('%Y-%m-%d')
                incidentes_por_dia[dia_str] = 0
            
            for incidente in incidentes:
                dia_str = incidente.fecha_hora_inicio.strftime('%Y-%m-%d')
                if dia_str in incidentes_por_dia:
                    incidentes_por_dia[dia_str] += 1
            
            # Identificar tendencias
            valores_diarios = list(incidentes_por_dia.values())
            tendencia = 'estable'
            if len(valores_diarios) >= 3:
                if valores_diarios[-1] > valores_diarios[-3]:
                    tendencia = 'aumentando'
                elif valores_diarios[-1] < valores_diarios[-3]:
                    tendencia = 'disminuyendo'
            
            return {
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': fecha_fin.isoformat()
                },
                'total_incidentes': len(incidentes),
                'promedio_diario': len(incidentes) / 7,
                'incidentes_por_dia': incidentes_por_dia,
                'tendencia': tendencia,
                'dia_mas_incidentes': max(
                    incidentes_por_dia.items(),
                    key=lambda x: x[1]
                ) if incidentes_por_dia else None
            }
            
        except Exception as e:
            logger.error(f"Error al generar informe semanal: {e}")
            return {}
    
    async def generar_informe_mensual(
        self,
        mes: int,
        año: int
    ) -> Dict[str, Any]:
        """Genera informe mensual detallado"""
        try:
            # Calcular fechas del mes
            fecha_inicio = datetime(año, mes, 1)
            if mes == 12:
                fecha_fin = datetime(año + 1, 1, 1) - timedelta(seconds=1)
            else:
                fecha_fin = datetime(año, mes + 1, 1) - timedelta(seconds=1)
            
            # Obtener todos los incidentes del mes
            query = select(Incidente).where(
                and_(
                    Incidente.fecha_hora_inicio >= fecha_inicio,
                    Incidente.fecha_hora_inicio <= fecha_fin
                )
            )
            
            resultado = await self.db.execute(query)
            incidentes = resultado.scalars().all()
            
            # Análisis detallado
            analisis = {
                'total_incidentes': len(incidentes),
                'por_severidad': {
                    'baja': 0,
                    'media': 0,
                    'alta': 0,
                    'critica': 0
                },
                'por_estado': {
                    'pendiente': 0,
                    'atendiendo': 0,
                    'resuelto': 0
                },
                'tiempo_respuesta_promedio': 0,
                'ubicaciones_mas_frecuentes': {},
                'horas_pico': {}
            }
            
            tiempos_respuesta = []
            
            for incidente in incidentes:
                # Por severidad
                if incidente.severidad in analisis['por_severidad']:
                    analisis['por_severidad'][incidente.severidad] += 1
                
                # Por estado
                if incidente.estado in analisis['por_estado']:
                    analisis['por_estado'][incidente.estado] += 1
                
                # Tiempo de respuesta
                if incidente.fecha_resolucion:
                    tiempo = (incidente.fecha_resolucion - incidente.fecha_hora_inicio).total_seconds()
                    tiempos_respuesta.append(tiempo)
                
                # Ubicaciones frecuentes
                ubicacion = incidente.ubicacion or 'Sin ubicación'
                if ubicacion not in analisis['ubicaciones_mas_frecuentes']:
                    analisis['ubicaciones_mas_frecuentes'][ubicacion] = 0
                analisis['ubicaciones_mas_frecuentes'][ubicacion] += 1
                
                # Horas pico
                hora = incidente.fecha
                if hora not in analisis['horas_pico']:
                    analisis['horas_pico'][hora] = 0
                analisis['horas_pico'][hora] += 1
            
            # Calcular promedios
            if tiempos_respuesta:
                analisis['tiempo_respuesta_promedio'] = sum(tiempos_respuesta) / len(tiempos_respuesta)
            
            # Ordenar ubicaciones por frecuencia
            analisis['ubicaciones_mas_frecuentes'] = dict(
                sorted(
                    analisis['ubicaciones_mas_frecuentes'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]  # Top 5
            )
            
            return {
                'mes': f"{año}-{mes:02d}",
                'analisis': analisis,
                'recomendaciones': self._generar_recomendaciones(analisis)
            }
            
        except Exception as e:
            logger.error(f"Error al generar informe mensual: {e}")
            return {}
    
    def _generar_recomendaciones(self, analisis: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recomendaciones = []
        
        # Recomendaciones por severidad
        total = analisis['total_incidentes']
        if total > 0:
            porcentaje_alta = (
                (analisis['por_severidad']['alta'] + analisis['por_severidad']['critica']) 
                / total * 100
            )
            if porcentaje_alta > 30:
                recomendaciones.append(
                    "Alto porcentaje de incidentes severos. "
                    "Se recomienda reforzar la vigilancia y medidas preventivas."
                )
        
        # Recomendaciones por tiempo de respuesta
        if analisis['tiempo_respuesta_promedio'] > 300:  # Más de 5 minutos
            recomendaciones.append(
                "El tiempo de respuesta promedio es alto. "
                "Considere optimizar los protocolos de respuesta."
            )
        
        # Recomendaciones por ubicación
        if analisis['ubicaciones_mas_frecuentes']:
            ubicacion_top = list(analisis['ubicaciones_mas_frecuentes'].keys())[0]
            recomendaciones.append(
                f"La ubicación con más incidentes es '{ubicacion_top}'. "
                "Se sugiere aumentar la vigilancia en esta área."
            )
        
        # Recomendaciones por horas pico
        if analisis['horas_pico']:
            hora_pico = max(analisis['horas_pico'].items(), key=lambda x: x[1])[0]
            recomendaciones.append(
                f"La hora con más incidentes es {hora_pico}:00. "
                "Considere reforzar el personal durante este horario."
            )
        
        return recomendaciones