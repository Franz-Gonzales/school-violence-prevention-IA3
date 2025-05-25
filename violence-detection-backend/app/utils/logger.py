"""
Sistema de logging estructurado
"""
import sys
import logging
from pathlib import Path
from datetime import datetime
import structlog
from app.config import configuracion

# Crear directorios de logs con fecha
def crear_directorio_logs():
    fecha = datetime.now().strftime("%Y-%m-%d")
    log_dir = Path("logs") / fecha
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

log_dir = crear_directorio_logs()

# Configuración del formato
formato_consola = "%(asctime)s [%(levelname)s] %(message)s"
formato_archivo = "%(asctime)s [%(levelname)s] %(message)s (%(name)s:%(lineno)d)"

# Configurar logging básico
logging.basicConfig(
    level=getattr(logging, configuracion.LOG_LEVEL, "INFO"),
    handlers=[
        # Handler para consola con colores
        logging.StreamHandler(sys.stdout),
        # Handler para archivo diario
        logging.FileHandler(
            log_dir / f"app_{datetime.now().strftime('%H-%M-%S')}.log",
            mode="a",
            encoding="utf-8"
        )
    ]
)

# Procesadores personalizados
def add_app_info(logger, name, event_dict):
    """Agrega información de la aplicación al log"""
    event_dict["app"] = {
        "name": configuracion.APP_NAME,
        "version": configuracion.APP_VERSION,
        "environment": "development" if configuracion.DEBUG else "production"
    }
    return event_dict

def add_emoji(logger, name, event_dict):
    """Agrega emojis según el nivel de log"""
    level = event_dict.get("level", "info")
    emojis = {
        "debug": "🐛",
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "critical": "🚨"
    }
    event_dict["emoji"] = emojis.get(level, "")
    return event_dict

# Configurar procesadores
procesadores = [
    structlog.stdlib.filter_by_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f"),
    add_emoji,
    add_app_info,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]

# Configurar renderer según el entorno
if sys.stderr.isatty():
    procesadores.append(
        structlog.dev.ConsoleRenderer(
            colors=True,
            level_styles={
                "debug": "blue",
                "info": "green",
                "warning": "yellow",
                "error": "red",
                "critical": "red,bold",
            }
        )
    )
else:
    procesadores.append(structlog.processors.JSONRenderer())

# Configurar structlog
structlog.configure(
    processors=procesadores,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def obtener_logger(nombre: str):
    """Obtiene un logger configurado"""
    return structlog.get_logger(
        nombre,
        modulo=nombre.split(".")[-1]
    )