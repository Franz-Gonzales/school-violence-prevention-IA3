import os
import shutil
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

class LabelManager:
    def __init__(self, images_dir, labels_dir, backup_dir):
        """
        Inicializa el gestor de etiquetas.
        
        Args:
            images_dir (str): Directorio de imágenes
            labels_dir (str): Directorio de etiquetas (.txt)
            backup_dir (str): Directorio para archivos huérfanos
        """
        self.images_dir = Path(images_dir)
        self.labels_dir = Path(labels_dir)
        self.backup_dir = Path(backup_dir)
        
        # Crear directorio de respaldo si no existe
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Estadísticas
        self.stats = {
            'total_labels': 0,
            'moved_files': 0,
            'remaining_labels': 0
        }

    def get_image_names(self):
        """Obtiene conjunto de nombres de imágenes sin extensión."""
        image_names = set()
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        
        for file in self.images_dir.iterdir():
            if file.is_file() and file.suffix.lower() in valid_extensions:
                image_names.add(file.stem)
        
        return image_names

    def process_labels(self):
        """Procesa los archivos de etiquetas y mueve los huérfanos."""
        image_names = self.get_image_names()
        label_files = list(self.labels_dir.glob('*.txt'))
        self.stats['total_labels'] = len(label_files)
        
        print(f"\n{'='*60}")
        print(f"Procesando {self.stats['total_labels']} archivos de etiquetas...")
        print(f"{'='*60}")
        
        # Crear subcarpeta con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_subdir = self.backup_dir / f"labels_huerfanos_{timestamp}"
        backup_subdir.mkdir(exist_ok=True)
        
        # Procesar archivos con barra de progreso
        for label_file in tqdm(label_files, desc="Verificando etiquetas"):
            if label_file.stem not in image_names:
                try:
                    # Mover archivo a directorio de respaldo
                    shutil.move(str(label_file), str(backup_subdir / label_file.name))
                    self.stats['moved_files'] += 1
                except Exception as e:
                    print(f"\nError al mover {label_file.name}: {str(e)}")
        
        # Actualizar estadísticas
        self.stats['remaining_labels'] = len(list(self.labels_dir.glob('*.txt')))
        
        # Mostrar resumen
        self.print_summary(backup_subdir)

    def print_summary(self, backup_subdir):
        """Imprime resumen del proceso."""
        print(f"\n{'='*60}")
        print("RESUMEN DEL PROCESO")
        print(f"{'='*60}")
        print(f"Total de archivos .txt procesados: {self.stats['total_labels']}")
        print(f"Archivos movidos a respaldo: {self.stats['moved_files']}")
        print(f"Archivos .txt restantes: {self.stats['remaining_labels']}")
        print(f"\nDirectorio de respaldo: {backup_subdir}")
        print(f"{'='*60}")

def main():
    # Configurar rutas
    images_dir = r"C:\Users\franz\Downloads\dataset_people_augmented\images\test"
    labels_dir = r"C:\Users\franz\Downloads\dataset_people_augmented\labels\test"
    backup_dir = r"C:\GONZALES\dataset_violencia\images_aumentation\images_sobra\labels"
    
    try:
        # Crear y ejecutar el gestor de etiquetas
        manager = LabelManager(images_dir, labels_dir, backup_dir)
        manager.process_labels()
        
    except Exception as e:
        print(f"\nError durante la ejecución: {str(e)}")
        raise

if __name__ == "__main__":
    main()