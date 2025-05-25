"""
Excepciones personalizadas del sistema
"""
from typing import Any, Dict, Optional


class ErrorSistemaBase(Exception):
    """Excepción base del sistema"""
    def __init__(
        self, 
        mensaje: str, 
        codigo: str = "ERROR_GENERAL",
        detalles: Optional[Dict[str, Any]] = None
    ):
        self.mensaje = mensaje
        self.codigo = codigo
        self.detalles = detalles or {}
        super().__init__(self.mensaje)


class ErrorAutenticacion(ErrorSistemaBase):
    """Error de autenticación"""
    def __init__(self, mensaje: str = "Error de autenticación"):
        super().__init__(mensaje, "ERROR_AUTENTICACION")


class ErrorPermisos(ErrorSistemaBase):
    """Error de permisos insuficientes"""
    def __init__(self, mensaje: str = "Permisos insuficientes"):
        super().__init__(mensaje, "ERROR_PERMISOS")


class ErrorCamara(ErrorSistemaBase):
    """Error relacionado con cámaras"""
    def __init__(self, mensaje: str, camara_id: Optional[int] = None):
        detalles = {"camara_id": camara_id} if camara_id else {}
        super().__init__(mensaje, "ERROR_CAMARA", detalles)


class ErrorModeloIA(ErrorSistemaBase):
    """Error en los modelos de IA"""
    def __init__(self, mensaje: str, modelo: Optional[str] = None):
        detalles = {"modelo": modelo} if modelo else {}
        super().__init__(mensaje, "ERROR_MODELO_IA", detalles)


class ErrorProcesamiento(ErrorSistemaBase):
    """Error en el procesamiento de video"""
    def __init__(self, mensaje: str, frame: Optional[int] = None):
        detalles = {"frame": frame} if frame is not None else {}
        super().__init__(mensaje, "ERROR_PROCESAMIENTO", detalles)


class ErrorAlarma(ErrorSistemaBase):
    """Error con el sistema de alarma"""
    def __init__(self, mensaje: str = "Error al activar alarma"):
        super().__init__(mensaje, "ERROR_ALARMA")


class ErrorNotificacion(ErrorSistemaBase):
    """Error al enviar notificación"""
    def __init__(self, mensaje: str, tipo: Optional[str] = None):
        detalles = {"tipo": tipo} if tipo else {}
        super().__init__(mensaje, "ERROR_NOTIFICACION", detalles)