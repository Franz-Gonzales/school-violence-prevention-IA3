import os
import subprocess

#  Configura las rutas de las carpetas
carpeta_origen = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_procesar\procesados"  # Carpeta con videos .avi
carpeta_destino = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\datos_procesar\videos_listos\no_violencia"  # Carpeta donde se guardarán los .mp4 convertidos

# Asegurar que la carpeta de destino existe
os.makedirs(carpeta_destino, exist_ok=True)

# Contador para numerar los videos procesados
contador = 1

# Buscar archivos .avi en la carpeta de origen
for archivo in os.listdir(carpeta_origen):
    if archivo.endswith(".avi"):
        ruta_avi = os.path.join(carpeta_origen, archivo)
        
        # Generar el nuevo nombre con numeración secuencial
        nuevo_nombre = f"processss{contador}.mp4"
        ruta_mp4 = os.path.join(carpeta_destino, nuevo_nombre)

        # Comando FFmpeg para convertir a MP4 sin pérdida de calidad
        comando = [
            "ffmpeg", "-i", ruta_avi, "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", ruta_mp4
        ]

        print(f"Convirtiendo: {archivo} -> {nuevo_nombre}")
        subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        contador += 1  # Incrementar el contador

print("Conversión completada. Los videos .mp4 están en:", carpeta_destino)
