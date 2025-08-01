"""
Configuración de la base de datos
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from app.config import configuracion
from app.utils.logger import obtener_logger
import asyncio

logger = obtener_logger(__name__)

# Motor de base de datos asíncrono
motor = create_async_engine(
    configuracion.DATABASE_URL,
    echo=configuracion.DB_ECHO,
    pool_pre_ping=True,
    pool_size=configuracion.DB_POOL_SIZE,
    max_overflow=configuracion.DB_MAX_OVERFLOW,
    pool_timeout=configuracion.DB_POOL_TIMEOUT,
    pool_recycle=configuracion.DB_POOL_RECYCLE,
    # AÑADIR CONFIGURACIÓN PARA EVITAR PROBLEMAS DE LOOP
    pool_reset_on_return='commit',
    future=True
)

# Sesión asíncrona
SesionAsincrona = async_sessionmaker(
    motor,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False  # Evitar auto-flush para mejor control
)

# Base para los modelos
Base = declarative_base()


async def obtener_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generador de sesiones de base de datos.
    
    Yields:
        AsyncSession: Sesión asíncrona de SQLAlchemy
    
    Raises:
        SQLAlchemyError: Si ocurre un error en la base de datos
    """
    async with SesionAsincrona() as sesion:
        try:
            yield sesion
            await sesion.commit()
        except SQLAlchemyError as e:
            await sesion.rollback()
            logger.error(f"Error en la sesión de base de datos: {str(e)}")
            print(f"Error en la sesión de base de datos: {str(e)}")
            raise
        except Exception as e:
            await sesion.rollback()
            logger.error(f"Error inesperado: {str(e)}")
            print(f"Error inesperado: {str(e)}")
            raise
        finally:
            await sesion.close()


async def inicializar_db():
    """
    Inicializa la base de datos creando todas las tablas.
    
    Raises:
        SQLAlchemyError: Si hay un error al crear las tablas
    """
    try:
        async with motor.begin() as conexion:
            await conexion.run_sync(Base.metadata.create_all)
            logger.info("Base de datos inicializada exitosamente")
            print("Base de datos inicializada exitosamente")
    except SQLAlchemyError as e:
        logger.error(f"Error al inicializar la base de datos: {str(e)}")
        print(f"Error al inicializar la base de datos: {str(e)}")
        raise


async def cerrar_db():
    """
    Cierra todas las conexiones del pool de la base de datos de forma segura.
    """
    try:
        # CIERRE MEJORADO PARA EVITAR ERRORES DE LOOP
        await motor.dispose()
        
        # Dar tiempo para que se cierren completamente
        await asyncio.sleep(0.5)
        
        logger.info("✅ Conexiones de base de datos cerradas correctamente")
        print("✅ Conexiones de base de datos cerradas correctamente")
        
    except Exception as e:
        # No mostrar error de loop cerrado ya que es esperado durante shutdown
        if "Event loop is closed" not in str(e):
            logger.error(f"❌ Error al cerrar conexiones de base de datos: {str(e)}")
            print(f"❌ Error al cerrar conexiones de base de datos: {str(e)}")