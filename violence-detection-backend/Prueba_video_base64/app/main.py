# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from typing import List
import os
import traceback

from . import models, schemas
from .database import engine, get_db
from .video_recorder import SimpleVideoRecorder, video_to_base64, get_video_info
from .config import settings

# Crear tablas
try:
    models.Base.metadata.create_all(bind=engine)
    print("✅ Tablas de base de datos creadas/verificadas correctamente")
except Exception as e:
    print(f"❌ Error creando tablas: {e}")

app = FastAPI(title="Video Recorder API")

# Configurar archivos estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Crear instancia del grabador con configuración
recorder = SimpleVideoRecorder(
    output_dir=settings.TEMP_VIDEO_DIR,
    fps=settings.VIDEO_FPS,
    max_duration=settings.MAX_DURATION
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/record-video")
async def record_video(db: Session = Depends(get_db)):
    """Graba un video y lo guarda en la base de datos"""
    video_path = None
    try:
        # Verificar conexión a la base de datos
        try:
            db.execute(text("SELECT 1"))
            print("✅ Conexión a la base de datos OK")
        except Exception as db_error:
            print(f"❌ Error de conexión a la base de datos: {db_error}")
            raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(db_error)}")
        
        # Grabar video
        print("🎬 Iniciando grabación de video...")
        video_path = recorder.record_video_session()
        
        if not video_path:
            raise HTTPException(status_code=400, detail="No se grabó ningún video o se canceló la grabación")
        
        if not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail=f"El archivo de video no existe: {video_path}")
        
        print(f"✅ Video grabado exitosamente: {video_path}")
        
        # Obtener información del video
        print("📊 Obteniendo información del video...")
        video_info = get_video_info(video_path)
        print(f"📊 Info del video: {video_info}")
        
        # Convertir a Base64
        print("🔄 Convirtiendo video a Base64...")
        base64_data = video_to_base64(video_path)
        
        if not base64_data:
            raise HTTPException(status_code=500, detail="Error convirtiendo video a Base64")
        
        print(f"✅ Video convertido a Base64 ({len(base64_data)} caracteres)")
        
        # Verificar tamaño del Base64
        base64_size_mb = len(base64_data) / 1024 / 1024
        print(f"📏 Tamaño Base64: {base64_size_mb:.2f} MB")
        
        if base64_size_mb > 10:  # Límite de 10MB para Base64
            raise HTTPException(status_code=400, detail=f"Video muy grande ({base64_size_mb:.2f} MB). Intenta con un video más corto.")
        
        # Preparar datos para la base de datos
        filename = os.path.basename(video_path)
        db_video = models.Video(
            filename=filename,
            video_base64=base64_data,
            duration=float(video_info.get('duration', 0.0)),
            file_size=int(video_info.get('file_size', 0))
        )
        
        # Guardar en base de datos con verificación
        print("💾 Guardando en base de datos...")
        try:
            db.add(db_video)
            db.commit()
            db.refresh(db_video)
            print(f"✅ Video guardado en BD con ID: {db_video.id}")
            
            # Verificar que se guardó el Base64
            saved_video = db.query(models.Video).filter(models.Video.id == db_video.id).first()
            if saved_video and saved_video.video_base64:
                print(f"✅ Base64 verificado en BD: {len(saved_video.video_base64)} caracteres")
            else:
                print("❌ Error: Base64 no se guardó correctamente")
                raise SQLAlchemyError("Base64 no se guardó en la base de datos")
                
        except SQLAlchemyError as db_error:
            db.rollback()
            print(f"❌ Error guardando en BD: {db_error}")
            raise HTTPException(status_code=500, detail=f"Error guardando en base de datos: {str(db_error)}")
        
        # Limpiar archivo temporal
        try:
            os.remove(video_path)
            print(f"🗑️ Archivo temporal eliminado: {video_path}")
        except Exception as cleanup_error:
            print(f"⚠️ No se pudo eliminar archivo temporal: {cleanup_error}")
        
        return {
            "message": "Video grabado y guardado exitosamente",
            "video_id": db_video.id,
            "filename": filename,
            "duration": video_info.get('duration', 0.0),
            "file_size": video_info.get('file_size', 0),
            "base64_length": len(base64_data),
            "base64_size_mb": base64_size_mb
        }
    
    except HTTPException:
        # Re-lanzar HTTPExceptions tal como están
        raise
    except Exception as e:
        # Log completo del error
        error_trace = traceback.format_exc()
        print(f"❌ Error inesperado en record_video:")
        print(error_trace)
        
        # Limpiar archivo temporal si existe
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                print(f"🗑️ Archivo temporal limpiado tras error: {video_path}")
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/videos", response_model=List[schemas.VideoResponse])
async def get_videos(db: Session = Depends(get_db)):
    """Obtiene la lista de videos"""
    try:
        videos = db.query(models.Video).order_by(models.Video.created_at.desc()).all()
        print(f"📋 Encontrados {len(videos)} videos en la base de datos")
        return videos
    except Exception as e:
        print(f"❌ Error obteniendo videos: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo videos: {str(e)}")

@app.get("/videos/{video_id}", response_model=schemas.VideoWithBase64)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """Obtiene un video específico con su Base64"""
    try:
        video = db.query(models.Video).filter(models.Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        print(f"📹 Obteniendo video ID {video_id}: {video.filename}")
        
        # Verificar que el Base64 no esté vacío
        if not video.video_base64:
            print(f"❌ Error: Video {video_id} no tiene datos Base64")
            raise HTTPException(status_code=404, detail="Video sin datos Base64")
        
        # Log para depuración
        print(f"📊 Base64 length: {len(video.video_base64)} caracteres")
        
        return video
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo video: {str(e)}")

@app.delete("/videos/{video_id}")
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    """Elimina un video"""
    try:
        video = db.query(models.Video).filter(models.Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        filename = video.filename
        db.delete(video)
        db.commit()
        
        print(f"🗑️ Video eliminado: {filename}")
        return {"message": "Video eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error eliminando video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error eliminando video: {str(e)}")

@app.get("/test-db")
async def test_database_connection(db: Session = Depends(get_db)):
    """Endpoint para probar la conexión a la base de datos"""
    try:
        result = db.execute(text("SELECT version()")).fetchone()
        video_count = db.query(models.Video).count()
        
        return {
            "status": "success",
            "database_version": result[0] if result else "Unknown",
            "video_count": video_count,
            "message": "Conexión a la base de datos OK"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

@app.get("/debug/video/{video_id}")
async def debug_video(video_id: int, db: Session = Depends(get_db)):
    """Endpoint de debug para verificar el video"""
    try:
        video = db.query(models.Video).filter(models.Video.id == video_id).first()
        if not video:
            return {"error": "Video no encontrado"}
        
        base64_preview = video.video_base64[:100] if video.video_base64 else "NULL"
        
        return {
            "id": video.id,
            "filename": video.filename,
            "duration": video.duration,
            "file_size": video.file_size,
            "base64_length": len(video.video_base64) if video.video_base64 else 0,
            "base64_preview": base64_preview,
            "created_at": video.created_at,
            "has_base64": bool(video.video_base64),
            "base64_starts_with": video.video_base64[:20] if video.video_base64 else None
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)