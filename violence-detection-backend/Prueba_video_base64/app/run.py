# run.py
"""
Script para ejecutar la aplicación de grabación de video
"""
import uvicorn
import os
import sys

def main():
    """Función principal para ejecutar la aplicación"""
    print("=== 🎬 VIDEO RECORDER CON BASE64 ===")
    print("Iniciando servidor FastAPI...")
    print("📡 URL: http://localhost:8000")
    print("🔄 Modo desarrollo con recarga automática")
    print("❌ Presiona Ctrl+C para detener")
    print("=" * 50)
    
    try:
        # Ejecutar la aplicación con uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando la aplicación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()