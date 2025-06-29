import os
import cv2
import math
import shutil

# PARÁMETROS CONFIGURABLES
ruta_carpeta_origen = r"C:\Users\franz\Downloads\datos_reciclar\videos" # Ruta de la carpeta con los videos originales
ruta_carpeta_destino = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_procesar\procesar"  # Ruta donde se moverán los videos seleccionados
duracion_objetivo =  19 # Mover todos los videos con esta duración (en segundos)

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
        
        # Liberar el recurs
        # o del video
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

def mover_videos_por_duracion():
    """
    Mueve videos de una duración específica a una carpeta de destino.
    """
    # Verificar que la carpeta de origen existe
    if not os.path.isdir(ruta_carpeta_origen):
        print(f"Error: La carpeta de origen '{ruta_carpeta_origen}' no existe.")
        return
    
    # Crear la carpeta de destino si no existe
    if not os.path.exists(ruta_carpeta_destino):
        try:
            os.makedirs(ruta_carpeta_destino)
            print(f"Carpeta de destino creada: {ruta_carpeta_destino}")
        except OSError as e:
            print(f"Error al crear la carpeta de destino: {e}")
            return
    
    # Extensiones comunes de archivos de video
    extensiones_video = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    
    # Contar videos para estadísticas
    total_videos = 0
    videos_movidos = 0
    
    print(f"Buscando videos de {duracion_objetivo} segundos en {ruta_carpeta_origen}...")
    
    # Recorrer todos los archivos en la carpeta de origen
    for archivo in os.listdir(ruta_carpeta_origen):
        ruta_completa = os.path.join(ruta_carpeta_origen, archivo)
        
        # Verificar si es un archivo y tiene extensión de video
        if os.path.isfile(ruta_completa) and any(archivo.lower().endswith(ext) for ext in extensiones_video):
            total_videos += 1
            
            # Obtener la duración del video
            duracion = obtener_duracion_video(ruta_completa)
            
            if duracion is not None:
                # Redondear la duración para clasificar correctamente
                segundo_redondeado = round(duracion)
                
                # Si la duración coincide con el objetivo, mover el video
                if segundo_redondeado == duracion_objetivo:
                    ruta_destino = os.path.join(ruta_carpeta_destino, archivo)
                    try:
                        shutil.move(ruta_completa, ruta_destino)
                        print(f"Movido: {archivo} ({duracion:.2f}s)")
                        videos_movidos += 1
                    except Exception as e:
                        print(f"Error al mover {archivo}: {e}")
    
    # Mostrar estadísticas finales
    print(f"\nProceso completado:")
    print(f"- Total de videos analizados: {total_videos}")
    print(f"- Videos de {duracion_objetivo} segundos encontrados y movidos: {videos_movidos}")

if __name__ == "__main__":
    mover_videos_por_duracion()