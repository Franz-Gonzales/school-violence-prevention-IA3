"""
Tareas de limpieza y mantenimiento del sistema
"""
import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from app.config import configuracion
from app.utils.logger import obtener_logger
from app.utils.file_utils import ManejadorArchivos
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.incident import Incidente
from app.core.database import obtener_db

logger = obtener_logger(__name__)


async def limpiar_archivos_temporales():
    """Limpia archivos temporales antiguos"""
    try:
        # Limpiar directorio de uploads
        archivos_eliminados = ManejadorArchivos.limpiar_archivos_antiguos(
            configuracion.UPLOAD_PATH,
            dias=1  # Archivos temporales de más de 1 día
        )
        logger.info(f"Archivos temporales eliminados: {archivos_eliminados}")
        
        # Limpiar archivos en /tmp
        tmp_path = Path("/tmp")
        patron = "temp_*"
        
        for archivo in tmp_path.glob(patron):
            try:
                if archivo.is_file():
                    edad = datetime.now() - datetime.fromtimestamp(archivo.stat().st_mtime)
                    if edad > timedelta(hours=12):
                        archivo.unlink()
                        logger.debug(f"Archivo temporal eliminado: {archivo}")
            except Exception as e:
                logger.error(f"Error al eliminar {archivo}: {e}")
                
    except Exception as e:
        logger.error(f"Error en limpieza de archivos temporales: {e}")


async def limpiar_videos_antiguos(dias_retencion: int = 30):
    """Limpia videos de evidencia antiguos según política de retención"""
    try:
        fecha_limite = datetime.now() - timedelta(days=dias_retencion)
        
        async for db in obtener_db():
            # Buscar incidentes antiguos con videos
            query = select(Incidente).where(
                and_(
                    Incidente.fecha_creacion < fecha_limite,
                    Incidente.video_evidencia_path.isnot(None)
                )
            )
            
            resultado = await db.execute(query)
            incidentes_antiguos = resultado.scalars().all()
            
            videos_eliminados = 0
            espacio_liberado = 0
            
            for incidente in incidentes_antiguos:
                if incidente.video_evidencia_path:
                    video_path = Path(incidente.video_evidencia_path)
                    
                    if video_path.exists():
                        try:
                            # Obtener tamaño antes de eliminar
                            tamaño = video_path.stat().st_size
                            
                            # Eliminar video
                            video_path.unlink()
                            videos_eliminados += 1
                            espacio_liberado += tamaño
                            
                            # Eliminar thumbnail si existe
                            if incidente.thumbnail_url:
                                thumbnail_path = Path(incidente.thumbnail_url)
                                if thumbnail_path.exists():
                                    thumbnail_path.unlink()
                            
                            # Actualizar registro
                            incidente.video_evidencia_path = None
                            incidente.thumbnail_url = None
                            
                            logger.info(f"Video eliminado para incidente {incidente.id}")
                            
                        except Exception as e:
                            logger.error(f"Error al eliminar video {video_path}: {e}")
            
            await db.commit()
            
            # Reportar resultados
            espacio_mb = espacio_liberado / (1024 * 1024)
            logger.info(
                f"Limpieza completada: {videos_eliminados} videos eliminados, "
                f"{espacio_mb:.2f} MB liberados"
            )
            
    except Exception as e:
        logger.error(f"Error en limpieza de videos antiguos: {e}")


async def optimizar_almacenamiento():
    """Optimiza el almacenamiento comprimiendo videos no procesados"""
    try:
        from app.tasks.video_processing import comprimir_video_evidencia
        
        videos_path = configuracion.VIDEO_EVIDENCE_PATH / "clips"
        videos_sin_comprimir = []
        
        # Buscar videos sin comprimir
        for video in videos_path.glob("*.mp4"):
            if "_compressed" not in video.stem:
                tamaño_mb = video.stat().st_size / (1024 * 1024)
                if tamaño_mb > 50:  # Videos mayores a 50MB
                    videos_sin_comprimir.append(video)
        
        logger.info(f"Videos para comprimir: {len(videos_sin_comprimir)}")
        
        # Comprimir videos
        for video in videos_sin_comprimir:
            video_comprimido = await comprimir_video_evidencia(video, "media")
            
            if video_comprimido:
                # Reemplazar original con comprimido
                video.unlink()
                video_comprimido.rename(video)
                logger.info(f"Video optimizado: {video}")
            
            # Dar tiempo entre compresiones
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error en optimización de almacenamiento: {e}")


async def verificar_integridad_sistema():
    """Verifica la integridad del sistema y reporta problemas"""
    problemas = []
    
    try:
        # Verificar directorios necesarios
        directorios_requeridos = [
            configuracion.MODELOS_PATH,
            configuracion.UPLOAD_PATH,
            configuracion.VIDEO_EVIDENCE_PATH,
            configuracion.VIDEO_EVIDENCE_PATH / "clips",
            configuracion.VIDEO_EVIDENCE_PATH / "frames"
        ]
        
        for directorio in directorios_requeridos:
            if not directorio.exists():
                problemas.append(f"Directorio faltante: {directorio}")
                directorio.mkdir(parents=True, exist_ok=True)
        
        # Verificar modelos
        modelos_requeridos = [
            configuracion.obtener_ruta_modelo(configuracion.YOLO_MODEL),
            configuracion.obtener_ruta_modelo(configuracion.TIMESFORMER_MODEL)
        ]
        
        for modelo in modelos_requeridos:
            if not modelo.exists():
                problemas.append(f"Modelo faltante: {modelo}")
        
        # Verificar espacio en disco
        import shutil
        total, usado, libre = shutil.disk_usage("/")
        espacio_libre_gb = libre / (1024 ** 3)
        
        if espacio_libre_gb < 10:  # Menos de 10GB libres
            problemas.append(f"Espacio en disco bajo: {espacio_libre_gb:.2f} GB libres")
        
        # Reportar resultados
        if problemas:
            logger.warning(f"Problemas detectados en verificación: {len(problemas)}")
            for problema in problemas:
                logger.warning(f"- {problema}")
        else:
            logger.info("Verificación de integridad completada sin problemas")
        
        return {"estado": "ok" if not problemas else "warning", "problemas": problemas}
        
    except Exception as e:
        logger.error(f"Error en verificación de integridad: {e}")
        return {"estado": "error", "problemas": [str(e)]}


async def ejecutar_mantenimiento_diario():
    """Ejecuta todas las tareas de mantenimiento diario"""
    logger.info("Iniciando mantenimiento diario del sistema")
    
    tareas = [
        ("Limpieza de archivos temporales", limpiar_archivos_temporales()),
        ("Limpieza de videos antiguos", limpiar_videos_antiguos()),
        ("Optimización de almacenamiento", optimizar_almacenamiento()),
        ("Verificación de integridad", verificar_integridad_sistema())
    ]
    
    for nombre, tarea in tareas:
        try:
            logger.info(f"Ejecutando: {nombre}")
            await tarea
            logger.info(f"Completado: {nombre}")
        except Exception as e:
            logger.error(f"Error en {nombre}: {e}")
    
    logger.info("Mantenimiento diario completado")


# Función para programar tareas periódicas
async def programar_tareas_periodicas():
    """Programa la ejecución periódica de tareas de mantenimiento"""
    while True:
        # Calcular tiempo hasta próxima ejecución (3 AM)
        ahora = datetime.now()
        proxima_ejecucion = ahora.replace(hour=3, minute=0, second=0, microsecond=0)
        
        if proxima_ejecucion <= ahora:
            proxima_ejecucion += timedelta(days=1)
        
        tiempo_espera = (proxima_ejecucion - ahora).total_seconds()
        
        logger.info(f"Próximo mantenimiento en {tiempo_espera/3600:.2f} horas")
        
        # Esperar hasta la próxima ejecución
        await asyncio.sleep(tiempo_espera)
        
        # Ejecutar mantenimiento
        await ejecutar_mantenimiento_diario()