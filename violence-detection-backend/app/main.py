"""
Aplicación principal FastAPI
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.v1 import api_router
from app.api.websocket.notifications_ws import websocket_notificaciones
from app.api.websocket.rtc_signaling import websocket_endpoint
from app.core.database import inicializar_db, cerrar_db
from app.core.exceptions import ErrorSistemaBase
from app.ai.model_loader import cargador_modelos
from app.config import configuracion
from app.utils.logger import obtener_logger
from datetime import datetime

logger = obtener_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    try:
        # Startup
        logger.info("Iniciando Software de Detección de Violencia Escolar")
        print("Iniciando Software de Detección de Violencia Escolar")
        
        # Inicializar base de datos
        await inicializar_db()
        logger.info("Base de datos inicializada")
        print("Base de datos inicializada")
        
        # Crear directorios necesarios
        try:
            configuracion.VIDEO_EVIDENCE_PATH.mkdir(parents=True, exist_ok=True)
            (configuracion.VIDEO_EVIDENCE_PATH / "clips").mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directorios de evidencias creados en: {configuracion.VIDEO_EVIDENCE_PATH}")
            print(f"✅ Directorios de evidencias creados en: {configuracion.VIDEO_EVIDENCE_PATH}")
        except Exception as e:
            logger.error(f"❌ Error al crear directorios de evidencias: {e}")
            print(f"❌ Error al crear directorios de evidencias: {e}")
        
        # Cargar modelos de IA
        try:
            cargador_modelos.cargar_todos_los_modelos()
            logger.info("Modelos de IA cargados exitosamente")
            print("Modelos de IA cargados exitosamente")
        except Exception as e:
            logger.error(f"Error al cargar modelos: {e}")
            print(f"Error al cargar modelos: {e}")
            # Continuar sin modelos en desarrollo
        
            # Continuar sin modelos en desarrollo
    
        # Iniciar tareas en background
        # asyncio.create_task(procesar_notificaciones())
        
        yield
        
        # Shutdown
        print("Iniciando cierre ordenado de la aplicación...")
        
        # 1. Cerrar conexiones WebSocket primero
        from app.api.websocket.stream_handler import manejador_streaming
        for cliente_id in list(manejador_streaming.conexiones_peer.keys()):
            await manejador_streaming.cerrar_conexion(cliente_id)
        
        # 2. Cancelar tareas pendientes
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if tasks:
            print(f"Cerrando {len(tasks)} tareas pendientes...")
            for task in tasks:
                task.cancel()
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout esperando que las tareas terminen")
        
        # 3. Liberar recursos en orden
        cargador_modelos.liberar_memoria()
        
        # 4. Cerrar base de datos explícitamente
        try:
            await cerrar_db()
            await asyncio.sleep(1)  # Dar tiempo para que se cierren las conexiones
        except Exception as e:
            print(f"Error cerrando DB: {e}")
        
        print("✅ Aplicación cerrada correctamente")
        
    except asyncio.CancelledError:
        print("Cierre de aplicación cancelado")
    except Exception as e:
        print(f"❌ Error durante el cierre: {e}")
        raise


# Crear aplicación FastAPI
app = FastAPI(
    title=configuracion.APP_NAME,
    description=configuracion.APP_DESCRIPTION,
    version=configuracion.APP_VERSION,
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/uploads", StaticFiles(directory=str(configuracion.UPLOAD_PATH)), name="uploads")
app.mount("/evidencias", StaticFiles(directory=str(configuracion.VIDEO_EVIDENCE_PATH)), name="evidencias")

# Incluir routers
app.include_router(api_router)

# WebSocket endpoints
app.websocket("/ws/notifications/{usuario_id}")(websocket_notificaciones)
app.websocket("/ws/rtc/{cliente_id}/{camara_id}")(websocket_endpoint)

# Manejador de excepciones personalizado
@app.exception_handler(ErrorSistemaBase)
async def manejador_error_sistema(request: Request, exc: ErrorSistemaBase):
    """Maneja las excepciones personalizadas del software"""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.codigo,
            "mensaje": exc.mensaje,
            "detalles": exc.detalles
        }
    )

# Endpoint de salud
@app.get("/health")
async def verificar_salud():
    """Verifica el estado del software"""
    return {
        "estado": "saludable",
        "timestamp": datetime.now().isoformat(),
        "version": configuracion.VERSION,
        "gpu_disponible": configuracion.obtener_configuracion_gpu()["gpu_disponible"]
    }

# Endpoint raíz
@app.get("/")
async def raiz():
    """Endpoint raíz con información del software"""
    return {
        "nombre": configuracion.NOMBRE_PROYECTO,
        "version": configuracion.VERSION,
        "descripcion": configuracion.DESCRIPCION,
        "documentacion": "/docs",
        "estado": "activo"
    }

# Función para procesar notificaciones en background
async def procesar_notificaciones():
    """Tarea en background para procesar notificaciones"""
    from app.api.websocket.notifications_ws import manejador_notificaciones_ws
    try:
        await manejador_notificaciones_ws.procesar_cola()
    except Exception as e:
        logger.error(f"Error en procesamiento de notificaciones: {e}")
        print(f"Error en procesamiento de notificaciones: {e}")


if __name__ == "__main__":
    import uvicorn
    
    # Configuración para desarrollo
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=configuracion.LOG_LEVEL.lower()
    )