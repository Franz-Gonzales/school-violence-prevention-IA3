"""
Router principal de la API v1
"""
from fastapi import APIRouter
from app.api.v1 import (
    auth,
    cameras, 
    incidents,
    reports,
    notifications,
    settings,
    users,
    files
)

api_router = APIRouter(prefix="/api/v1")

# Incluir todos los routers
api_router.include_router(auth.router)
api_router.include_router(cameras.router)
api_router.include_router(incidents.router)
api_router.include_router(reports.router)
api_router.include_router(notifications.router)
api_router.include_router(settings.router)
api_router.include_router(users.router)
api_router.include_router(files.router)