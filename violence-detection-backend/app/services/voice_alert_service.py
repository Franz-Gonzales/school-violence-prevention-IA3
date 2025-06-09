# app/services/voice_alert_service.py
"""
Servicio de alertas de voz usando ElevenLabs
"""
import asyncio
import threading
import time
from typing import Optional, Dict, Any
from elevenlabs.client import ElevenLabs
import sounddevice as sd
import numpy as np
from datetime import datetime, timedelta
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class ServicioAlertasVoz:
    """Servicio para alertas de voz en tiempo real"""
    
    def __init__(self):
        self.client = None
        self.voice_id = "onwK4e9ZLuTAKqWW03F9"  # ID de la voz de Daniel
        self.habilitado = False
        self.ultima_alerta = 0
        self.cooldown_segundos = 15  # Evitar spam de alertas
        self.executor = None
        self._inicializar_cliente()
    
    def _inicializar_cliente(self):
        """Inicializa el cliente de ElevenLabs"""
        try:
            api_key = configuracion.ELEVENLABS_API_KEY
            if not api_key:
                logger.warning("API Key de ElevenLabs no configurada. Alertas de voz deshabilitadas.")
                print("⚠️ API Key de ElevenLabs no configurada. Alertas de voz deshabilitadas.")
                return
            
            self.client = ElevenLabs(api_key=api_key)
            self.habilitado = True
            
            # Crear executor para threading
            from concurrent.futures import ThreadPoolExecutor
            self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="voice_alert")
            
            logger.info("✅ Servicio de alertas de voz inicializado correctamente")
            print("✅ Servicio de alertas de voz inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error al inicializar servicio de voz: {e}")
            print(f"❌ Error al inicializar servicio de voz: {e}")
            self.habilitado = False
    
    def _generar_mensaje_alerta(self, ubicacion: str, probabilidad: float, personas: int) -> str:
        """Genera el mensaje de alerta personalizado"""
        probabilidad_pct = int(probabilidad * 100)
        
        # Mensajes base según severidad
        if probabilidad >= 0.9:
            base = "¡¡ALERTA CRÍTICA!! ¡¡VIOLENCIA EXTREMA DETECTADA!!"
        elif probabilidad >= 0.8:
            base = "¡¡ALERTA ALTA!! ¡¡VIOLENCIA DETECTADA!!"
        elif probabilidad >= 0.60:
            base = "¡¡ATENCIÓN!! ¡¡INCIDENTE VIOLENTO DETECTADO!!"
        else:
            base = "¡ALERTA! ¡ACTIVIDAD VIOLENTA DETECTADA!"
        
        # Construir mensaje completo
        mensaje_partes = [
            base,
            f"¡¡UBICACIÓN INMEDIATA: {ubicacion.upper()}!!",
            f"¡¡PROBABILIDAD: {probabilidad_pct} POR CIENTO!!",
        ]
        
        if personas > 0:
            if personas == 1:
                mensaje_partes.append("¡¡DOS PERSONAS INVOLUCRADAS!!")
            elif personas == 2:	
                mensaje_partes.append("¡¡DOS PERSONAS INVOLUCRADAS!!")
            else:
                mensaje_partes.append(f"¡¡{personas} PERSONAS INVOLUCRADAS!!")
        
        mensaje_partes.extend([
            "¡SEGURIDAD! ¡RESPONDAN INMEDIATAMENTE!",
            "¡ACTIVANDO PROTOCOLOS DE EMERGENCIA AHORA!",
        ])
        
        return " ".join(mensaje_partes)
    
    def _reproducir_audio_sync(self, audio_data: bytes) -> bool:
        """Reproduce audio de forma síncrona"""
        try:
            # Convertir bytes a numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Ajustar volumen para mayor impacto
            volume_factor = 1.8
            audio_array = np.clip(audio_array * volume_factor, -32768, 32767).astype(np.int16)
            
            # Reproducir
            sample_rate = 22050
            sd.play(audio_array, sample_rate)
            sd.wait()  # Esperar a que termine
            
            print("🔊 Alerta de voz reproducida exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error reproduciendo audio: {e}")
            print(f"❌ Error reproduciendo audio: {e}")
            return False
    
    def _generar_y_reproducir_alerta(self, mensaje: str) -> bool:
        """Genera y reproduce la alerta de voz de forma síncrona"""
        try:
            if not self.client:
                print("⚠️ Cliente de ElevenLabs no disponible")
                return False
            
            print(f"🎙️ Generando alerta de voz: {mensaje[:50]}...")
            
            # Generar audio con configuración optimizada para alertas
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=mensaje,
                model_id="eleven_multilingual_v2",
                output_format="pcm_22050",
                voice_settings={
                    "stability": 0.3,      # Menos estabilidad para tono urgente
                    "similarity_boost": 0.8, # Alta claridad
                    "style": 0.9,          # Máxima expresividad para urgencia
                    "speed": 1.17           # Velocidad ligeramente aumentada
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
            logger.error(f"❌ Error generando/reproduciendo alerta: {e}")
            print(f"❌ Error generando/reproduciendo alerta: {e}")
            return False
    
    async def emitir_alerta_violencia(
        self, 
        ubicacion: str, 
        probabilidad: float, 
        personas_detectadas: int = 0,
        forzar: bool = False
    ) -> bool:
        """
        Emite una alerta de voz por violencia detectada
        
        Args:
            ubicacion: Ubicación donde se detectó la violencia
            probabilidad: Probabilidad de violencia (0.0 - 1.0)
            personas_detectadas: Número de personas involucradas
            forzar: Si True, ignora el cooldown
            
        Returns:
            True si la alerta se emitió correctamente
        """
        if not self.habilitado:
            return False
        
        current_time = time.time()
        
        # Verificar cooldown (a menos que se fuerce)
        if not forzar and (current_time - self.ultima_alerta) < self.cooldown_segundos:
            tiempo_restante = self.cooldown_segundos - (current_time - self.ultima_alerta)
            print(f"⏳ Alerta de voz en cooldown. {tiempo_restante:.1f}s restantes")
            return False
        
        try:
            # Generar mensaje personalizado
            mensaje = self._generar_mensaje_alerta(ubicacion, probabilidad, personas_detectadas)
            
            print(f"🚨 EMITIENDO ALERTA DE VOZ - Ubicación: {ubicacion}")
            print(f"📢 Mensaje: {mensaje}")
            
            # Ejecutar en thread separado para no bloquear
            if self.executor:
                future = self.executor.submit(self._generar_y_reproducir_alerta, mensaje)
                
                # Actualizar timestamp inmediatamente para evitar duplicados
                self.ultima_alerta = current_time
                
                # Log del resultado (sin esperar)
                def callback(future_result):
                    try:
                        success = future_result.result(timeout=30)
                        if success:
                            logger.info(f"✅ Alerta de voz emitida exitosamente para {ubicacion}")
                        else:
                            logger.warning(f"⚠️ Falló la emisión de alerta de voz para {ubicacion}")
                    except Exception as e:
                        logger.error(f"❌ Error en callback de alerta de voz: {e}")
                
                future.add_done_callback(callback)
                return True
            else:
                print("❌ Executor no disponible para alertas de voz")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error emitiendo alerta de voz: {e}")
            print(f"❌ Error emitiendo alerta de voz: {e}")
            return False
    
    async def probar_alerta(self, ubicacion: str = "área de prueba") -> bool:
        """Prueba el sistema de alertas de voz"""
        return await self.emitir_alerta_violencia(
            ubicacion=ubicacion,
            probabilidad=0.85,
            personas_detectadas=2,
            forzar=True
        )
    
    def configurar_cooldown(self, segundos: int):
        """Configura el tiempo de cooldown entre alertas"""
        self.cooldown_segundos = max(5, min(60, segundos))  # Entre 5 y 60 segundos
        print(f"⏱️ Cooldown de alertas de voz configurado a {self.cooldown_segundos}s")
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Obtiene el estado actual del servicio"""
        tiempo_desde_ultima = time.time() - self.ultima_alerta if self.ultima_alerta > 0 else 999
        
        return {
            "habilitado": self.habilitado,
            "cliente_conectado": self.client is not None,
            "cooldown_segundos": self.cooldown_segundos,
            "tiempo_desde_ultima_alerta": tiempo_desde_ultima,
            "puede_emitir_alerta": tiempo_desde_ultima >= self.cooldown_segundos,
            "voice_id": self.voice_id
        }
    
    def cerrar(self):
        """Cierra el servicio y libera recursos"""
        if self.executor:
            self.executor.shutdown(wait=False)
        print("🔇 Servicio de alertas de voz cerrado")


# Instancia global del servicio
servicio_alertas_voz = ServicioAlertasVoz()