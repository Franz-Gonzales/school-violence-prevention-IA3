"""
Servicio de gestión de incidentes
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.incident import Incidente, EstadoIncidente, TipoIncidente, SeveridadIncidente  # Importar los Enum
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class ServicioIncidentes:
    """Servicio para gestión de incidentes"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def crear_incidente(self, datos_incidente: Dict[str, Any]) -> Incidente:
        """Crea un nuevo incidente"""
        try:
            incidente = Incidente(**datos_incidente)
            self.db.add(incidente)
            await self.db.commit()
            await self.db.refresh(incidente)
            
            logger.info(f"Incidente creado: ID {incidente.id}")
            return incidente
            
        except Exception as e:
            logger.error(f"Error al crear incidente: {e}")
            await self.db.rollback()
            raise
    
    async def obtener_incidente(self, incidente_id: int) -> Optional[Incidente]:
        """Obtiene un incidente por ID"""
        try:
            resultado = await self.db.execute(
                select(Incidente).where(Incidente.id == incidente_id)
            )
            return resultado.scalars().first()
        except Exception as e:
            logger.error(f"Error al obtener incidente: {e}")
            return None
    
    async def listar_incidentes(
        self,
        limite: int = 100,
        offset: int = 0,
        estado: Optional[EstadoIncidente] = None,  # Usar el Enum EstadoIncidente
        camara_id: Optional[int] = None,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None
    ) -> List[Incidente]:
        """Lista incidentes con filtros opcionales"""
        try:
            query = select(Incidente)
            
            # Aplicar filtros
            condiciones = []
            if estado:
                condiciones.append(Incidente.estado == estado)  # Comparar con el Enum
            if camara_id:
                condiciones.append(Incidente.camara_id == camara_id)
            if fecha_inicio:
                condiciones.append(Incidente.fecha_hora_inicio >= fecha_inicio)
            if fecha_fin:
                condiciones.append(Incidente.fecha_hora_inicio <= fecha_fin)
            
            if condiciones:
                query = query.where(and_(*condiciones))
            
            # Ordenar por fecha descendente
            query = query.order_by(Incidente.fecha_hora_inicio.desc())
            query = query.limit(limite).offset(offset)
            
            resultado = await self.db.execute(query)
            return resultado.scalars().all()
            
        except Exception as e:
            logger.error(f"Error al listar incidentes: {e}")
            return []
    
    async def actualizar_incidente(
        self,
        incidente_id: int,
        datos_actualizacion: Dict[str, Any]
    ) -> Optional[Incidente]:
        """Actualiza un incidente existente"""
        try:
            incidente = await self.obtener_incidente(incidente_id)
            if not incidente:
                return None
            
            # Actualizar campos
            for campo, valor in datos_actualizacion.items():
                if hasattr(incidente, campo):
                    setattr(incidente, campo, valor)
            
            # Si se está resolviendo, agregar fecha de resolución
            if datos_actualizacion.get('estado') == EstadoIncidente.RESUELTO:  # Usar el Enum
                incidente.fecha_resolucion = datetime.now()
                
                # Calcular duración si no se ha calculado
                if incidente.fecha_hora_fin and not incidente.duracion_segundos:
                    duracion = incidente.fecha_hora_fin - incidente.fecha_hora_inicio
                    incidente.duracion_segundos = int(duracion.total_seconds())
            
            await self.db.commit()
            await self.db.refresh(incidente)
            
            logger.info(f"Incidente {incidente_id} actualizado")
            return incidente
            
        except Exception as e:
            logger.error(f"Error al actualizar incidente: {e}")
            await self.db.rollback()
            return None
    
    async def obtener_estadisticas(
        self,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Obtiene estadísticas de incidentes"""
        try:
            # Si no se especifican fechas, usar últimos 30 días
            if not fecha_fin:
                fecha_fin = datetime.now()
            if not fecha_inicio:
                fecha_inicio = fecha_fin - timedelta(days=30)
            
            # Query base con filtro de fechas
            query_base = select(Incidente).where(
                and_(
                    Incidente.fecha_hora_inicio >= fecha_inicio,
                    Incidente.fecha_hora_inicio <= fecha_fin
                )
            )
            
            # Total de incidentes
            resultado_total = await self.db.execute(query_base)
            total_incidentes = len(resultado_total.scalars().all())
            
            # Incidentes por estado
            resultado_estados = await self.db.execute(
                query_base.with_only_columns([Incidente.estado, func.count(Incidente.estado)])
                .group_by(Incidente.estado)
            )
            estados_count = {estado.value: 0 for estado in EstadoIncidente}  # Inicializar con valores del Enum
            for estado, count in resultado_estados:
                estados_count[estado.value] = count
            
            # Calcular tiempo promedio de respuesta
            tiempos_respuesta = []
            for incidente in await self.db.execute(query_base):
                if incidente.fecha_resolucion:
                    tiempo = (incidente.fecha_resolucion - incidente.fecha_hora_inicio).total_seconds()
                    tiempos_respuesta.append(tiempo)
            
            tiempo_respuesta_promedio = (
                sum(tiempos_respuesta) / len(tiempos_respuesta)
                if tiempos_respuesta else 0
            )
            
            return {
                'total_incidentes': total_incidentes,
                'incidentes_por_estado': estados_count,
                'tiempo_respuesta_promedio_segundos': tiempo_respuesta_promedio,
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': fecha_fin.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {}
