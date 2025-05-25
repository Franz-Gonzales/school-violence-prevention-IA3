import psycopg2
import sys
from pathlib import Path

def test_postgres_connection():
    """Prueba la conexión a PostgreSQL y muestra información del servidor"""
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(
            database="deteccion_violencia",
            user="postgres",
            password="gonzales",
            host="localhost",
            port="5432"
        )
        
        # Crear un cursor
        cur = conn.cursor()
        
        # Obtener versión
        cur.execute('SELECT version()')
        version = cur.fetchone()[0]
        
        # Obtener bases de datos
        cur.execute("""
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false;
        """)
        databases = [row[0] for row in cur.fetchall()]
        
        # Imprimir información
        print("\n✅ ¡Conexión exitosa!")
        print("\nInformación del servidor:")
        print(f"Versión: {version}")
        print("\nBases de datos disponibles:")
        for db in databases:
            print(f"- {db}")
            
        # Verificar permisos
        cur.execute("""
            SELECT has_database_privilege(current_user, current_database(), 'CREATE');
        """)
        has_create = cur.fetchone()[0]
        print(f"\nPermisos CREATE: {'Sí' if has_create else 'No'}")
        
        return True
        
    except Exception as e:
        print("\n❌ Error al conectar:")
        print(f"Error: {str(e)}")
        return False
        
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals() and conn is not None:
            conn.close()
            print("\nConexión cerrada.")

if __name__ == "__main__":
    success = test_postgres_connection()
    
    if success:
        print("\n📝 Usa esta configuración en tu archivo .env:")
        print("DATABASE_URL=postgresql+asyncpg://postgres:gonzales@localhost:5432/violence_detection_db")
