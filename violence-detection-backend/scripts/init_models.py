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


def configurar_modelos():
    """Configura los modelos necesarios"""
    modelos_dir = configuracion.MODELOS_PATH
    modelos_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Directorio de modelos: {modelos_dir}")
    
    # Verificar modelos existentes
    yolo_path = modelos_dir / configuracion.YOLO_MODEL
    timesformer_path = modelos_dir / configuracion.TIMESFORMER_MODEL
    
    modelos_faltantes = []
    
    if not yolo_path.exists():
        modelos_faltantes.append(("YOLO", yolo_path))
        logger.warning(f"Modelo YOLO no encontrado: {yolo_path}")
    
    if not timesformer_path.exists():
        modelos_faltantes.append(("TimesFormer", timesformer_path))
        logger.warning(f"Modelo TimesFormer no encontrado: {timesformer_path}")
    
    if modelos_faltantes:
        print("\n MODELOS FALTANTES DETECTADOS")
        print("Los siguientes modelos no se encontraron:")
        for nombre, ruta in modelos_faltantes:
            print(f"  - {nombre}: {ruta}")
        
        print("\nPor favor, coloca los modelos entrenados en las rutas indicadas.")
        print("\nAlternativamente, puedes:")
        print("1. Descargar modelos pre-entrenados de Hugging Face")
        print("2. Entrenar tus propios modelos")
        print("3. Usar los modelos de ejemplo (menor precisión)")
        
        respuesta = input("\n¿Desea continuar sin los modelos? (s/n): ")
        if respuesta.lower() != 's':
            sys.exit(1)
    else:
        logger.info("Todos los modelos encontrados correctamente")
    
    # Crear estructura de directorios adicionales
    subdirs = ['processor', 'checkpoints', 'exports']
    for subdir in subdirs:
        (modelos_dir / subdir).mkdir(exist_ok=True)
    
    logger.info("Configuración de modelos completada")


def crear_archivo_ejemplo():
    """Crea un archivo de ejemplo para pruebas"""
    ejemplo_config = """
# Configuración de Modelos de IA

## Modelos Requeridos:

1. **YOLOv11 para detección de personas**
   - Archivo: yolov11_personas.pt
   - Entrenado para detectar solo clase 'persona'
   
2. **TimesFormer para detección de violencia**
   - Archivo: timesformer_violence_detector_best_ft.pt
   - Modelo fine-tuned para clasificación binaria (violencia/no violencia)
   
3. **Procesador TimesFormer**
   - Directorio: processor/
   - Contiene archivos de configuración del procesador

## Ubicación:
Todos los modelos deben estar en: {ruta_modelos}

## Entrenamiento:
Si necesitas entrenar tus propios modelos, consulta la documentación en:
https://github.com/tu-repo/docs/training.md
"""
    
    readme_path = configuracion.MODELOS_PATH / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(ejemplo_config.format(ruta_modelos=configuracion.MODELOS_PATH))
    
    logger.info(f"Archivo de información creado: {readme_path}")


def main():
    """Función principal"""
    logger.info("Iniciando configuración de modelos")
    
    # Configurar modelos
    configurar_modelos()
    
    # Crear archivo de información
    crear_archivo_ejemplo()
    
    logger.info("Configuración completada")
    
    print("\n✅ Configuración de modelos completada")
    print(f"📁 Los modelos deben estar en: {configuracion.MODELOS_PATH}")
    print("\n🚀 Próximos pasos:")
    print("1. Coloca tus modelos entrenados en el directorio indicado")
    print("2. Ejecuta el servidor con: python -m uvicorn app.main:app --reload")
    print("3. Accede a la documentación en: http://localhost:8000/docs")


if __name__ == "__main__":
    main()