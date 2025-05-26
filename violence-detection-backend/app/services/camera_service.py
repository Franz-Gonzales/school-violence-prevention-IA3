"""
Servicio de gestión de cámaras
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.camera import Camara, EstadoCamara, TipoCamara  # Importar los Enum
from app.utils.logger import obtener_logger
from datetime import datetime

logger = obtener_logger(__name__)


class ServicioCamaras:
    """Servicio para gestión de cámaras"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def crear_camara(self, datos_camara: Dict[str, Any]) -> Camara:
        """Crea una nueva cámara"""
        try:
            camara = Camara(**datos_camara)
            self.db.add(camara)
            await self.db.commit()
            await self.db.refresh(camara)
            
            logger.info(f"Cámara creada: {camara.nombre}")
            print(f"Cámara creada: {camara.nombre}")
            return camara
            
        except Exception as e:
            logger.error(f"Error al crear cámara: {e}")
            print(f"Error al crear cámara: {e}")
            await self.db.rollback()
            raise
    
    async def obtener_camara(self, camara_id: int) -> Optional[Camara]:
        """Obtiene una cámara por ID"""
        try:
            resultado = await self.db.execute(
                select(Camara).where(Camara.id == camara_id)
            )
            return resultado.scalars().first()
        except Exception as e:
            logger.error(f"Error al obtener cámara: {e}")
            print(f"Error al obtener cámara: {e}")
            return None
    
    async def listar_camaras(
        self,
        activas_solo: bool = False,
        limite: int = 100,
        offset: int = 0
    ) -> List[Camara]:
        """Lista todas las cámaras"""
        try:
            query = select(Camara)
            
            if activas_solo:
                query = query.where(Camara.estado == EstadoCamara.ACTIVA)  # Usar Enum
            
            query = query.limit(limite).offset(offset)
            
            resultado = await self.db.execute(query)
            return resultado.scalars().all()
            
        except Exception as e:
            logger.error(f"Error al listar cámaras: {e}")
            print(f"Error al listar cámaras: {e}")
            return []
    
    async def actualizar_estado_camara(
        self,
        camara_id: int,
        estado: EstadoCamara  
    ) -> Optional[Camara]:
        """Actualiza el estado de una cámara"""
        try:
            camara = await self.obtener_camara(camara_id)
            if not camara:
                return None
            
            camara.estado = estado
            if estado == EstadoCamara.ACTIVA:  
                camara.ultima_actividad = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(camara)
            
            logger.info(f"Estado de cámara {camara_id} actualizado a: {estado.value}")
            print(f"Estado de cámara {camara_id} actualizado a: {estado.value}")
            return camara
            
        except Exception as e:
            logger.error(f"Error al actualizar estado de cámara: {e}")
            print(f"Error al actualizar estado de cámara: {e}")
            await self.db.rollback()
            return None
    
    async def actualizar_configuracion_camara(
        self,
        camara_id: int,
        configuracion: Dict[str, Any]
    ) -> Optional[Camara]:
        """Actualiza la configuración de una cámara"""
        try:
            camara = await self.obtener_camara(camara_id)
            if not camara:
                return None
            
            # Actualizar campos de configuración
            if 'resolucion_ancho' in configuracion:
                camara.resolucion_ancho = configuracion['resolucion_ancho']
            if 'resolucion_alto' in configuracion:
                camara.resolucion_alto = configuracion['resolucion_alto']
            if 'fps' in configuracion:
                camara.fps = configuracion['fps']
            
            # Guardar configuración adicional en JSON
            camara.configuracion_json = configuracion
            
            await self.db.commit()
            await self.db.refresh(camara)
            
            logger.info(f"Configuración de cámara {camara_id} actualizada")
            print(f"Configuración de cámara {camara_id} actualizada")
            return camara
            
        except Exception as e:
            logger.error(f"Error al actualizar configuración de cámara: {e}")
            print(f"Error al actualizar configuración de cámara: {e}")
            await self.db.rollback()
            return None