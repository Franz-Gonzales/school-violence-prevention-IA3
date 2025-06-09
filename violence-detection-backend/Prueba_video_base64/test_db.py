"""
Script para probar la conexión a la base de datos
"""
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal
from app.models import Video
from sqlalchemy import text

def test_database_connection():
    """Prueba la conexión a PostgreSQL"""
    print("🔍 Probando conexión a la base de datos...")
    
    try:
        # Probar conexión básica
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL conectado: {version[:50]}...")
        
        # Probar sesión de SQLAlchemy
        db = SessionLocal()
        try:
            # Verificar tabla videos
            video_count = db.query(Video).count()
            print(f"✅ Tabla 'videos' encontrada con {video_count} registros")
            
            # Probar inserción de prueba
            test_video = Video(
                filename="test.mp4",
                video_base64="dGVzdCBkYXRh",  # "test data" en base64
                duration=5.0,
                file_size=1024
            )
            
            db.add(test_video)
            db.commit()
            
            # Verificar inserción
            saved_video = db.query(Video).filter_by(filename="test.mp4").first()
            if saved_video:
                print(f"✅ Inserción de prueba exitosa, ID: {saved_video.id}")
                
                # Limpiar registro de prueba
                db.delete(saved_video)
                db.commit()
                print("🗑️ Registro de prueba eliminado")
            
        finally:
            db.close()
        
        print("🎉 ¡Todas las pruebas de base de datos pasaron!")
        return True
        
    except Exception as e:
        print(f"❌ Error en la base de datos: {e}")
        print("\n🔧 Posibles soluciones:")
        print("1. Verificar que PostgreSQL esté ejecutándose")
        print("2. Comprobar credenciales en app/database.py")
        print("3. Verificar que la base de datos 'video_recorder_db' existe")
        print("4. Ejecutar create_db.sql")
        return False

def show_connection_info():
    """Muestra información de conexión"""
    from app.database import DATABASE_URL
    print(f"📡 URL de conexión: {DATABASE_URL}")
    print(f"🏠 Host: localhost")
    print(f"🔐 Usuario: postgres")
    print(f"🗄️ Base de datos: video_recorder_db")

if __name__ == "__main__":
    print("=== 🧪 PRUEBA DE BASE DE DATOS ===")
    show_connection_info()
    print()
    
    if test_database_connection():
        sys.exit(0)
    else:
        sys.exit(1)