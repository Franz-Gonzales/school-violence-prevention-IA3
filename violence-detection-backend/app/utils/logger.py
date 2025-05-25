"""
Sistema de logging estructurado
"""
import sys
import structlog
from pathlib import Path
from app.config import configuracion

# Configurar procesadores
procesadores = [
    structlog.stdlib.filter_by_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]

# Renderizador según el entorno
if sys.stderr.isatty():
    procesadores.append(structlog.dev.ConsoleRenderer())
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
    return structlog.get_logger(nombre)


# Logger principal del sistema
logger = obtener_logger("sistema_violencia")