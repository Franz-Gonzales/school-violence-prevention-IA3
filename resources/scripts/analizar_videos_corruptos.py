import os
import subprocess
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class VerificadorIntegridadVideo:
    def __init__(self, directorio_entrada, directorio_salida, archivo_log="integridad_video.log"):
        """
        Inicializa el verificador de integridad de videos.
        
        Args:
            directorio_entrada (str): Directorio que contiene los videos a verificar
            directorio_salida (str): Directorio para los videos reparados
            archivo_log (str): Ruta del archivo de registro
        """
        self.directorio_entrada = Path(directorio_entrada)
        self.directorio_salida = Path(directorio_salida)
        self.directorio_salida.mkdir(parents=True, exist_ok=True)
        
        # Configurar registro de eventos
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(archivo_log),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("VerificadorVideo")
        
        # Estadísticas
        self.estadisticas = {
            'total_videos': 0,
            'videos_corruptos': 0,
            'videos_reparados': 0,
            'reparaciones_fallidas': 0
        }

    def verificar_integridad_video(self, ruta_video):
        """Verifica si un archivo de video está corrupto usando FFmpeg."""
        try:
            resultado = subprocess.run(
                ['ffmpeg', '-v', 'error', '-i', str(ruta_video), '-f', 'null', '-'],
                stderr=subprocess.PIPE,
                text=True
            )
            
            if resultado.stderr:
                self.logger.warning(f"Video corrupto encontrado: {ruta_video}")
                self.logger.debug(f"Errores FFmpeg: {resultado.stderr}")
                return False, resultado.stderr
            return True, ""
            
        except Exception as e:
            self.logger.error(f"Error al verificar {ruta_video}: {str(e)}")
            return False, str(e)

    def reparar_video(self, ruta_video):
        """Intenta reparar un archivo de video corrupto."""
        try:
            ruta_salida = self.directorio_salida / f"reparado_{ruta_video.name}"
            
            # Primer intento: Remux simple
            comando = [
                'ffmpeg', '-i', str(ruta_video),
                '-c:v', 'copy', '-c:a', 'copy',
                str(ruta_salida)
            ]
            
            resultado = subprocess.run(
                comando,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )
            
            # Verificar si la reparación fue exitosa
            es_valido, _ = self.verificar_integridad_video(ruta_salida)
            
            if es_valido:
                self.logger.info(f"Reparado exitosamente: {ruta_video.name}")
                self.estadisticas['videos_reparados'] += 1
                return True
            
            # Segundo intento: Recodificar video
            self.logger.info(f"Intentando recodificación completa para: {ruta_video.name}")
            comando = [
                'ffmpeg', '-i', str(ruta_video),
                '-c:v', 'libx264', '-preset', 'medium',
                '-crf', '23', '-c:a', 'aac',
                str(ruta_salida)
            ]
            
            subprocess.run(comando, check=True)
            
            # Verificación final
            es_valido, _ = self.verificar_integridad_video(ruta_salida)
            if es_valido:
                self.logger.info(f"Reparado exitosamente mediante recodificación: {ruta_video.name}")
                self.estadisticas['videos_reparados'] += 1
                return True
            
            self.estadisticas['reparaciones_fallidas'] += 1
            return False
            
        except Exception as e:
            self.logger.error(f"Error al reparar {ruta_video}: {str(e)}")
            self.estadisticas['reparaciones_fallidas'] += 1
            return False

    def procesar_videos(self, max_workers=4):
        """Procesa todos los videos en el directorio de entrada."""
        archivos_video = list(self.directorio_entrada.glob("**/*.[mM][pP]4"))
        self.estadisticas['total_videos'] = len(archivos_video)
        
        self.logger.info(f"Iniciando verificación de integridad para {len(archivos_video)} videos")
        videos_corruptos = []
        
        # Verificar integridad de todos los videos
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for ruta_video in archivos_video:
                futures.append(
                    executor.submit(self.verificar_integridad_video, ruta_video)
                )
            
            for ruta_video, future in tqdm(zip(archivos_video, futures), 
                                         total=len(archivos_video),
                                         desc="Verificando integridad de videos"):
                es_valido, errores = future.result()
                if not es_valido:
                    videos_corruptos.append((ruta_video, errores))
                    self.estadisticas['videos_corruptos'] += 1
        
        # Procesar videos corruptos
        if videos_corruptos:
            self.logger.info(f"\nSe encontraron {len(videos_corruptos)} videos corruptos")
            self.logger.info("Iniciando proceso de reparación...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for ruta_video, _ in videos_corruptos:
                    futures.append(
                        executor.submit(self.reparar_video, ruta_video)
                    )
                
                list(tqdm(
                    futures,
                    total=len(videos_corruptos),
                    desc="Reparando videos"
                ))
        
        # Imprimir estadísticas finales
        self.imprimir_estadisticas()

    def imprimir_estadisticas(self):
        """Imprime las estadísticas del procesamiento."""
        self.logger.info("\n" + "="*50)
        self.logger.info("ESTADÍSTICAS DE PROCESAMIENTO DE VIDEOS")
        self.logger.info("="*50)
        self.logger.info(f"Total de videos procesados: {self.estadisticas['total_videos']}")
        self.logger.info(f"Videos corruptos encontrados: {self.estadisticas['videos_corruptos']}")
        self.logger.info(f"Videos reparados exitosamente: {self.estadisticas['videos_reparados']}")
        self.logger.info(f"Reparaciones fallidas: {self.estadisticas['reparaciones_fallidas']}")
        self.logger.info("="*50)

def main():
    # Configurar rutas
    directorio_entrada = r"C:\GONZALES\dataset_violencia\video_aumentation\violence"
    directorio_salida = r"C:\GONZALES\dataset_violencia\video_aumentation\procesados"
    
    # Crear y ejecutar el verificador
    verificador = VerificadorIntegridadVideo(
        directorio_entrada=directorio_entrada,
        directorio_salida=directorio_salida,
        archivo_log="integridad_video.log"
    )
    
    verificador.procesar_videos(max_workers=4)

if __name__ == "__main__":
    main()