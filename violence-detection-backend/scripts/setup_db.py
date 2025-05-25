"""
Script para configurar la base de datos inicial
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base, obtener_db
from app.config import configuracion
from app.models import *  # Importar todos los modelos
from app.models.user import Usuario, RolUser  # Importar el Enum RolUser
from app.models.camera import Camara, TipoCamara, EstadoCamara  # Importar los Enums
from app.core.security import obtener_hash_password
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


async def crear_tablas():
    """Crea todas las tablas en la base de datos"""
    engine = create_async_engine(configuracion.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Crear todas las tablas
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    logger.info("Tablas creadas exitosamente")


async def crear_usuario_admin():
    """Crea un usuario administrador inicial"""
    async for db in obtener_db():
        try:
            # Verificar si ya existe un admin
            from sqlalchemy import select
            
            resultado = await db.execute(
                select(Usuario).where(Usuario.email == "admin@usfx.com")
            )
            
            if resultado.scalars().first():
                logger.info("Usuario admin ya existe")
                return
            
            # Crear usuario admin
            admin = Usuario(
                nombre_completo="Administrador Sistema",
                email="admin@usfx.com",
                password_hash=obtener_hash_password("gonzales123"),
                rol=RolUser.ADMIN,  # Usar Enum
                activo=True,
                cargo="Administrador del Sistema"
            )
            
            db.add(admin)
            await db.commit()
            
            logger.info("Usuario administrador creado")
            logger.info("Email: admin@usfx.com")
            logger.info("Contraseña: gonzales123 (CAMBIAR EN PRODUCCIÓN)")
            
        except Exception as e:
            logger.error(f"Error al crear usuario admin: {e}")
            await db.rollback()
        finally:
            await db.close()


async def insertar_datos_prueba():
    """Inserta datos de prueba en la base de datos"""
    async for db in obtener_db():
        try:
            # Crear cámaras de prueba
            camaras = [
                Camara(
                    nombre="Cámara Principal",
                    ubicacion="Entrada Principal",
                    descripcion="Cámara USB Trust Taxon 2K",
                    tipo_camara=TipoCamara.USB,  # Usar Enum
                    estado=EstadoCamara.INACTIVA  # Usar Enum
                ),
                Camara(
                    nombre="Cámara Patio",
                    ubicacion="Patio Central",
                    descripcion="Vista del patio principal",
                    tipo_camara=TipoCamara.IP,  # Usar Enum
                    estado=EstadoCamara.INACTIVA  # Usar Enum
                ),
                Camara(
                    nombre="Cámara Pasillo A",
                    ubicacion="Pasillo Edificio A",
                    descripcion="Monitoreo de pasillo",
                    tipo_camara=TipoCamara.USB,  # Usar Enum
                    estado=EstadoCamara.INACTIVA  # Usar Enum
                )
            ]
            
            for camara in camaras:
                db.add(camara)
            
            await db.commit()
            logger.info("Datos de prueba insertados")
            
        except Exception as e:
            logger.error(f"Error al insertar datos de prueba: {e}")
            await db.rollback()
        finally:
            await db.close()


async def main():
    """Función principal del script"""
    logger.info("Iniciando configuración de base de datos")
    
    # Crear tablas
    await crear_tablas()
    
    # Crear usuario administrador
    await crear_usuario_admin()
    
    # Insertar datos de prueba
    respuesta = input("¿Desea insertar datos de prueba? (s/n): ")
    if respuesta.lower() == 's':
        await insertar_datos_prueba()
    
    logger.info("Configuración completada")


if __name__ == "__main__":
    asyncio.run(main())