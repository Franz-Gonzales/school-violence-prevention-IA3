"""
Script para verificar créditos de ElevenLabs
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
    print("🔍 Verificando créditos de ElevenLabs...")
    print("=" * 50)
    
    # Crear instancia del servicio
    servicio = ServicioAlertasVoz()
    
    if not servicio.habilitado:
        print("❌ Servicio de alertas de voz no habilitado")
        print("   Verifica que ELEVENLABS_API_KEY esté configurada")
        return
    
    # Verificar créditos
    info_creditos = servicio.verificar_creditos()
    
    if info_creditos["success"]:
        print("✅ Información de créditos obtenida:")
        print(f"   📊 Créditos disponibles: {info_creditos['creditos_disponibles']:,}")
        print(f"   📈 Cuota total: {info_creditos['cuota_total']:,}")
        print(f"   📉 Créditos usados: {info_creditos['creditos_usados']:,}")
        print(f"   📊 Porcentaje usado: {info_creditos['porcentaje_usado']}%")
        print(f"   🎯 Estado: {info_creditos['estado']}")
        
        if 'plan_tipo' in info_creditos:
            print(f"   📋 Plan: {info_creditos['plan_tipo']}")
        
        # Mostrar estimaciones
        print(f"\n📝 Estimaciones:")
        alertas_cortas = info_creditos['creditos_disponibles'] // 100  # ~100 chars por alerta corta
        alertas_largas = info_creditos['creditos_disponibles'] // 200  # ~200 chars por alerta larga
        print(f"   🔊 Alertas cortas posibles: ~{alertas_cortas}")
        print(f"   📢 Alertas largas posibles: ~{alertas_largas}")
        
    else:
        print(f"❌ Error obteniendo créditos: {info_creditos['error']}")
    
    # Probar viabilidad con mensaje de ejemplo
    print(f"\n🧪 Probando viabilidad de mensaje...")
    mensaje_prueba = "¡ALERTA! ¡VIOLENCIA DETECTADA! ¡UBICACIÓN: PATIO PRINCIPAL!"
    viabilidad = servicio.puede_generar_audio(mensaje_prueba)
    
    print(f"   📝 Mensaje de prueba: '{mensaje_prueba}'")
    print(f"   📏 Longitud: {len(mensaje_prueba)} caracteres")
    print(f"   ✅ Puede generar: {'Sí' if viabilidad['puede_generar'] else 'No'}")
    print(f"   💬 Razón: {viabilidad['razon']}")
    
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