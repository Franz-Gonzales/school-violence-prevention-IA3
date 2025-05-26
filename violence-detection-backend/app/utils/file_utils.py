"""
Utilidades para manejo de archivos
"""
import os
import shutil
from pathlib import Path
from typing import Optional
import aiofiles
from datetime import datetime
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class ManejadorArchivos:
    """Clase para manejo de archivos del sistema"""
    
    @staticmethod
    async def guardar_archivo_temporal(
        contenido: bytes,
        extension: str = ".tmp"
    ) -> Path:
        """Guarda un archivo temporal"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"temp_{timestamp}{extension}"
        ruta_temp = Path("/tmp") / nombre_archivo
        
        async with aiofiles.open(ruta_temp, 'wb') as f:
            await f.write(contenido)
        
        return ruta_temp
    
    @staticmethod
    async def mover_archivo(
        origen: Path,
        destino: Path,
        crear_directorio: bool = True
    ) -> bool:
        """Mueve un archivo de origen a destino"""
        try:
            if crear_directorio:
                destino.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(origen), str(destino))
            logger.info(f"Archivo movido de {origen} a {destino}")
            print(f"Archivo movido de {origen} a {destino}")
            return True
            
        except Exception as e:
            logger.error(f"Error al mover archivo: {e}")
            print(f"Error al mover archivo: {e}")
            return False
    
    @staticmethod
    def limpiar_archivos_antiguos(
        directorio: Path,
        dias: int = 30
    ) -> int:
        """Limpia archivos más antiguos que X días"""
        archivos_eliminados = 0
        ahora = datetime.now()
        
        try:
            for archivo in directorio.iterdir():
                if archivo.is_file():
                    tiempo_modificacion = datetime.fromtimestamp(
                        archivo.stat().st_mtime
                    )
                    diferencia = (ahora - tiempo_modificacion).days
                    
                    if diferencia > dias:
                        archivo.unlink()
                        archivos_eliminados += 1
                        logger.info(f"Archivo eliminado: {archivo}")
                        print(f"Archivo eliminado: {archivo}")
            
            return archivos_eliminados
            
        except Exception as e:
            logger.error(f"Error al limpiar archivos: {e}")
            print(f"Error al limpiar archivos: {e}")
            return 0
    
    @staticmethod
    def generar_nombre_archivo(
        prefijo: str,
        extension: str,
        incluir_timestamp: bool = True
    ) -> str:
        """Genera un nombre único para archivo"""
        if incluir_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            return f"{prefijo}_{timestamp}{extension}"
        else:
            return f"{prefijo}{extension}"