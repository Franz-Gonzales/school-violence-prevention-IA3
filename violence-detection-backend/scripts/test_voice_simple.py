"""
Script de prueba simplificado para alertas de voz
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
load_dotenv(root_dir / ".env")

import os
from elevenlabs.client import ElevenLabs
import sounddevice as sd
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor


class AlertaVozSimple:
    """Servicio de alertas de voz simplificado sin verificación de créditos"""
    
    def __init__(self):
        self.client = None
        self.voice_id = "onwK4e9ZLuTAKqWW03F9"
        self.habilitado = False
        self.ultima_alerta = 0
        self.cooldown_segundos = 15
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._inicializar_cliente()
    
    def _inicializar_cliente(self):
        """Inicializa el cliente de ElevenLabs"""
        try:
            api_key = os.getenv('ELEVENLABS_API_KEY')
            if not api_key:
                print("❌ API Key de ElevenLabs no configurada")
                return
            
            self.client = ElevenLabs(api_key=api_key)
            self.habilitado = True
            print("✅ Cliente ElevenLabs inicializado correctamente")
            
        except Exception as e:
            print(f"❌ Error inicializando cliente: {e}")
            self.habilitado = False
    
    def _generar_mensaje_alerta(self, ubicacion: str, probabilidad: float, personas: int) -> str:
        """Genera el mensaje de alerta"""
        probabilidad_pct = int(probabilidad * 100)
        
        if probabilidad >= 0.9:
            base = "¡¡ALERTA CRÍTICA!! ¡¡VIOLENCIA EXTREMA DETECTADA!!"
        elif probabilidad >= 0.8:
            base = "¡¡ALERTA ALTA!! ¡¡VIOLENCIA DETECTADA!!"
        else:
            base = "¡ALERTA! ¡ACTIVIDAD VIOLENTA DETECTADA!"
        
        mensaje = f"{base} ¡¡UBICACIÓN: {ubicacion.upper()}!! "
        mensaje += f"¡¡PROBABILIDAD: {probabilidad_pct} POR CIENTO!! "
        
        if personas > 0:
            mensaje += f"¡¡{personas} PERSONAS INVOLUCRADAS!! "
        
        mensaje += "¡SEGURIDAD RESPONDA INMEDIATAMENTE!"
        
        return mensaje
    
    def _reproducir_audio_sync(self, audio_data: bytes) -> bool:
        """Reproduce audio de forma síncrona"""
        try:
            # Convertir bytes a numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Ajustar volumen
            volume_factor = 1.8
            audio_array = np.clip(audio_array * volume_factor, -32768, 32767).astype(np.int16)
            
            # Reproducir
            sample_rate = 22050
            sd.play(audio_array, sample_rate)
            sd.wait()
            
            print("🔊 Alerta de voz reproducida exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error reproduciendo audio: {e}")
            return False
    
    def _generar_y_reproducir_alerta(self, mensaje: str) -> bool:
        """Genera y reproduce la alerta de voz (SIN verificar créditos)"""
        try:
            if not self.client:
                print("⚠️ Cliente de ElevenLabs no disponible")
                return False
            
            print(f"🎙️ Generando alerta: {mensaje[:50]}...")
            
            # *** GENERAR AUDIO DIRECTAMENTE (como en altavoz.py) ***
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=mensaje,
                model_id="eleven_multilingual_v2",
                output_format="pcm_22050",
                voice_settings={
                    "stability": 0.3,
                    "similarity_boost": 0.8,
                    "style": 0.9,
                    "speed": 1.2
                },
                optimize_streaming_latency=1
            )
            
            # Combinar fragmentos de audio
            audio_bytes = b''.join(audio_generator)
            
            if not audio_bytes:
                print("❌ No se generó audio")
                return False
            
            # Reproducir inmediatamente
            return self._reproducir_audio_sync(audio_bytes)
            
        except Exception as e:
            print(f"❌ Error generando/reproduciendo alerta: {e}")
            return False
    
    async def emitir_alerta_violencia(
        self, 
        ubicacion: str, 
        probabilidad: float, 
        personas_detectadas: int = 0,
        forzar: bool = False
    ) -> bool:
        """Emite una alerta de voz (SIN verificar créditos)"""
        if not self.habilitado:
            print("❌ Servicio no habilitado")
            return False
        
        current_time = time.time()
        
        # Verificar cooldown
        if not forzar and (current_time - self.ultima_alerta) < self.cooldown_segundos:
            tiempo_restante = self.cooldown_segundos - (current_time - self.ultima_alerta)
            print(f"⏳ Alerta en cooldown. {tiempo_restante:.1f}s restantes")
            return False
        
        try:
            # Generar mensaje
            mensaje = self._generar_mensaje_alerta(ubicacion, probabilidad, personas_detectadas)
            
            print(f"🚨 EMITIENDO ALERTA DE VOZ - Ubicación: {ubicacion}")
            
            # *** EJECUTAR DIRECTAMENTE SIN VERIFICAR CRÉDITOS ***
            future = self.executor.submit(self._generar_y_reproducir_alerta, mensaje)
            self.ultima_alerta = current_time
            
            def callback(future_result):
                try:
                    success = future_result.result(timeout=30)
                    if success:
                        print(f"✅ Alerta emitida exitosamente para {ubicacion}")
                    else:
                        print(f"⚠️ Falló la emisión de alerta para {ubicacion}")
                except Exception as e:
                    print(f"❌ Error en callback: {e}")
            
            future.add_done_callback(callback)
            return True
                
        except Exception as e:
            print(f"❌ Error emitiendo alerta: {e}")
            return False
    
    def cerrar(self):
        """Cierra el servicio"""
        self.executor.shutdown(wait=False)
        print("🔇 Servicio cerrado")


async def probar_alertas_simplificadas():
    """Prueba el sistema simplificado"""
    print("🎯 Probando alertas de voz simplificadas (sin verificación de créditos)")
    print("=" * 70)
    
    # Crear servicio
    servicio = AlertaVozSimple()
    
    if not servicio.habilitado:
        print("❌ Servicio no disponible")
        return
    
    print("✅ Servicio inicializado. Iniciando pruebas...")
    
    # Prueba 1
    print("\n🧪 Prueba 1: Alerta básica")
    success = await servicio.emitir_alerta_violencia(
        ubicacion="Patio Principal",
        probabilidad=0.85,
        personas_detectadas=2
    )
    print(f"   Resultado: {'✅ Exitosa' if success else '❌ Falló'}")
    
    await asyncio.sleep(3)
    
    # Prueba 2
    print("\n🧪 Prueba 2: Alerta crítica")
    success = await servicio.emitir_alerta_violencia(
        ubicacion="Aula 201",
        probabilidad=0.95,
        personas_detectadas=3,
        forzar=True
    )
    print(f"   Resultado: {'✅ Exitosa' if success else '❌ Falló'}")
    
    servicio.cerrar()
    print("\n✅ Pruebas completadas")


if __name__ == "__main__":
    try:
        asyncio.run(probar_alertas_simplificadas())
    except KeyboardInterrupt:
        print("\n⏸️ Pruebas interrumpidas")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()