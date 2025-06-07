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
    CAMERA_FPS: int = 15  # FPS estable para captura
    DISPLAY_WIDTH: int = 640
    DISPLAY_HEIGHT: int = 480
    BUFFER_FRAMES: int = 8
    CLIP_DURATION: int = 8  # Duración total del clip (pre + post incidente)
    
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
    YOLO_CONF_THRESHOLD: float = 0.65
    VIOLENCE_THRESHOLD: float = 0.70
    
    # Resolución YOLO optimizada para velocidad
    YOLO_RESOLUTION_WIDTH: int = 416
    YOLO_RESOLUTION_HEIGHT: int = 416
    
    # ========== CONFIGURACIÓN DE VIDEO EVIDENCIA ==========
    
    # FPS para videos de evidencia (CRÍTICO para reproducción correcta)
    EVIDENCE_TARGET_FPS: int = 20  # FPS fijo para todos los videos de evidencia
    EVIDENCE_QUALITY: str = "alta"  # alta, media, baja
    
    # Duración de clips de evidencia
    EVIDENCE_PRE_INCIDENT_SECONDS: float = 4.0   # Segundos antes del incidente
    EVIDENCE_POST_INCIDENT_SECONDS: float = 6.0  # Segundos después del incidente
    EVIDENCE_MAX_DURATION_SECONDS: int = 25      # Duración máxima total
    
    # CODEC SIMPLIFICADO (más compatible)
    VIDEO_CODEC: str = "mp4v"  # Usar mp4v como principal (más compatible)
    VIDEO_CODEC_FALLBACK: str = "XVID"  # Fallback si mp4v no está disponible
    VIDEO_CONTAINER: str = "mp4"
    VIDEO_BITRATE: str = "3000k"
    
    VIDEO_CRF: int = 23  # Constant Rate Factor (0-51, menor = mejor calidad)
    
    # Buffer inteligente para evidencia (AMPLIADO)
    EVIDENCE_BUFFER_SIZE_SECONDS: int = 30  # Buffer más grande (45 segundos)
    EVIDENCE_FRAME_INTERPOLATION: bool = False  # Desactivar para usar frames reales
    EVIDENCE_TIMESTAMP_OVERLAY: bool = True
    EVIDENCE_CAPTURE_FPS: int = 30  # FPS de captura más alto
    EVIDENCE_SMOOTH_TRANSITIONS: bool = True
    EVIDENCE_TEMPORAL_SMOOTHING: bool = True
    
    # CONFIGURACIÓN DE COMPRESIÓN OPTIMIZADA
    VIDEO_QUALITY_SETTINGS: Dict[str, Dict[str, Any]] = {
        "alta": {
            "bitrate": "3000k",  # Bitrate más alto
            "crf": 16,           # Calidad muy alta
            "scale": 1.0,
            "fps": 15,
            "codec": "H264"
        },
        "media": {
            "bitrate": "2000k", 
            "crf": 20,           # Calidad alta
            "scale": 1.0,
            "fps": 15,
            "codec": "H264"
        },
        "baja": {
            "bitrate": "1200k",
            "crf": 24,
            "scale": 1.0,        # Mantener escala completa
            "fps": 15,
            "codec": "H264"
        }
    }
    
    # BUFFER Y PROCESAMIENTO MEJORADO
    EVIDENCE_FRAME_SMOOTHING: bool = True    # Suavizado de frames
    EVIDENCE_ADAPTIVE_FPS: bool = False      # Desactivar FPS adaptativo para consistencia

    # CONFIGURACIÓN DE OPENCV WRITER MEJORADA
    OPENCV_WRITER_CONFIG: Dict[str, Any] = {
        "fourcc": "mp4v",  # Usar mp4v como principal
        "fps": EVIDENCE_TARGET_FPS,  # FPS fijo para todos los videos de evidencia
        "bitrate": VIDEO_BITRATE,     # Bitrate optimizado
        "quality": 95,                # Calidad del video (0-100)
        "compression_level": 3,       # Nivel de compresión (0-9)
        "use_gpu_acceleration": False  # Desactivar aceleración GPU para compatibilidad
    }
    
    # CONFIGURACIÓN DE PROCESAMIENTO DE FRAMES
    FRAME_PROCESSING_CONFIG: Dict[str, Any] = {
        "resize_method": "INTER_LINEAR",     # Método de redimensionado
        "smooth_frames": True,               # Suavizado entre frames
        "temporal_consistency": True,        # Consistencia temporal
        "violence_overlay_duration": 5.0,   # Duración del overlay de violencia
    }
    
    # CONFIGURACIÓN DE THREADING PARA VIDEO
    VIDEO_PROCESSING_THREADS: int = 2       # Hilos dedicados para video
    VIDEO_QUEUE_SIZE: int = 100             # Cola más grande para frames
    VIDEO_WRITE_BUFFER_SIZE: int = 50       # Buffer de escritura
    
    # CONFIGURACIÓN DE DEBUGGING
    VIDEO_DEBUG_ENABLED: bool = True        # Debug de videos
    VIDEO_SAVE_INTERMEDIATE: bool = False   # Guardar frames intermedios
    VIDEO_TIMING_LOGS: bool = True          # Logs de timing detallados
    
    
    
    # ========== CONFIGURACIÓN DE PROCESAMIENTO ==========
    
    # Configuración de alarma Tuya
    TUYA_DEVICE_ID: Optional[str] = None
    TUYA_LOCAL_KEY: Optional[str] = None
    TUYA_IP_ADDRESS: Optional[str] = None
    TUYA_DEVICE_VERSION: str = "3.5"
    ALARMA_DURACION: int = 5  # Duración de la alarma en segundos
    
    # Notificaciones web
    VAPID_PUBLIC_KEY: Optional[str] = None
    VAPID_PRIVATE_KEY: Optional[str] = None
    VAPID_CLAIMS_EMAIL: Optional[str] = None
    
    # Optimización de procesamiento
    PROCESS_EVERY_N_FRAMES: int = 4  # Procesar cada N frames para eficiencia
    MAX_CONCURRENT_PROCESSES: int = 2
    
    # Configuración GPU
    USE_GPU: bool = False
    GPU_DEVICE: int = 0
    MAX_BATCH_SIZE: int = 4
    
    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs_violencia_detection.log"
    
    # ========== CONFIGURACIÓN DE RENDIMIENTO ==========
    
    # Configuración de rendimiento de video mejorada
    VIDEO_BUFFER_SIZE: int = 40  # Frames en buffer circular
    FRAME_QUEUE_SIZE: int = 50   # Tamaño de cola de frames
    PROCESSING_THREAD_COUNT: int = 2  # Hilos para procesamiento
    
    # Control de memoria
    MAX_MEMORY_USAGE_MB: int = 1024
    CLEANUP_INTERVAL_SECONDS: int = 60
    FRAME_CACHE_SIZE: int = 100  # Frames en caché para procesamiento
    
    # Configuración de threading y async
    ASYNC_WORKERS: int = 4  # Workers para tareas asíncronas
    THREAD_POOL_SIZE: int = 8  # Tamaño del pool de threads
    
    # ========== CONFIGURACIÓN DE ALMACENAMIENTO ==========
    
    # Gestión de archivos de evidencia
    EVIDENCE_CLEANUP_DAYS: int = 30  # Días antes de limpiar evidencias antiguas
    EVIDENCE_MAX_SIZE_GB: float = 5.0  # Tamaño máximo de directorio de evidencias
    EVIDENCE_BACKUP_ENABLED: bool = True  # Backup automático de evidencias críticas
    EVIDENCE_COMPRESSION_ENABLED: bool = True  # Comprimir evidencias antiguas
    
    # Configuración de thumbnails
    THUMBNAIL_ENABLED: bool = True
    THUMBNAIL_WIDTH: int = 320
    THUMBNAIL_HEIGHT: int = 180
    THUMBNAIL_QUALITY: int = 85
    
    # ========== CONFIGURACIÓN DE CALIDAD DE STREAM ==========
    
    # Configuración adaptativa de calidad
    ADAPTIVE_QUALITY_ENABLED: bool = True
    QUALITY_ADAPTATION_INTERVAL: int = 10  # Segundos entre ajustes
    
    # Thresholds para cambio automático de calidad
    QUALITY_THRESHOLDS: Dict[str, Dict[str, float]] = {
        "cpu_usage": {"high": 80.0, "medium": 60.0, "low": 40.0},
        "memory_usage": {"high": 80.0, "medium": 60.0, "low": 40.0},
        "frame_drop_rate": {"high": 5.0, "medium": 2.0, "low": 1.0},
        "bandwidth": {"high": 2000, "medium": 1000, "low": 500}  # kbps
    }
    
    # Buffer específico para secuencias de violencia (frames dedicados)
    EVIDENCE_VIOLENCE_BUFFER_SIZE: int = 800  # Frames dedicados para violencia (opcional)

    # Control de captura durante violencia
    EVIDENCE_VIOLENCE_CAPTURE_ALL: bool = True  # Capturar TODOS los frames durante violencia

    
    # Configuraciones de calidad de stream
    STREAM_QUALITY_PROFILES: Dict[str, Dict[str, Any]] = {
        "Alta": {
            "width": 640,
            "height": 480,
            "fps": 15,
            "bitrate": "1500k",
            "processing_interval": 2
        },
        "Media": {
            "width": 480,
            "height": 360,
            "fps": 12,
            "bitrate": "800k", 
            "processing_interval": 3
        },
        "Baja": {
            "width": 320,
            "height": 240,
            "fps": 8,
            "bitrate": "400k",
            "processing_interval": 4
        }
    }

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def obtener_ruta_modelo(self, nombre_modelo: str) -> Path:
        return self.MODELOS_PATH / nombre_modelo
    
    def crear_directorios(self):
        """Crea todos los directorios necesarios para el sistema"""
        directorios = [
            self.MODELOS_PATH,
            self.UPLOAD_PATH,
            self.VIDEO_EVIDENCE_PATH,
            self.VIDEO_EVIDENCE_PATH / "clips",
            self.VIDEO_EVIDENCE_PATH / "thumbnails",
            self.VIDEO_EVIDENCE_PATH / "temp",
            self.VIDEO_EVIDENCE_PATH / "compressed",
            self.VIDEO_EVIDENCE_PATH / "backup"
        ]
        for directorio in directorios:
            directorio.mkdir(parents=True, exist_ok=True)
    
    def obtener_configuracion_gpu(self) -> Dict[str, Any]:
        """Obtiene información sobre la configuración de GPU"""
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
    
    def obtener_configuracion_evidencia(self) -> Dict[str, Any]:
        """Obtiene configuración optimizada para evidencia de video"""
        quality_config = self.VIDEO_QUALITY_SETTINGS[self.EVIDENCE_QUALITY]
        
        return {
            "fps_target": self.EVIDENCE_TARGET_FPS,
            "pre_incident_duration": self.EVIDENCE_PRE_INCIDENT_SECONDS,
            "post_incident_duration": self.EVIDENCE_POST_INCIDENT_SECONDS,
            "max_duration": self.EVIDENCE_MAX_DURATION_SECONDS,
            "quality": quality_config,
            "codec": self.VIDEO_CODEC,
            "container": self.VIDEO_CONTAINER,
            "interpolation_enabled": self.EVIDENCE_FRAME_INTERPOLATION,
            "timestamp_overlay": self.EVIDENCE_TIMESTAMP_OVERLAY,
            "buffer_size_seconds": self.EVIDENCE_BUFFER_SIZE_SECONDS
        }
    
    def obtener_configuracion_streaming(self, calidad: str = "Alta") -> Dict[str, Any]:
        """Obtiene configuración optimizada para streaming según calidad"""
        profile = self.STREAM_QUALITY_PROFILES.get(calidad, self.STREAM_QUALITY_PROFILES["Alta"])
        
        return {
            "resolution": (profile["width"], profile["height"]),
            "fps": profile["fps"],
            "bitrate": profile["bitrate"],
            "processing_interval": profile["processing_interval"],
            "buffer_size": self.VIDEO_BUFFER_SIZE,
            "adaptive_quality": self.ADAPTIVE_QUALITY_ENABLED
        }
    
    def calcular_parametros_evidencia(self, duracion_violencia: float) -> Dict[str, Any]:
        """Calcula parámetros óptimos para un clip de evidencia"""
        # Calcular duración total del clip
        duracion_total = (
            self.EVIDENCE_PRE_INCIDENT_SECONDS + 
            duracion_violencia + 
            self.EVIDENCE_POST_INCIDENT_SECONDS
        )
        
        # Limitar a duración máxima
        if duracion_total > self.EVIDENCE_MAX_DURATION_SECONDS:
            duracion_total = self.EVIDENCE_MAX_DURATION_SECONDS
            # Ajustar tiempos proporcionalmente
            factor = self.EVIDENCE_MAX_DURATION_SECONDS / duracion_total
            pre_time = self.EVIDENCE_PRE_INCIDENT_SECONDS * factor
            post_time = self.EVIDENCE_POST_INCIDENT_SECONDS * factor
        else:
            pre_time = self.EVIDENCE_PRE_INCIDENT_SECONDS
            post_time = self.EVIDENCE_POST_INCIDENT_SECONDS
        
        # Calcular número de frames necesarios
        total_frames = int(duracion_total * self.EVIDENCE_TARGET_FPS)
        
        return {
            "duracion_total": duracion_total,
            "pre_incident_time": pre_time,
            "post_incident_time": post_time,
            "total_frames": total_frames,
            "fps": self.EVIDENCE_TARGET_FPS,
            "frames_per_second": self.EVIDENCE_TARGET_FPS
        }
    
    def optimizar_configuracion_recursos(self) -> Dict[str, Any]:
        """Optimiza la configuración basada en recursos del sistema"""
        import psutil
        
        # Obtener información del sistema
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Ajustar configuración basada en recursos
        if memory_gb < 4:
            # Sistema con poca memoria
            config = {
                "processing_threads": min(2, cpu_count),
                "frame_buffer_size": 15,
                "quality_profile": "Baja",
                "processing_interval": 6
            }
        elif memory_gb < 8:
            # Sistema con memoria media
            config = {
                "processing_threads": min(4, cpu_count),
                "frame_buffer_size": 25,
                "quality_profile": "Media", 
                "processing_interval": 4
            }
        else:
            # Sistema con buena memoria
            config = {
                "processing_threads": min(6, cpu_count),
                "frame_buffer_size": 30,
                "quality_profile": "Alta",
                "processing_interval": 2
            }
        
        config.update({
            "system_memory_gb": memory_gb,
            "cpu_cores": cpu_count,
            "recommended_max_cameras": max(1, int(memory_gb / 2))
        })
        
        return config

@lru_cache()
def obtener_configuracion() -> Configuracion:
    config = Configuracion()
    config.crear_directorios()
    return config

# Instancia global de configuración
configuracion = obtener_configuracion()