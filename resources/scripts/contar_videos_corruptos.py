import os
import subprocess
from pathlib import Path
from tqdm import tqdm

def verificar_video(ruta_video):
    """
    Verifica si un video está corrupto usando FFmpeg.
    Retorna una tupla (nombre_archivo, está_corrupto, mensaje_error)
    """
    try:
        resultado = subprocess.run(
            ['ffmpeg', '-v', 'error', '-i', str(ruta_video), '-f', 'null', '-'],
            stderr=subprocess.PIPE,
            text=True
        )
        
        if resultado.stderr:
            return (ruta_video.name, True, resultado.stderr)
        return (ruta_video.name, False, "")
        
    except Exception as e:
        return (ruta_video.name, True, str(e))

def buscar_videos_corruptos(directorio):
    """Busca videos corruptos en el directorio especificado."""
    # Obtener lista de videos MP4
    directorio = Path(directorio)
    archivos_video = list(directorio.glob("**/*.[mM][pP]4"))
    
    if not archivos_video:
        print("No se encontraron archivos de video en el directorio.")
        return
    
    print(f"\n{'='*60}")
    print(f"Analizando {len(archivos_video)} videos en: {directorio}")
    print(f"{'='*60}\n")
    
    videos_corruptos = []
    
    # Analizar cada video con barra de progreso
    for video in tqdm(archivos_video, desc="Verificando videos"):
        nombre, corrupto, error = verificar_video(video)
        if corrupto:
            videos_corruptos.append((nombre, error))
    
    # Mostrar resultados
    print(f"\n{'='*60}")
    print("RESULTADOS DEL ANÁLISIS")
    print(f"{'='*60}")
    print(f"Total de videos analizados: {len(archivos_video)}")
    print(f"Videos corruptos encontrados: {len(videos_corruptos)}")
    
    if videos_corruptos:
        print("\nLista de videos corruptos encontrados:")
        print("-" * 60)
        for nombre, error in videos_corruptos:
            print(f"✘ {nombre}")
            print(f"  Error: {error.split('\\n')[0]}")  # Solo muestra la primera línea del error
            print("-" * 60)
    else:
        print("\nNo se encontraron videos corruptos.")

if __name__ == "__main__":
    # Directorio que contiene los videos a analizar
    DIRECTORIO_VIDEOS = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_reparados\videos_corruptos"
    
    buscar_videos_corruptos(DIRECTORIO_VIDEOS)