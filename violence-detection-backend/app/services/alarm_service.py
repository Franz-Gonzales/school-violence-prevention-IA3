"""
Servicio para control de alarma Tuya - MEJORADO
"""
import tinytuya
import asyncio
import threading
import time
from typing import Optional
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class ServicioAlarma:
    """Servicio para controlar la alarma Tuya WiFi"""
    
    def __init__(self):
        self.device = None
        self.alarm_timer = None
        self.alarm_active = False
        self.configurar_dispositivo()
        
    def configurar_dispositivo(self):
        """Configura la conexión con el dispositivo Tuya"""
        try:
            self.device = tinytuya.Device(
                configuracion.TUYA_DEVICE_ID,
                configuracion.TUYA_IP_ADDRESS,
                configuracion.TUYA_LOCAL_KEY,
                version=configuracion.TUYA_DEVICE_VERSION
            )
            logger.info("Dispositivo Tuya configurado correctamente")
            print("Dispositivo Tuya configurado correctamente")
        except Exception as e:
            logger.error(f"Error al configurar dispositivo Tuya: {e}")
            print(f"Error al configurar dispositivo Tuya: {e}")
    
    async def activar_alarma(self, duracion: int = 5) -> bool:
        """
        Activa la alarma por un tiempo determinado - MEJORADO
        
        Args:
            duracion: Duración en segundos
            
        Returns:
            True si se activó correctamente
        """
        if not self.device:
            print("Dispositivo Tuya no configurado")
            return False
        
        if self.alarm_active:
            print("Alarma ya está activa")
            return True
        
        try:
            # Activar alarma
            print(f"🚨 Activando alarma por {duracion} segundos")
            
            self.device.set_value(104, True)
            self.alarm_active = True
            
            # Usar threading.Timer en lugar de asyncio.sleep para evitar interrupciones
            self.alarm_timer = threading.Timer(duracion, self._deactivate_alarm)
            self.alarm_timer.start()
            
            return True
            
        except Exception as e:
            print(f"Error al activar alarma: {e}")
            self.alarm_active = False
            return False
    
    def _deactivate_alarm(self):
        """Desactiva la alarma - método interno"""
        try:
            if self.device and self.alarm_active:
                self.device.set_value(104, False)
                self.alarm_active = False
                print("🔕 Alarma desactivada")
        except Exception as e:
            print(f"Error al desactivar alarma: {e}")
        finally:
            self.alarm_active = False
    
    def detener_alarma_manual(self):
        """Detiene la alarma manualmente"""
        if self.alarm_timer:
            self.alarm_timer.cancel()
        self._deactivate_alarm()
    
    async def probar_conexion(self) -> bool:
        """Prueba la conexión con el dispositivo"""
        if not self.device:
            return False
        
        try:
            status = self.device.status()
            print(f"Estado del dispositivo: {status}")
            return True
        except Exception as e:
            print(f"Error al conectar con dispositivo: {e}")
            return False
    
    def obtener_estado(self) -> Optional[dict]:
        """Obtiene el estado actual del dispositivo"""
        if not self.device:
            return None
        
        try:
            return {
                "device_status": self.device.status(),
                "alarm_active": self.alarm_active
            }
        except Exception as e:
            print(f"Error al obtener estado: {e}")
            return None