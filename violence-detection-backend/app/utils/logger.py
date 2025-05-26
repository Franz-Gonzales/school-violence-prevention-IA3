"""
Sistema de logging estructurado
"""
import sys
import logging
from pathlib import Path
from datetime import datetime
import structlog
from app.config import configuracion

# Crear directorio de logs
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configurar procesadores
procesadores = [
    structlog.stdlib.filter_by_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]

# Configurar colores y emojis en consola
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

# Configurar logging básico
logging.basicConfig(
    level=getattr(logging, configuracion.LOG_LEVEL, "INFO"),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            log_dir / "app.log",
            mode="a",
            encoding="utf-8"
        )
    ]
)

def obtener_logger(nombre: str):
    """Obtiene un logger configurado"""
    return structlog.get_logger(nombre)