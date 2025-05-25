"""
Configuración de la base de datos
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import configuracion

# Motor de base de datos asíncrono
motor = create_async_engine(
    configuracion.DATABASE_URL,
    echo=configuracion.DB_ECHO,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40
)

# Sesión asíncrona
SesionAsincrona = async_sessionmaker(
    motor,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base para los modelos
Base = declarative_base()


async def obtener_db() -> AsyncGenerator[AsyncSession, None]:
    """Generador de sesiones de base de datos"""
    async with SesionAsincrona() as sesion:
        try:
            yield sesion
            await sesion.commit()
        except Exception:
            await sesion.rollback()
            raise
        finally:
            await sesion.close()


async def inicializar_db():
    """Inicializa la base de datos creando las tablas"""
    async with motor.begin() as conexion:
        await conexion.run_sync(Base.metadata.create_all)


async def cerrar_db():
    """Cierra las conexiones de la base de datos"""
    await motor.dispose()