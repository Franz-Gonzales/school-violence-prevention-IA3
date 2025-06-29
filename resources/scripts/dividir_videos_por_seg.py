import os
from moviepy.editor import VideoFileClip
from tqdm import tqdm
import imageio
# imageio.plugins.ffmpeg.download()  # Asegura que FFMPEG esté disponible

# ===================== PARÁMETROS CONFIGURABLES =========================
INPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_procesar\procesar"
OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_procesar\ambiguo"
SEGMENT_DURATION = 5  # Duración de cada segmento en segundos
EXTENSIONES_VALIDAS = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
# ========================================================================

def dividir_videos_en_segmentos(input_folder, output_folder, segment_duration):
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"La carpeta de entrada no existe: {input_folder}")
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta de salida creada: {output_folder}")

    print("=" * 70)
    print("INICIANDO PROCESAMIENTO DE VIDEOS")
    print(f"Carpeta de entrada: {input_folder}")
    print(f"Carpeta de salida : {output_folder}")
    print(f"Duración de los clips: {segment_duration} segundos")
    print("=" * 70)

    archivos_procesados = 0
    errores = 0
    
    # Lista todos los archivos de video válidos
    archivos = [f for f in os.listdir(input_folder) 
                if os.path.isfile(os.path.join(input_folder, f)) 
                and os.path.splitext(f)[1].lower() in EXTENSIONES_VALIDAS]

    for archivo in tqdm(archivos, desc="Procesando videos"):
        ruta_video = os.path.join(input_folder, archivo)
        nombre_base, ext = os.path.splitext(archivo)

        try:
            # Configuración específica para evitar errores de FFMPEG
            video = VideoFileClip(ruta_video, audio=False)  # Deshabilitar audio
            duracion = video.duration

            if duracion <= 1:
                print(f"\n[OMITIDO] {archivo}: Duración insuficiente ({duracion:.2f} segundos)")
                video.close()
                continue

            num_segmentos = int(duracion // segment_duration)
            if duracion % segment_duration > 0:
                num_segmentos += 1

            for i in range(num_segmentos):
                inicio = i * segment_duration
                fin = min((i + 1) * segment_duration, duracion)

                if fin - inicio < 1:
                    continue

                clip = video.subclip(inicio, fin)
                nombre_clip = f"{nombre_base}_{str(i+1).zfill(3)}.mp4"
                ruta_salida = os.path.join(output_folder, nombre_clip)

                # Configuración mejorada para write_videofile
                clip.write_videofile(
                    ruta_salida,
                    codec="libx264",
                    audio=False,  # Sin audio
                    preset='ultrafast',  # Codificación más rápida
                    threads=4,  # Usar múltiples hilos
                    verbose=False,
                    logger=None,
                    ffmpeg_params=[
                        "-crf", "23",  # Calidad constante
                        "-movflags", "+faststart"  # Optimización para streaming
                    ]
                )
                clip.close()

            video.close()
            archivos_procesados += 1

        except Exception as e:
            print(f"\n[ERROR] No se pudo procesar {archivo}: {str(e)}")
            errores += 1
            continue

    print("\n" + "=" * 70)
    print("PROCESAMIENTO COMPLETADO")
    print(f"Videos procesados exitosamente : {archivos_procesados}")
    print(f"Videos con errores              : {errores}")
    print(f"Clips generados en: {output_folder}")
    print("=" * 70)

if __name__ == "__main__":
    dividir_videos_en_segmentos(INPUT_FOLDER, OUTPUT_FOLDER, SEGMENT_DURATION)