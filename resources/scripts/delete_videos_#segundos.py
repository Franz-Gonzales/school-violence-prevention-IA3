import os
from moviepy.editor import VideoFileClip

def eliminar_videos_con_duracion_cero(carpeta_videos):
    """
    Elimina todos los archivos de video con duración 0 segundos en una carpeta específica.
    
    Args:
        carpeta_videos (str): Ruta a la carpeta que contiene los videos.
    """
    if not os.path.exists(carpeta_videos):
        raise FileNotFoundError(f"La carpeta especificada no existe: {carpeta_videos}")
    
    print("=" * 60)
    print("ELIMINADOR DE VIDEOS CON DURACIÓN 0 SEGUNDOS")
    print(f"Carpeta analizada: {carpeta_videos}")
    print("=" * 60)

    videos_eliminados = 0
    videos_conservados = 0
    errores = 0
    num_segundo = 3.5  # Numero de segundos que deseas eliminar

    for archivo in os.listdir(carpeta_videos):
        ruta_archivo = os.path.join(carpeta_videos, archivo)

        # Saltar si no es un archivo
        if not os.path.isfile(ruta_archivo):
            continue

        # Verificar extensión de video (puedes ajustar esta lista según tus formatos)
        extensiones_validas = ['.mp4', '.avi', '.mov', '.mkv', '.webm', 'mpg']
        _, ext = os.path.splitext(archivo)
        if ext.lower() not in extensiones_validas:
            continue

        try:
            # Cargar video con moviepy
            video = VideoFileClip(ruta_archivo)
            duracion = video.duration
            video.close()

            if duracion < num_segundo or duracion is None:
                os.remove(ruta_archivo)
                print(f"[ELIMINADO] {archivo} (duración: 0s)")
                videos_eliminados += 1
            else:
                print(f"[OK] {archivo} (duración: {duracion:.2f}s)")
                videos_conservados += 1

        except Exception as e:
            print(f"[ERROR] No se pudo procesar {archivo}: {str(e)}")
            errores += 1
            continue

    print("\n" + "=" * 60)
    print("RESUMEN DE LA EJECUCIÓN")
    print("=" * 60)
    print(f"Videos eliminados (0s): {videos_eliminados}")
    print(f"Videos conservados     : {videos_conservados}")
    print(f"Errores al procesar    : {errores}")
    print("=" * 60)


# PUNTO DE ENTRADA
if __name__ == "__main__":
    # MODIFICA ESTA RUTA CON TU CARPETA DE VIDEOS
    CARPETA_VIDEOS = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_procesar\ambiguo"
    
    try:
        eliminar_videos_con_duracion_cero(CARPETA_VIDEOS)
    except Exception as e:
        print(f"ERROR CRÍTICO: {str(e)}")
