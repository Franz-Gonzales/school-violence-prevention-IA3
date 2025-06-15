from elevenlabs.client import ElevenLabs
import io
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import sys

# Inicializar el cliente con tu API key
client = ElevenLabs(api_key="sk_59dd5eeff1a5ee283c21e3923954840d0185d48c6dc2cd3d")

# Usar directamente la voz de Daniel
selected_voice = "onwK4e9ZLuTAKqWW03F9"  # ID de la voz de Daniel

# Frase de alerta
alerta = "¡Atención! ¡Emergencia detectada en el sector norte! ¡Evacúe de inmediato!"

# Generar el audio con tono alarmante y respuesta rápida
try:
    audio = client.text_to_speech.convert(
        voice_id=selected_voice,
        text=alerta,
        model_id="eleven_multilingual_v2",  # Modelo multilingüe para español
        output_format="pcm_22050",  # Formato PCM, 22.05kHz
        voice_settings={
            "stability": 0.3,  # Menor estabilidad para tono más urgente y dinámico
            "similarity_boost": 0.8,  # Alta claridad para voz nítida
            "style": 0.9,  # Alta exageración para un tono alarmante y enfático
            "speed": 1.2  # Velocidad máxima permitida para urgencia
        },
        optimize_streaming_latency=1  # Optimizar para baja latencia
    )
except Exception as e:
    print(f"Error al generar audio: {e}")
    sys.exit(1)  # Terminar el script si hay error

# Convertir el audio a un formato reproducible
audio_bytes = b''.join(audio)  # Combinar los fragmentos del generador

# Asumir que el audio es PCM crudo (16-bit, 22.05kHz)
sample_rate = 22050  # Frecuencia de muestreo
audio_data = np.frombuffer(audio_bytes, dtype=np.int16)  # Convertir bytes a datos PCM 16-bit

# Ajustar el volumen para mayor impacto
volume_factor = 1.8  # Aumentar el volumen en un 80%
audio_data = np.clip(audio_data * volume_factor, -32768, 32767).astype(np.int16)  # Evitar distorsión

# Reproducir el audio por el altavoz
sd.play(audio_data, sample_rate)
sd.wait()  # Esperar a que termine la reproducción

# Terminar el script inmediatamente después de la reproducción
sys.exit(0)
