"""
Servicio para control de alarma Tuya
"""
import tinytuya
import asyncio
from typing import Optional
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class ServicioAlarma:
    """Servicio para controlar la alarma Tuya WiFi"""
    
    def __init__(self):
        self.device = None
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
        except Exception as e:
            logger.error(f"Error al configurar dispositivo Tuya: {e}")
    
    async def activar_alarma(self, duracion: int = 10) -> bool:
        """
        Activa la alarma por un tiempo determinado
        
        Args:
            duracion: Duración en segundos
            
        Returns:
            True si se activó correctamente
        """
        if not self.device:
            logger.error("Dispositivo Tuya no configurado")
            return False
        
        try:
            # Activar alarma (DPS 104 puede variar según el modelo)
            logger.info(f"Activando alarma por {duracion} segundos")
            self.device.set_value(104, True)
            
            # Esperar duración especificada
            await asyncio.sleep(duracion)
            
            # Desactivar alarma
            self.device.set_value(104, False)
            logger.info("Alarma desactivada")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al activar alarma: {e}")
            return False
    
    async def probar_conexion(self) -> bool:
        """Prueba la conexión con el dispositivo"""
        if not self.device:
            return False
        
        try:
            status = self.device.status()
            logger.info(f"Estado del dispositivo: {status}")
            return True
        except Exception as e:
            logger.error(f"Error al conectar con dispositivo: {e}")
            return False
    
    def obtener_estado(self) -> Optional[dict]:
        """Obtiene el estado actual del dispositivo"""
        if not self.device:
            return None
        
        try:
            return self.device.status()
        except Exception as e:
            logger.error(f"Error al obtener estado: {e}")
            return None