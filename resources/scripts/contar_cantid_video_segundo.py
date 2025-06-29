import os
import cv2
import math
from collections import defaultdict

# CONFIGURA AQUÍ LAS RUTAS
ruta_carpeta = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\videos_completado\amenazante_ambigua"  # Cambia esto por la ruta a tu carpeta de videos
nombre_archivo_salida = "reporte_videos.txt"  # Nombre del archivo de salida
inicio = 1  # Segundo inicial para el análisis
fin = 30  # Segundo final para el análisis

def obtener_duracion_video(ruta_video):
    """
    Obtiene la duración de un video en segundos usando OpenCV.
    """
    try:
        video = cv2.VideoCapture(ruta_video)
        if not video.isOpened():
            print(f"Error: No se pudo abrir {ruta_video}")
            return None
            
        # Obtener frames por segundo y cantidad de frames
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Liberar el recurso del video
        video.release()
        
        if fps > 0:
            duracion = frame_count / fps
            return duracion
        else:
            print(f"Error: FPS es 0 en {ruta_video}")
            return None
    except Exception as e:
        print(f"Error al procesar {ruta_video}: {str(e)}")
        return None

def analizar_videos_por_duracion(carpeta_videos):
    """
    Recorre una carpeta de videos, analiza sus duraciones y las organiza por segundos enteros.
    """
    # Diccionario para almacenar los videos agrupados por duración (segundo entero)
    videos_por_duracion = defaultdict(list)
    
    # Extensiones comunes de archivos de video
    extensiones_video = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    
    # Recorrer todos los archivos en la carpeta
    total_videos = 0
    for archivo in os.listdir(carpeta_videos):
        ruta_completa = os.path.join(carpeta_videos, archivo)
        
        # Verificar si es un archivo y tiene extensión de video
        if os.path.isfile(ruta_completa) and any(archivo.lower().endswith(ext) for ext in extensiones_video):
            duracion = obtener_duracion_video(ruta_completa)
            
            if duracion is not None:
                # Redondear normalmente para clasificar correctamente (3.46s → 3s)
                segundo_entero = round(duracion)
                
                # Solo consideramos videos entre 1 y 10 segundos
                if inicio <= segundo_entero <= fin:
                    videos_por_duracion[segundo_entero].append(archivo)
                    total_videos += 1
    
    return videos_por_duracion, total_videos

def generar_reporte(videos_por_duracion, total_videos, ruta_salida):
    """
    Genera un archivo de texto con el reporte de videos agrupados por duración.
    """
    with open(ruta_salida, 'w', encoding='utf-8') as archivo_salida:
        archivo_salida.write(f"REPORTE DE ANÁLISIS DE VIDEOS\n")
        archivo_salida.write(f"Total de videos analizados: {total_videos}\n\n")
        
        # Generar el reporte para cada segundo (1-10)
        for segundo in range(1, fin + 1):
            videos = videos_por_duracion.get(segundo, [])
            cantidad = len(videos)
            
            if cantidad > 0:
                archivo_salida.write(f"- Videos con una duración de {segundo}s: {cantidad} videos\n")
                archivo_salida.write(f"Lista de videos con duración de {segundo} segundos:\n")
                
                for i, video in enumerate(videos, 1):
                    archivo_salida.write(f"{i}. {video}\n")
                
                archivo_salida.write("\n")
            else:
                archivo_salida.write(f"- No existen videos con una duración de {segundo}s\n\n")
    
    print(f"Reporte generado en: {os.path.abspath(ruta_salida)}")

def main():
    """
    Función principal que ejecuta el análisis de videos.
    """
    # Validar que la carpeta existe
    if not os.path.isdir(ruta_carpeta):
        print(f"Error: La ruta '{ruta_carpeta}' no es una carpeta válida.")
        return
    
    print(f"Analizando videos en: {ruta_carpeta}")
    print("Este proceso puede tardar dependiendo de la cantidad de videos...")
    
    # Analizar videos
    videos_por_duracion, total_videos = analizar_videos_por_duracion(ruta_carpeta)
    
    # Generar reporte
    generar_reporte(videos_por_duracion, total_videos, nombre_archivo_salida)
    
    print("Análisis completado.")

if __name__ == "__main__":
    main()