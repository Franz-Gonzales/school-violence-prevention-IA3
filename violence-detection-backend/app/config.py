from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from functools import lru_cache

class Configuracion(BaseSettings):
    APP_NAME: str = "Software de Detección de Violencia Escolar"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Software de IA para prevención de violencia"
    DEBUG: bool = False
    
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Configuración de cámara optimizada
    CAMERA_INDEX: int = 1
    CAMERA_WIDTH: int = 640
    CAMERA_HEIGHT: int = 480
    CAMERA_FPS: int = 15  # FPS estable
    DISPLAY_WIDTH: int = 640
    DISPLAY_HEIGHT: int = 480
    BUFFER_FRAMES: int = 8
    CLIP_DURATION: int = 6  # Aumentado a 6 segundos para mejor evidencia
    
    STUN_SERVER: str = "stun:stun.l.google.com:19302"
    TURN_SERVER: Optional[str] = None
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    MODELOS_PATH: Path = BASE_DIR / "models_weights"
    UPLOAD_PATH: Path = BASE_DIR / "uploads"
    VIDEO_EVIDENCE_PATH: Path = BASE_DIR / "evidencias"
    
    YOLO_MODEL: str = "yolo/exported_v3/best.pt"
    TIMESFORMER_MODEL: str = "timesformer/exported_models2/timesformer_violence_detector_half.onnx"
    
    # Configuración TimesFormer optimizada
    TIMESFORMER_CONFIG: Dict[str, Any] = {
        "input_size": 224,
        "num_frames": 8,
        "patch_size": 16,
        "num_channels": 3,
        "hidden_size": 768,
        "mean": [0.45, 0.45, 0.45],
        "std": [0.225, 0.225, 0.225],
        "labels": ["no_violencia", "violencia"]
    }
    
    # Resoluciones optimizadas
    DEFAULT_RESOLUTION: tuple = (640, 480)
    PROCESSING_RESOLUTION: tuple = (640, 640)
    DEFAULT_FPS: int = 15
    
    # Umbrales de confianza
    YOLO_CONF_THRESHOLD: float = 0.65  # Reducido ligeramente para mejor detección
    VIOLENCE_THRESHOLD: float = 0.72
    
    # Resolución YOLO optimizada para velocidad
    YOLO_RESOLUTION_WIDTH: int = 416  # Mantener 416 para balance velocidad/precisión
    YOLO_RESOLUTION_HEIGHT: int = 416
    
    # Configuración de alarma Tuya
    TUYA_DEVICE_ID: Optional[str] = None
    TUYA_LOCAL_KEY: Optional[str] = None
    TUYA_IP_ADDRESS: Optional[str] = None
    TUYA_DEVICE_VERSION: str = "3.5"
    ALARMA_DURACION: int = 3
    
    # Notificaciones web
    VAPID_PUBLIC_KEY: Optional[str] = None
    VAPID_PRIVATE_KEY: Optional[str] = None
    VAPID_CLAIMS_EMAIL: Optional[str] = None
    
    # Optimización de procesamiento
    PROCESS_EVERY_N_FRAMES: int = 4  # Aumentado para reducir carga de procesamiento
    MAX_CONCURRENT_PROCESSES: int = 2  # Limitar procesos concurrentes
    
    # Configuración GPU
    USE_GPU: bool = False
    GPU_DEVICE: int = 0
    MAX_BATCH_SIZE: int = 4  # Reducido para evitar OOM
    
    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs_violencia_detection.log"
    
    # Configuración de rendimiento de video
    VIDEO_BUFFER_SIZE: int = 30  # Frames en buffer
    MAX_EVIDENCE_DURATION: int = 15  # Máximo 15 segundos de evidencia
    VIDEO_COMPRESSION_QUALITY: int = 85  # Calidad de compresión (0-100)
    
    # Control de memoria
    MAX_MEMORY_USAGE_MB: int = 1024  # Límite de memoria en MB
    CLEANUP_INTERVAL_SECONDS: int = 60  # Intervalo de limpieza
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def obtener_ruta_modelo(self, nombre_modelo: str) -> Path:
        return self.MODELOS_PATH / nombre_modelo
    
    def crear_directorios(self):
        directorios = [
            self.MODELOS_PATH,
            self.UPLOAD_PATH,
            self.VIDEO_EVIDENCE_PATH,
            self.VIDEO_EVIDENCE_PATH / "clips",
            self.VIDEO_EVIDENCE_PATH / "frames",
            self.VIDEO_EVIDENCE_PATH / "temp"  # Directorio temporal
        ]
        for directorio in directorios:
            directorio.mkdir(parents=True, exist_ok=True)
    
    def obtener_configuracion_gpu(self) -> Dict[str, Any]:
        import torch
        if self.USE_GPU and torch.cuda.is_available():
            return {
                "device": f"cuda:{self.GPU_DEVICE}",
                "gpu_disponible": True,
                "gpu_nombre": torch.cuda.get_device_name(self.GPU_DEVICE),
                "memoria_gpu": torch.cuda.get_device_properties(self.GPU_DEVICE).total_memory
            }
        return {
            "device": "cpu",
            "gpu_disponible": False,
            "gpu_nombre": None,
            "memoria_gpu": 0
        }
    
    def obtener_configuracion_streaming(self) -> Dict[str, Any]:
        """Obtiene configuración optimizada para streaming"""
        return {
            "target_fps": self.CAMERA_FPS,
            "resolution": (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT),
            "buffer_size": self.VIDEO_BUFFER_SIZE,
            "processing_interval": self.PROCESS_EVERY_N_FRAMES,
            "max_evidence_frames": self.DEFAULT_FPS * self.MAX_EVIDENCE_DURATION
        }

@lru_cache()
def obtener_configuracion() -> Configuracion:
    config = Configuracion()
    config.crear_directorios()
    return config

configuracion = obtener_configuracion()