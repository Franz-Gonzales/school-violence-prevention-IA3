"""
Script para visualizar datos de la base de datos
"""
import asyncio
import sys
from pathlib import Path
from typing import List

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import obtener_db
from app.models.user import Usuario
from app.models.camera import Camara
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)

async def mostrar_usuarios():
    """Muestra todos los usuarios en la base de datos"""
    async for db in obtener_db():
        try:
            resultado = await db.execute(select(Usuario))
            usuarios = resultado.scalars().all()
            
            print("\n📋 USUARIOS REGISTRADOS:")
            print("=" * 50)
            for user in usuarios:
                print(f"ID: {user.id}")
                print(f"Nombre: {user.nombre_completo}")
                print(f"Email: {user.email}")
                print(f"Rol: {user.rol.value}")
                print(f"Cargo: {user.cargo}")
                print(f"Activo: {'✅' if user.activo else '❌'}")
                print("-" * 50)
        finally:
            await db.close()

async def mostrar_camaras():
    """Muestra todas las cámaras en la base de datos"""
    async for db in obtener_db():
        try:
            resultado = await db.execute(select(Camara))
            camaras = resultado.scalars().all()
            
            print("\n📹 CÁMARAS REGISTRADAS:")
            print("=" * 50)
            for cam in camaras:
                print(f"ID: {cam.id}")
                print(f"Nombre: {cam.nombre}")
                print(f"Ubicación: {cam.ubicacion}")
                print(f"Descripción: {cam.descripcion}")
                print(f"Tipo: {cam.tipo_camara.value}")
                print(f"Estado: {cam.estado.value}")
                print("-" * 50)
        finally:
            await db.close()

async def main():
    """Función principal"""
    print("\n🔍 Visualizando datos de la base de datos...")
    
    await mostrar_usuarios()
    await mostrar_camaras()

if __name__ == "__main__":
    asyncio.run(main())