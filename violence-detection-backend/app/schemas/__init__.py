"""
Schemas Pydantic para validación de datos
"""
from app.schemas.user import UsuarioBase, UsuarioCrear, Usuario, UsuarioLogin
from app.schemas.camera import CamaraBase, CamaraCrear, Camara, CamaraActualizar
from app.schemas.incident import IncidenteBase, IncidenteCrear, Incidente, IncidenteActualizar
from app.schemas.notification import NotificacionBase, NotificacionCrear, Notificacion

__all__ = [
    "UsuarioBase", "UsuarioCrear", "Usuario", "UsuarioLogin",
    "CamaraBase", "CamaraCrear", "Camara", "CamaraActualizar",
    "IncidenteBase", "IncidenteCrear", "Incidente", "IncidenteActualizar",
    "NotificacionBase", "NotificacionCrear", "Notificacion"
]