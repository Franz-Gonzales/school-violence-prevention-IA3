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
                    "speed": 1.2           # Velocidad ligeramente aumentada
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
        Emite una alerta de voz por violencia detectada (con verificación de créditos)
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
            
            # *** NUEVO: Verificar créditos antes de proceder ***
            verificacion = self.puede_generar_audio(mensaje)
            if not verificacion["puede_generar"]:
                print(f"❌ No se puede generar alerta: {verificacion['razon']}")
                print(f"   Créditos necesarios: {verificacion['creditos_necesarios']}")
                print(f"   Créditos disponibles: {verificacion['creditos_disponibles']}")
                return False
            
            print(f"✅ Créditos suficientes para generar alerta")
            print(f"   Necesarios: {verificacion['creditos_necesarios']} | Disponibles: {verificacion['creditos_disponibles']}")
            
            print(f"🚨 EMITIENDO ALERTA DE VOZ - Ubicación: {ubicacion}")
            print(f"📢 Mensaje: {mensaje}")
            
            # Resto del código existente...
            if self.executor:
                future = self.executor.submit(self._generar_y_reproducir_alerta, mensaje)
                self.ultima_alerta = current_time
                
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
    
    def verificar_creditos(self) -> Dict[str, Any]:
        """
        Verifica los créditos disponibles en la cuenta de ElevenLabs
        
        Returns:
            Dict con información de créditos y estado
        """
        try:
            if not self.client:
                return {
                    "success": False,
                    "error": "Cliente de ElevenLabs no disponible",
                    "creditos_disponibles": 0,
                    "cuota_total": 0,
                    "creditos_usados": 0,
                    "porcentaje_usado": 0
                }
            
            # Hacer una solicitud a la API de usuario para obtener información de créditos
            # Nota: ElevenLabs no tiene endpoint directo de créditos, pero podemos usar el endpoint de usuario
            response = self.client.user.get()
            
            # Extraer información relevante
            subscription = response.subscription if hasattr(response, 'subscription') else None
            
            if subscription:
                character_count = subscription.character_count
                character_limit = subscription.character_limit
                creditos_restantes = character_limit - character_count
                porcentaje_usado = (character_count / character_limit) * 100 if character_limit > 0 else 0
                
                return {
                    "success": True,
                    "creditos_disponibles": creditos_restantes,
                    "cuota_total": character_limit,
                    "creditos_usados": character_count,
                    "porcentaje_usado": round(porcentaje_usado, 2),
                    "plan_tipo": subscription.tier if hasattr(subscription, 'tier') else "Unknown",
                    "estado": "activa" if creditos_restantes > 0 else "agotada",
                    "fecha_consulta": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "No se pudo obtener información de suscripción",
                    "creditos_disponibles": 0,
                    "cuota_total": 0,
                    "creditos_usados": 0,
                    "porcentaje_usado": 0
                }
                
        except Exception as e:
            logger.error(f"Error verificando créditos de ElevenLabs: {e}")
            return {
                "success": False,
                "error": f"Error en verificación: {str(e)}",
                "creditos_disponibles": 0,
                "cuota_total": 0,
                "creditos_usados": 0,
                "porcentaje_usado": 0
            }

    def puede_generar_audio(self, texto: str) -> Dict[str, Any]:
        """
        Verifica si hay suficientes créditos para generar audio con el texto dado
        
        Args:
            texto: Texto a convertir a audio
            
        Returns:
            Dict con información de viabilidad
        """
        try:
            # Estimar créditos necesarios (aproximadamente 1 crédito por caracter)
            caracteres_necesarios = len(texto)
            
            # Verificar créditos disponibles
            info_creditos = self.verificar_creditos()
            
            if not info_creditos["success"]:
                return {
                    "puede_generar": False,
                    "razon": "No se pudo verificar créditos",
                    "creditos_necesarios": caracteres_necesarios,
                    "creditos_disponibles": 0
                }
            
            creditos_disponibles = info_creditos["creditos_disponibles"]
            puede_generar = creditos_disponibles >= caracteres_necesarios
            
            return {
                "puede_generar": puede_generar,
                "razon": "Suficientes créditos" if puede_generar else "Créditos insuficientes",
                "creditos_necesarios": caracteres_necesarios,
                "creditos_disponibles": creditos_disponibles,
                "creditos_restantes_despues": creditos_disponibles - caracteres_necesarios if puede_generar else creditos_disponibles
            }
            
        except Exception as e:
            logger.error(f"Error verificando viabilidad de audio: {e}")
            return {
                "puede_generar": False,
                "razon": f"Error en verificación: {str(e)}",
                "creditos_necesarios": len(texto),
                "creditos_disponibles": 0
            }
    
    def cerrar(self):
        """Cierra el servicio y libera recursos"""
        if self.executor:
            self.executor.shutdown(wait=False)
        print("🔇 Servicio de alertas de voz cerrado")


# Instancia global del servicio
servicio_alertas_voz = ServicioAlertasVoz()