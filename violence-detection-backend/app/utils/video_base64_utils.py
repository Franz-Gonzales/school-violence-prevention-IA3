# app/utils/video_base64_utils.py - NUEVO ARCHIVO
"""
Utilidades para conversión de video a Base64 - Basado en ejemplo funcional
"""
import cv2
import base64
import subprocess
import os
from pathlib import Path
from typing import Optional, Dict, Any
from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


def convert_video_to_web_format(input_path: str, output_path: str) -> bool:
    """CORREGIDO: Conversión con FPS consistente y sin reproducción rápida"""
    try:
        print(f"🔄 Convirtiendo {input_path} a formato web...")
        
        # Verificar que FFmpeg está disponible
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ FFmpeg no está instalado o no está en PATH")
            return False
        
        # *** CORRECCIÓN: FPS fijo y consistente ***
        target_fps = "12"  # *** FPS fijo para evitar reproducción rápida ***
        
        print(f"📊 Usando FPS fijo: {target_fps} para conversión web")
        
        # *** COMANDO FFMPEG CORREGIDO ***
        command = [
            'ffmpeg',
            '-i', input_path,                    # Input file
            '-c:v', 'libx264',                   # Video codec H.264
            '-profile:v', 'baseline',            # Profile compatible con web
            '-level', '3.0',                     # Level compatible
            '-pix_fmt', 'yuv420p',              # Pixel format compatible
            '-r', target_fps,                   # *** FPS FIJO ***
            '-g', '24',                         # *** NUEVO: GOP size para estabilidad ***
            '-keyint_min', '12',                # *** NUEVO: Keyframe interval mínimo ***
            '-movflags', '+faststart',           # Optimización para web
            '-preset', 'medium',                 # *** CAMBIADO: preset más estable ***
            '-crf', '20',                       # *** MEJORADO: mejor calidad ***
            '-maxrate', '2M',                   # *** AUMENTADO: mejor bitrate ***
            '-bufsize', '4M',                   # *** AUMENTADO: buffer más grande ***
            '-vsync', 'cfr',                    # *** NUEVO: Constant frame rate ***
            '-force_fps',                       # *** NUEVO: Forzar FPS consistente ***
            '-y',                               # Sobrescribir output
            output_path
        ]
        
        print(f"🔧 Comando FFmpeg CORREGIDO: {' '.join(command)}")
        
        # Ejecutar conversión
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Video convertido exitosamente: {output_path}")
            
            # *** VERIFICACIÓN CORREGIDA de FPS ***
            try:
                cap = cv2.VideoCapture(output_path)
                converted_fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                duration = frame_count / converted_fps if converted_fps > 0 else 0
                cap.release()
                
                print(f"📊 FPS del archivo convertido: {converted_fps}")
                print(f"📊 Frames totales: {frame_count}")
                print(f"📊 Duración: {duration:.2f} segundos")
                
                # *** VERIFICAR QUE EL FPS ES CORRECTO ***
                if abs(converted_fps - float(target_fps)) > 1.0:
                    print(f"⚠️ Advertencia: FPS convertido ({converted_fps}) difiere del objetivo ({target_fps})")
                else:
                    print(f"✅ FPS convertido correctamente: {converted_fps}")
                    
            except Exception as fps_error:
                print(f"⚠️ No se pudo verificar FPS del video convertido: {fps_error}")
            
            # Verificar que el archivo se creó correctamente
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:  # Al menos 1KB
                file_size = os.path.getsize(output_path)
                print(f"📏 Tamaño del archivo convertido: {file_size} bytes")
                return True
            else:
                print("❌ El archivo convertido está vacío o es muy pequeño")
                return False
        else:
            print(f"❌ Error en FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error convirtiendo video: {e}")
        return False

def video_to_base64(video_path: str) -> Optional[str]:
    """
    Convierte un archivo de video a Base64 con conversión web-compatible
    Basado exactamente en el ejemplo funcional de Prueba_video_base64
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(video_path):
            print(f"❌ Error: El archivo no existe: {video_path}")
            return None
        
        # Crear archivo temporal convertido
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        temp_dir = configuracion.VIDEO_EVIDENCE_PATH / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        converted_path = temp_dir / f"{base_name}_web.mp4"
        
        # Convertir a formato web-compatible
        if not convert_video_to_web_format(video_path, str(converted_path)):
            print("❌ Error: No se pudo convertir el video a formato web")
            return None
        
        # Usar el archivo convertido para Base64
        final_path = converted_path
        
        file_size = os.path.getsize(final_path)
        print(f"📏 Tamaño del archivo convertido: {file_size} bytes")
        
        # Límite de 10MB para el archivo convertido
        if file_size > 10 * 1024 * 1024:
            print(f"⚠️ Advertencia: Archivo convertido muy grande ({file_size} bytes)")
        
        with open(final_path, "rb") as video_file:
            video_data = video_file.read()
            print(f"📖 Datos leídos del archivo convertido: {len(video_data)} bytes")
            
            if len(video_data) == 0:
                print("❌ Error: El archivo convertido está vacío")
                return None
            
            base64_data = base64.b64encode(video_data).decode('utf-8')
            print(f"🔄 Base64 generado: {len(base64_data)} caracteres")
            
            # Verificar que el Base64 es válido
            try:
                decoded_test = base64.b64decode(base64_data)
                if len(decoded_test) != len(video_data):
                    print("❌ Error: Validación de Base64 falló")
                    return None
                print("✅ Base64 validado correctamente")
            except Exception as validation_error:
                print(f"❌ Error validando Base64: {validation_error}")
                return None
        
        # Limpiar archivo convertido temporal
        try:
            os.remove(converted_path)
            print(f"🗑️ Archivo convertido temporal eliminado: {converted_path}")
        except:
            pass
        
        return base64_data
            
    except Exception as e:
        print(f"❌ Error convirtiendo video a Base64: {e}")
        return None


def get_video_info_detailed(video_path: str) -> Dict[str, Any]:
    """
    Obtiene información detallada del video
    Basado en el ejemplo funcional
    """
    try:
        if not os.path.exists(video_path):
            print(f"❌ Error: El archivo no existe: {video_path}")
            return {'duration': 0, 'file_size': 0, 'fps': 0, 'resolution': '0x0'}
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Error: No se pudo abrir el video: {video_path}")
            return {'duration': 0, 'file_size': 0, 'fps': 0, 'resolution': '0x0'}
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        file_size = os.path.getsize(video_path)
        
        print(f"📊 Video info - FPS: {fps}, Frames: {frame_count}, Duración: {duration:.2f}s, "
              f"Resolución: {width}x{height}, Tamaño: {file_size} bytes")
        
        return {
            'duration': duration,
            'file_size': file_size,
            'fps': fps,
            'resolution': f"{width}x{height}",
            'width': width,
            'height': height,
            'frame_count': frame_count
        }
    except Exception as e:
        print(f"❌ Error obteniendo info del video: {e}")
        return {'duration': 0, 'file_size': 0, 'fps': 0, 'resolution': '0x0'}


def validate_base64_video(base64_data: str) -> bool:
    """Valida que el Base64 sea un video válido"""
    try:
        if not base64_data:
            return False
        
        # Intentar decodificar
        decoded = base64.b64decode(base64_data)
        
        # Verificar que tiene contenido
        if len(decoded) < 1000:  # Al menos 1KB
            return False
        
        # Verificar magic bytes de MP4
        if decoded[:4] not in [b'ftyp', b'\x00\x00\x00\x20ftyp']:
            # Buscar ftyp en los primeros bytes
            if b'ftyp' not in decoded[:100]:
                print("⚠️ Advertencia: No se detectó formato MP4 válido")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validando Base64: {e}")
        return False