import os
import subprocess
from tqdm import tqdm
import logging
from pathlib import Path
from multiprocessing import Pool, cpu_count
from concurrent.futures import ThreadPoolExecutor

class VideoConverter:
    def __init__(self, input_folder, output_folder, num_workers=None):
        """
        Inicializa el convertidor de video.
        
        Args:
            input_folder (str): Ruta a la carpeta con los videos .mpeg
            output_folder (str): Ruta donde se guardarán los videos .mp4
            num_workers (int): Número de workers para procesamiento paralelo
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.num_workers = num_workers or min(cpu_count(), 8)  # Limitar a 8 cores máximo
        
    def get_mpeg_files(self):
        return list(self.input_folder.glob('*.mpeg'))
    
    def convert_video(self, input_path):
        """Convierte un video individual."""
        try:
            output_path = self.output_folder / f"{input_path.stem}.mp4"
            
            command = [
                'ffmpeg',
                '-i', str(input_path),
                '-c:v', 'libx264',
                '-preset', 'veryfast',  # Más rápido que 'medium'
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-movflags', '+faststart',
                '-threads', str(2),  # Usar 2 threads por proceso
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,  # Reducir overhead de I/O
                stderr=subprocess.PIPE,
                text=True
            )
            
            return (input_path.name, result.returncode == 0)
            
        except Exception as e:
            return (input_path.name, False)
    
    def process_videos(self):
        mpeg_files = self.get_mpeg_files()
        
        if not mpeg_files:
            print("No se encontraron archivos .mpeg en la carpeta de entrada")
            return
        
        print(f"Iniciando conversión de {len(mpeg_files)} videos usando {self.num_workers} workers...")
        
        # Usar ThreadPoolExecutor para mostrar la barra de progreso
        with ThreadPoolExecutor(max_workers=1) as progress_executor:
            # Usar Pool para el procesamiento paralelo de videos
            with Pool(processes=self.num_workers) as pool:
                # Crear un iterador de resultados
                results_iterator = pool.imap_unordered(self.convert_video, mpeg_files)
                
                # Configurar la barra de progreso
                successful = 0
                failed = 0
                
                with tqdm(total=len(mpeg_files), desc="Convirtiendo videos") as pbar:
                    for filename, success in results_iterator:
                        if success:
                            successful += 1
                        else:
                            failed += 1
                        pbar.update(1)
                        pbar.set_postfix({'Exitosos': successful, 'Fallidos': failed})
        
        print(f"""
        Conversión completada:
        - Videos procesados: {len(mpeg_files)}
        - Conversiones exitosas: {successful}
        - Conversiones fallidas: {failed}
        - Carpeta de salida: {self.output_folder}
        - Workers utilizados: {self.num_workers}
        """)

def main():
    input_folder = r"C:\Users\franz\Downloads\archive (5)\dataset\NON_CCTV_DATA"
    output_folder = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\procesados\clips_procesar"
    
    try:
        # Crear el convertidor con procesamiento paralelo
        converter = VideoConverter(
            input_folder=input_folder,
            output_folder=output_folder,
            num_workers=None  # Automáticamente usa el número óptimo de cores
        )
        converter.process_videos()
        
    except Exception as e:
        print(f"Error en la ejecución del programa: {str(e)}")
        raise

if __name__ == "__main__":
    main()