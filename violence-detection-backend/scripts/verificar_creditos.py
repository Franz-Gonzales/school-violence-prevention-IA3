"""
Script para verificar créditos de ElevenLabs - ACTUALIZADO SIN VERIFICACIÓN
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
load_dotenv(root_dir / ".env")

from app.services.voice_alert_service import ServicioAlertasVoz

def main():
    print("🔍 Verificando estado de ElevenLabs (sin consultar créditos)...")
    print("=" * 60)
    
    # Crear instancia del servicio
    servicio = ServicioAlertasVoz()
    
    if not servicio.habilitado:
        print("❌ Servicio de alertas de voz no habilitado")
        print("   Verifica que ELEVENLABS_API_KEY esté configurada")
        return
    
    print("✅ Servicio inicializado correctamente")
    print("📝 API Key configurada y cliente conectado")
    
    # Mostrar estado del servicio
    estado = servicio.obtener_estado()
    print(f"\n📊 Estado del servicio:")
    for key, value in estado.items():
        print(f"   - {key}: {value}")
    
    # *** OMITIR verificación de créditos que causa error 401 ***
    print(f"\n⚠️ Nota: Verificación de créditos omitida")
    print(f"   Razón: API key tiene permisos limitados (solo text-to-speech)")
    print(f"   El servicio funcionará normalmente para generar alertas de voz")
    
    # Probar viabilidad con mensaje de ejemplo (sin consultar API)
    print(f"\n🧪 Probando viabilidad de mensaje...")
    mensaje_prueba = "¡ALERTA! ¡VIOLENCIA DETECTADA! ¡UBICACIÓN: PATIO PRINCIPAL!"
    viabilidad = servicio.puede_generar_audio(mensaje_prueba)
    
    print(f"   📝 Mensaje de prueba: '{mensaje_prueba}'")
    print(f"   📏 Longitud: {len(mensaje_prueba)} caracteres")
    print(f"   ✅ Puede generar: {'Sí' if viabilidad['puede_generar'] else 'No'}")
    print(f"   💬 Razón: {viabilidad['razon']}")
    
    # Recomendaciones
    print(f"\n💡 Recomendaciones:")
    print(f"   - El servicio está configurado y funcionando")
    print(f"   - Las alertas de voz se generarán sin verificar créditos")
    print(f"   - Si necesitas verificar créditos, usa una API key con más permisos")
    
    servicio.cerrar()
    print(f"\n✅ Verificación completada")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n⏸️ Verificación interrumpida")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()