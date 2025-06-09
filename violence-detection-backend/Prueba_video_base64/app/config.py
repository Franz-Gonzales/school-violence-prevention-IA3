# config.py
"""
Configuración centralizada de la aplicación
"""
import os
from typing import Optional

class Settings:
    """Configuración de la aplicación"""
    
    # Base de datos
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "video_recorder_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "gonzales"
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Video - CONFIGURACIÓN MEJORADA
    VIDEO_FPS: int = 30          # AUMENTAR A 30 FPS para mejor fluidez
    VIDEO_WIDTH: int = 640       # Resolución mejorada
    VIDEO_HEIGHT: int = 480      # Resolución mejorada
    MAX_DURATION: int = 10       # segundos
    
    # Directorios
    TEMP_VIDEO_DIR: str = "temp_videos"
    STATIC_DIR: str = "static"
    TEMPLATES_DIR: str = "templates"
    
    # Audio
    VOICE_THRESHOLD: int = 150
    SILENCE_DURATION: float = 2.0
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    def __init__(self):
        # Crear directorios si no existen
        os.makedirs(self.TEMP_VIDEO_DIR, exist_ok=True)
        os.makedirs(self.STATIC_DIR, exist_ok=True)
        os.makedirs(self.TEMPLATES_DIR, exist_ok=True)

# Instancia global de configuración
settings = Settings()