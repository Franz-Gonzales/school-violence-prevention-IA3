import os
import subprocess
from tqdm import tqdm

# Rutas predefinidas
INPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_V2\videosV2_timesformer\no_violence"  # Carpeta con videos
OUTPUT_FOLDER = r"C:\GONZALES\dataset_violencia\dataset_V2\images_yolo_process"     # Carpeta para frames

def process_videos(input_folder, output_folder):
    """
    Extrae 3 frames de videos, los mejora y los guarda en 640x640 para YOLOv8n.
    
    Args:
        input_folder (str): Ruta a la carpeta con videos
        output_folder (str): Ruta a la carpeta de salida para frames
    """
    # Crear directorio de salida si no existe
    os.makedirs(output_folder, exist_ok=True)

    # Verificar que la carpeta de entrada exista
    if not os.path.exists(input_folder):
        print(f"Error: La carpeta de entrada {input_folder} no existe.")
        return

    # Obtener lista de videos
    videos = [f for f in os.listdir(input_folder) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv'))]
    if not videos:
        print(f"Error: No se encontraron videos en {input_folder}.")
        return

    print(f"Procesando {len(videos)} videos en {input_folder}...")

    # Procesar cada video
    for video in tqdm(videos):
        video_path = os.path.join(input_folder, video)
        base_name = os.path.splitext(video)[0]  # Ej. violence_001
        
        # Frame 1: Segundo 1 (frame 15 a 15 FPS)
        output_1 = os.path.join(output_folder, f"{base_name}_frame_001.jpg")
        cmd_1 = (
            f"ffmpeg -i \"{video_path}\" -vf "
            f"select=eq(n\\,15),unsharp=5:5:1.0,scale=640:640:force_original_aspect_ratio=decrease,pad=640:640:(ow-iw)/2:(oh-ih)/2 "
            f"-frames:v 1 -q:v 1 \"{output_1}\" -y"
        )
        result_1 = subprocess.run(cmd_1, shell=True, capture_output=True, text=True)
        if result_1.returncode != 0:
            print(f"Error al procesar {video} (frame 1): {result_1.stderr}")
        
        # Frame 2: Segundo 3 (frame 45 a 15 FPS)
        output_2 = os.path.join(output_folder, f"{base_name}_frame_002.jpg")
        cmd_2 = (
            f"ffmpeg -i \"{video_path}\" -vf "
            f"select=eq(n\\,30),unsharp=5:5:1.0,scale=640:640:force_original_aspect_ratio=decrease,pad=640:640:(ow-iw)/2:(oh-ih)/2 "
            f"-frames:v 1 -q:v 1 \"{output_2}\" -y"
        )
        result_2 = subprocess.run(cmd_2, shell=True, capture_output=True, text=True)
        if result_2.returncode != 0:
            print(f"Error al procesar {video} (frame 2): {result_2.stderr}")
        
        # Frame 3: Segundo 5 (frame 75 a 15 FPS)
        output_3 = os.path.join(output_folder, f"{base_name}_frame_003.jpg")
        cmd_3 = (
            f"ffmpeg -i \"{video_path}\" -vf "
            f"select=eq(n\\,45),unsharp=5:5:1.0,scale=640:640:force_original_aspect_ratio=decrease,pad=640:640:(ow-iw)/2:(oh-ih)/2 "
            f"-frames:v 1 -q:v 1 \"{output_3}\" -y"
        )
        result_3 = subprocess.run(cmd_3, shell=True, capture_output=True, text=True)
        if result_3.returncode != 0:
            print(f"Error al procesar {video} (frame 3): {result_3.stderr}")

    # Contar frames generados
    frames_generated = len([f for f in os.listdir(output_folder) if f.endswith('.jpg')])
    print(f"¡Frames procesados en {output_folder}!")
    print(f"Total de frames extraídos: {frames_generated}")
    print("Puedes moverlos manualmente a train/val/test según necesites.")

if __name__ == "__main__":
    print("=== INICIANDO PROCESAMIENTO DE FRAMES ===")
    print(f"Carpeta de entrada: {INPUT_FOLDER}")
    print(f"Carpeta de salida: {OUTPUT_FOLDER}")
    print("========================================")

    # Ejecutar procesamiento
    process_videos(INPUT_FOLDER, OUTPUT_FOLDER)