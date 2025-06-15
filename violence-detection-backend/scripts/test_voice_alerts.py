# scripts/test_voice_alerts.py - Script para probar alertas de voz

"""
Script de prueba para el sistema de alertas de voz - ACTUALIZADO SIN VERIFICACIÓN DE CRÉDITOS
"""
import asyncio
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# *** AGREGAR: Cargar variables de entorno desde .env ***
from dotenv import load_dotenv
load_dotenv(root_dir / ".env")

from app.services.voice_alert_service import ServicioAlertasVoz
from app.config import configuracion


async def probar_alertas_voz():
    """Prueba completa del sistema de alertas de voz - SIN VERIFICACIÓN DE CRÉDITOS"""
    print("🎙️ Iniciando pruebas del sistema de alertas de voz...")
    
    # Crear instancia del servicio
    servicio = ServicioAlertasVoz()
    
    # Verificar estado inicial
    estado = servicio.obtener_estado()
    print(f"\n📊 Estado inicial del servicio:")
    for key, value in estado.items():
        print(f"   - {key}: {value}")
    
    if not servicio.habilitado:
        print("\n❌ El servicio de alertas de voz no está habilitado.")
        print("   Verifica que ELEVENLABS_API_KEY esté configurada en el archivo .env")
        return
    
    print(f"\n✅ Servicio habilitado. Iniciando pruebas...")
    
    # Prueba 1: Alerta básica (SIN verificación de créditos)
    print(f"\n🧪 Prueba 1: Alerta básica (sin verificación de créditos)")
    success = await servicio.emitir_alerta_violencia(
        ubicacion="Patio Principal",
        probabilidad=0.85,
        personas_detectadas=2
    )
    print(f"   Resultado: {'✅ Exitosa' if success else '❌ Falló'}")
    
    # Esperar un poco
    await asyncio.sleep(3)
    
    # Prueba 2: Alerta crítica
    print(f"\n🧪 Prueba 2: Alerta crítica (alta probabilidad)")
    success = await servicio.emitir_alerta_violencia(
        ubicacion="Aula 201",
        probabilidad=0.95,
        personas_detectadas=3,
        forzar=True  # Forzar para ignorar cooldown
    )
    print(f"   Resultado: {'✅ Exitosa' if success else '❌ Falló'}")
    
    # Esperar un poco
    await asyncio.sleep(3)
    
    # Prueba 3: Alerta con cooldown
    print(f"\n🧪 Prueba 3: Alerta con cooldown (debería fallar)")
    success = await servicio.emitir_alerta_violencia(
        ubicacion="Cafetería",
        probabilidad=0.75,
        personas_detectadas=1
    )
    print(f"   Resultado: {'✅ Exitosa' if success else '❌ Falló (esperado por cooldown)'}")
    
    # Prueba 4: Configurar cooldown
    print(f"\n🧪 Prueba 4: Configurar cooldown corto")
    servicio.configurar_cooldown(5)  # 5 segundos
    estado_nuevo = servicio.obtener_estado()
    print(f"   Cooldown configurado a: {estado_nuevo['cooldown_segundos']}s")
    
    # Esperar y probar nuevamente
    print(f"   Esperando 6 segundos...")
    await asyncio.sleep(6)
    
    success = await servicio.emitir_alerta_violencia(
        ubicacion="Biblioteca",
        probabilidad=0.80,
        personas_detectadas=2
    )
    print(f"   Resultado después del cooldown: {'✅ Exitosa' if success else '❌ Falló'}")
    
    # Estado final
    estado_final = servicio.obtener_estado()
    print(f"\n📊 Estado final del servicio:")
    for key, value in estado_final.items():
        print(f"   - {key}: {value}")
    
    # Limpiar recursos
    servicio.cerrar()
    print(f"\n✅ Pruebas completadas. Servicio cerrado.")


async def probar_configuracion():
    """Prueba la configuración del sistema"""
    print("⚙️ Verificando configuración del sistema de alertas de voz...")
    
    # Verificar variables de entorno
    api_key = os.getenv('ELEVENLABS_API_KEY')
    print(f"   ELEVENLABS_API_KEY: {'✅ Configurada' if api_key else '❌ No configurada'}")
    
    if api_key:
        print(f"   API Key (primeros 10 chars): {api_key[:10]}...")
    
    # *** AGREGAR: Debug de configuración ***
    print(f"   Configuración desde config.py: {'✅ Disponible' if hasattr(configuracion, 'ELEVENLABS_API_KEY') and configuracion.ELEVENLABS_API_KEY else '❌ No disponible'}")
    
    # Verificar dependencias
    dependencias = {
        'elevenlabs': False,
        'sounddevice': False,
        'numpy': False,
        'scipy': False
    }
    
    for dep in dependencias:
        try:
            __import__(dep)
            dependencias[dep] = True
        except ImportError:
            pass
    
    print(f"\n📦 Dependencias:")
    for dep, disponible in dependencias.items():
        print(f"   - {dep}: {'✅ Disponible' if disponible else '❌ No disponible'}")
    
    # Verificar dispositivos de audio
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        print(f"\n🔊 Dispositivos de audio encontrados: {len(devices)}")
        
        # Mostrar dispositivo por defecto
        default_device = sd.default.device
        print(f"   Dispositivo por defecto: {default_device}")
    except Exception as e:
        print(f"\n❌ Error verificando dispositivos de audio: {e}")
    
    return all(dependencias.values()) and api_key is not None


async def main():
    """Función principal"""
    print("🎯 Sistema de Pruebas - Alertas de Voz (SIN verificación de créditos)")
    print("=" * 70)
    
    # *** AGREGAR: Verificar que se cargó el .env ***
    print(f"📁 Archivo .env cargado desde: {root_dir / '.env'}")
    print(f"🔑 Variables cargadas: {len([k for k in os.environ.keys() if k.startswith(('ELEVENLABS', 'VOICE'))])} relacionadas con voz")
    
    # Verificar configuración primero
    config_ok = await probar_configuracion()
    
    if not config_ok:
        print(f"\n❌ La configuración no es correcta. Instala las dependencias faltantes:")
        print("   pip install elevenlabs sounddevice scipy")
        print("   Y configura ELEVENLABS_API_KEY en el archivo .env")
        return
    
    print(f"\n✅ Configuración verificada. Procediendo con las pruebas...")
    
    # Ejecutar pruebas
    await probar_alertas_voz()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n⏸️ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()