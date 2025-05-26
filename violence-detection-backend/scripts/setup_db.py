"""
Script para configurar la base de datos inicial
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional, List

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text, select
from app.core.database import Base, obtener_db
from app.config import configuracion
from app.models import *  # Importar todos los modelos
from app.models.user import Usuario, RolUser
from app.models.camera import Camara, TipoCamara, EstadoCamara
from app.core.security import obtener_hash_password
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


async def verificar_conexion(engine: AsyncEngine) -> bool:
    """Verifica la conexión a la base de datos"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Conexión a la base de datos verificada")
            print("Conexión a la base de datos verificada")
            return True
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        print(f"Error al conectar a la base de datos: {e}")
        return False


async def crear_tablas() -> bool:
    """Crea todas las tablas en la base de datos"""
    try:
        engine = create_async_engine(
            configuracion.DATABASE_URL,
            echo=configuracion.DB_ECHO,
            pool_pre_ping=True,
            pool_size=configuracion.DB_POOL_SIZE,
            max_overflow=configuracion.DB_MAX_OVERFLOW
        )

        # Verificar conexión primero
        if not await verificar_conexion(engine):
            return False
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        await engine.dispose()
        logger.info("Tablas creadas exitosamente")
        print("Tablas creadas exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error al crear tablas: {e}")
        print(f"Error al crear tablas: {e}")
        return False


async def crear_usuario_admin() -> Optional[Usuario]:
    """Crea un usuario administrador inicial"""
    async for db in obtener_db():
        try:
            # Verificar si ya existe un admin
            resultado = await db.execute(
                select(Usuario).where(Usuario.email == "admin@usfx.com")
            )
            
            admin = resultado.scalars().first()
            if admin:
                logger.info("Usuario admin ya existe")
                print("Usuario admin ya existe")
                return admin
            
            # Crear usuario admin
            admin = Usuario(
                nombre_completo="Carlos Gonzales",
                user_name="carlitos",
                email="admin@usfx.com",
                password_hash=obtener_hash_password("carlitos123"),
                rol=RolUser.ADMIN,
                activo=True,
                cargo="Administrador del Sistema"
            )
            
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            
            logger.info("✅ Usuario administrador creado exitosamente")
            print("✅ Usuario administrador creado exitosamente")
            logger.info("📧 Email: admin@usfx.com")
            print("📧 Email: admin@usfx.com")
            logger.info("🔑 Contraseña: gonzales123 (¡CAMBIAR EN PRODUCCIÓN!)")
            print("🔑 Contraseña: gonzales123 (¡CAMBIAR EN PRODUCCIÓN!)")
            
            return admin
            
        except Exception as e:
            logger.error(f"❌ Error al crear usuario admin: {e}")
            print(f"❌ Error al crear usuario admin: {e}")
            await db.rollback()
            return None
        finally:
            await db.close()


async def insertar_datos_prueba() -> bool:
    """Inserta datos de prueba en la base de datos"""
    async for db in obtener_db():
        try:
            # Crear cámaras de prueba
            camaras: List[Camara] = [
                Camara(
                    nombre="Cámara Principal",
                    ubicacion="Entrada Principal",
                    descripcion="Cámara USB Trust Taxon 2K",
                    tipo_camara=TipoCamara.USB,
                    estado=EstadoCamara.INACTIVA
                ),
                Camara(
                    nombre="Cámara Patio",
                    ubicacion="Patio Central",
                    descripcion="Vista del patio principal",
                    tipo_camara=TipoCamara.IP,
                    estado=EstadoCamara.INACTIVA
                ),
                Camara(
                    nombre="Cámara Pasillo A",
                    ubicacion="Pasillo Edificio A",
                    descripcion="Monitoreo de pasillo",
                    tipo_camara=TipoCamara.USB,
                    estado=EstadoCamara.INACTIVA
                )
            ]
            
            db.add_all(camaras)
            await db.commit()
            
            logger.info(f"✅ {len(camaras)} cámaras de prueba insertadas")
            print(f"✅ {len(camaras)} cámaras de prueba insertadas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al insertar datos de prueba: {e}")
            print(f"❌ Error al insertar datos de prueba: {e}")
            await db.rollback()
            return False
        finally:
            await db.close()


async def main():
    """Función principal del script"""
    logger.info("🚀 Iniciando configuración de base de datos")
    print("🚀 Iniciando configuración de base de datos")
    
    # Crear tablas
    if not await crear_tablas():
        logger.error("❌ Error al crear tablas. Abortando...")
        print("❌ Error al crear tablas. Abortando...")
        return
    
    # Crear usuario administrador
    admin = await crear_usuario_admin()
    if not admin:
        logger.error("❌ Error al crear usuario admin. Abortando...")
        print("❌ Error al crear usuario admin. Abortando...")
        return
    
    # Insertar datos de prueba
    respuesta = input("\n¿Desea insertar datos de prueba? (s/n): ").lower()
    if respuesta == 's':
        if await insertar_datos_prueba():
            logger.info("✅ Datos de prueba insertados correctamente")
            print("✅ Datos de prueba insertados correctamente")
        else:
            logger.error("❌ Error al insertar datos de prueba")
            print("❌ Error al insertar datos de prueba")
    
    logger.info("✅ Configuración completada exitosamente")
    print("✅ Configuración completada exitosamente")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Proceso interrumpido por el usuario")
        print("\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        print(f"❌ Error inesperado: {e}")