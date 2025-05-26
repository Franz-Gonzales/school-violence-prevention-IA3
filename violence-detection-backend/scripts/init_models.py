"""
Script para descargar y configurar modelos iniciales
"""
import os
import sys
from pathlib import Path
import requests
from tqdm import tqdm

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import configuracion
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)


def descargar_archivo(url: str, destino: Path, descripcion: str = "Descargando"):
    """Descarga un archivo con barra de progreso"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    destino.parent.mkdir(parents=True, exist_ok=True)
    
    with open(destino, 'wb') as file:
        with tqdm(
            desc=descripcion,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                pbar.update(size)


def verificar_dependencias():
    """Verifica las dependencias necesarias"""
    try:
        import onnxruntime
        logger.info("✅ ONNX Runtime instalado correctamente")
    except ImportError:
        logger.error("❌ ONNX Runtime no encontrado. Instalando...")
        os.system("pip install onnxruntime-gpu" if configuracion.USE_GPU else "pip install onnxruntime")

def configurar_modelos():
    """Configura los modelos necesarios"""
    verificar_dependencias()
    logger.info("Iniciando configuración de modelos", emoji="🚀")
    print("🚀 Iniciando configuración de modelos")
    
    modelos_dir = configuracion.MODELOS_PATH
    modelos_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Verificando directorio de modelos", directorio=str(modelos_dir), emoji="📁")
    print(f"📁 Verificando directorio de modelos: {modelos_dir}")
    
    # Verificar modelos existentes
    yolo_path = modelos_dir / configuracion.YOLO_MODEL
    timesformer_path = modelos_dir / configuracion.TIMESFORMER_MODEL
    
    modelos_faltantes = []
    
    if not yolo_path.exists():
        modelos_faltantes.append(("YOLO", yolo_path))
        logger.warning("Modelo YOLO no encontrado", ruta=str(yolo_path), emoji="⚠️")
        print(f"⚠️ Modelo YOLO no encontrado: {yolo_path}")
    
    if not timesformer_path.exists():
        modelos_faltantes.append(("TimesFormer", timesformer_path))
        logger.warning("Modelo TimesFormer no encontrado", ruta=str(timesformer_path), emoji="⚠️")
        print(f"⚠️ Modelo TimesFormer no encontrado: {timesformer_path}")
    
    if modelos_faltantes:
        logger.warning("Se detectaron modelos faltantes", cantidad=len(modelos_faltantes), modelos=[m[0] for m in modelos_faltantes], emoji="⚠️")
        print(f"\n⚠️ Se detectaron {len(modelos_faltantes)} modelos faltantes:")
        
        for nombre, ruta in modelos_faltantes:
            print(f"  - {nombre}: {ruta}")
        
        print("\nPor favor:")
        print("1. Coloca los modelos entrenados en las rutas indicadas")
        print("2. O descarga modelos pre-entrenados de Hugging Face")
        print("3. O usa los modelos de ejemplo (menor precisión)")
        
        respuesta = input("\n¿Desea continuar sin los modelos? (s/n): ")
        if respuesta.lower() != 's':
            sys.exit(1)
    else:
        logger.info("Todos los modelos verificados correctamente", emoji="✅")
        print("✅ Todos los modelos verificados correctamente")
    
    # Crear estructura de directorios
    for subdir in ['checkpoints', 'exports']:
        dir_path = modelos_dir / subdir
        dir_path.mkdir(exist_ok=True)
        logger.debug(f"Directorio creado: {subdir}", ruta=str(dir_path), emoji="📁")
        print(f"📁 Directorio creado: {dir_path}")
    
    logger.info("Configuración de modelos completada exitosamente", emoji="✅")
    print("✅ Configuración de modelos completada exitosamente")


def crear_archivo_ejemplo():
    """Crea un archivo de ejemplo para pruebas"""
    ejemplo_config = """
# Configuración de Modelos de IA

## Modelos Requeridos:

1. **YOLOv11 para detección de personas**
   - Archivo: yolov11_personas.pt
   - Entrenado para detectar solo clase 'persona'
   
2. **TimesFormer para detección de violencia**
   - Archivo: timesformer_violence_detector_half.onnx
   - Modelo optimizado para clasificación binaria (violencia/no violencia)
   - Formato: ONNX para mejor rendimiento y compatibilidad

## Ubicación:
Todos los modelos deben estar en: {ruta_modelos}

## Formato de Entrada (TimesFormer ONNX):
- Tamaño de entrada: 224x224
- Número de frames: 8
- Formato: [batch_size, channels, num_frames, height, width]
- Normalización: mean=[0.45, 0.45, 0.45], std=[0.225, 0.225, 0.225]

## Entrenamiento:
Si necesitas entrenar tus propios modelos, consulta la documentación en:
https://github.com/tu-repo/docs/training.md
"""
    
    readme_path = configuracion.MODELOS_PATH / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(ejemplo_config.format(ruta_modelos=configuracion.MODELOS_PATH))
    
    logger.info(f"Archivo de información creado: {readme_path}")
    print(f"Archivo de información creado: {readme_path}")


def main():
    """Función principal"""
    logger.info("Iniciando configuración de modelos")
    print("Iniciando configuración de modelos")
    
    # Configurar modelos
    configurar_modelos()
    
    # Crear archivo de información
    crear_archivo_ejemplo()
    
    logger.info("Configuración completada")
    print("Configuración completada")
    
    print("\n✅ Configuración de modelos completada")
    print(f"📁 Los modelos deben estar en: {configuracion.MODELOS_PATH}")
    print("\n🚀 Próximos pasos:")
    print("1. Coloca tus modelos entrenados en el directorio indicado")
    print("2. Ejecuta el servidor con: python -m uvicorn app.main:app --reload")
    print("3. Accede a la documentación en: http://localhost:8000/docs")


if __name__ == "__main__":
    main()