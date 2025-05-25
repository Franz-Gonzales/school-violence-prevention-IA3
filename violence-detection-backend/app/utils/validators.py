"""
Validadores personalizados
"""
import re
from typing import Optional
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


class Validadores:
    """Clase con validadores del software"""
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """Valida formato de email"""
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(patron, email))
    
    @staticmethod
    def validar_telefono(telefono: str) -> bool:
        """Valida formato de teléfono"""
        # Acepta formatos como: +591 12345678, 12345678, etc.
        patron = r'^(\+\d{1,3}\s?)?\d{7,15}$'
        telefono_limpio = telefono.replace(" ", "").replace("-", "")
        return bool(re.match(patron, telefono_limpio))
    
    @staticmethod
    def validar_resolucion(ancho: int, alto: int) -> bool:
        """Valida resolución de video"""
        resoluciones_validas = [
            (640, 480),   # VGA
            (1280, 720),  # HD
            (1920, 1080), # Full HD
            (2560, 1440), # 2K
        ]
        
        return (ancho, alto) in resoluciones_validas
    
    @staticmethod
    def validar_fps(fps: int) -> bool:
        """Valida FPS"""
        return 1 <= fps <= 60
    
    @staticmethod
    def validar_umbral(umbral: float) -> bool:
        """Valida umbral de detección"""
        return 0.0 <= umbral <= 1.0