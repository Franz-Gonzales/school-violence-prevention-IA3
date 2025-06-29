import os
import re
import ffmpeg
from collections import defaultdict
from tqdm import tqdm

def get_video_info(file_path):
    """
    Obtiene información del video usando ffprobe.
    
    Args:
        file_path (str): Ruta al archivo de video
    
    Returns:
        tuple: ((width, height), fps) o (None, None) si hay error
    """
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] 
                        if stream['codec_type'] == 'video'), None)
        
        if video_stream:
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            fps = eval(video_stream['avg_frame_rate'])  # Evalúa fracciones como "30000/1001"
            duration = float(video_stream.get('duration', 0))
            return (width, height), fps, duration
            
    except ffmpeg.Error as e:
        print(f"\nError de FFmpeg en {os.path.basename(file_path)}: {e.stderr.decode()}")
    except Exception as e:
        print(f"\nError al procesar {os.path.basename(file_path)}: {str(e)}")
    
    return None, None, None

def analyze_videos_in_folder(folder_path):
    """
    Analiza todos los videos en una carpeta y muestra estadísticas.
    
    Args:
        folder_path (str): Ruta a la carpeta con videos
    """
    resolution_count = defaultdict(int)
    fps_count = defaultdict(int)
    duration_stats = {'total': 0, 'min': float('inf'), 'max': 0}
    total_videos = 0
    failed_videos = []

    # Validar directorio
    if not os.path.isdir(folder_path):
        print(f"Error: El directorio '{folder_path}' no existe.")
        return

    print(f"\n{'='*50}")
    print(f"Analizando videos en: {folder_path}")
    print(f"{'='*50}\n")

    # Obtener lista de videos
    video_files = [f for f in os.scandir(folder_path) 
                if f.is_file() and f.name.lower().endswith(
                    ('.mp4', '.avi', '.mov', '.mkv', '.webm'))]

    # Procesar videos con barra de progreso
    for entry in tqdm(video_files, desc="Procesando videos"):
        total_videos += 1
        resolution, fps, duration = get_video_info(entry.path)
        
        if resolution and fps and duration:
            resolution_count[resolution] += 1
            fps_count[fps] += 1
            duration_stats['total'] += duration
            duration_stats['min'] = min(duration_stats['min'], duration)
            duration_stats['max'] = max(duration_stats['max'], duration)
        else:
            failed_videos.append(entry.name)

    # Mostrar resultados
    print(f"\n{'='*50}")
    print("RESUMEN DEL ANÁLISIS")
    print(f"{'='*50}")
    print(f"\nTotal de videos analizados: {total_videos}")
    
    if total_videos > 0:
        print("\nDistribución por resolución:")
        for res, count in sorted(resolution_count.items(), key=lambda x: (-x[1], x[0])):
            percentage = (count / total_videos) * 100
            print(f"{res[0]}x{res[1]}: {count} videos ({percentage:.1f}%)")

        print("\nDistribución por FPS:")
        for fps, count in sorted(fps_count.items(), key=lambda x: (-x[1], x[0])):
            percentage = (count / total_videos) * 100
            print(f"{fps:.1f} FPS: {count} videos ({percentage:.1f}%)")

        if duration_stats['total'] > 0:
            print("\nEstadísticas de duración:")
            print(f"Total: {duration_stats['total']/60:.1f} minutos")
            print(f"Mínima: {duration_stats['min']:.1f} segundos")
            print(f"Máxima: {duration_stats['max']:.1f} segundos")
            print(f"Promedio: {(duration_stats['total']/total_videos):.1f} segundos")

        if failed_videos:
            print("\nVideos con errores:")
            for video in failed_videos:
                print(f"- {video}")

if __name__ == "__main__":
    # Ruta de la carpeta a analizar
    folder_path = r"C:\GONZALES\dataset_violencia\video_aumentation\no_violence"
    analyze_videos_in_folder(folder_path)