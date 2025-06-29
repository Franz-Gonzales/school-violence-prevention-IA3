import os

def clean_labels(images_dir, labels_dir):
    # Obtener lista de nombres de imágenes (sin extensión)
    image_names = set()
    for filename in os.listdir(images_dir):
        if os.path.isfile(os.path.join(images_dir, filename)):
            name, ext = os.path.splitext(filename)
            image_names.add(name)

    # Eliminar archivos .txt que no tienen imagen correspondiente
    deleted_count = 0
    for filename in os.listdir(labels_dir):
        file_path = os.path.join(labels_dir, filename)
        if os.path.isfile(file_path):
            name, ext = os.path.splitext(filename)
            if ext.lower() == '.txt' and name not in image_names:
                os.remove(file_path)
                deleted_count += 1
                print(f"Eliminado: {filename}")

    # Resultado final
    print(f"\nTotal de archivos .txt eliminados: {deleted_count}")
    remaining_labels = len([f for f in os.listdir(labels_dir) if f.endswith('.txt')])
    print(f"Total de archivos .txt restantes: {remaining_labels}")

# Rutas de las carpetas (modifica estas variables según tus necesidades)
images_dir = r"C:\GONZALES\dataset_violencia\dataset_detection_person\images\train"  # Carpeta con las imágenes limpias
labels_dir = r"C:\GONZALES\dataset_violencia\dataset_detection_person\labels\train"    # Carpeta con los archivos .txt de anotaciones

# Ejecutar la limpieza
clean_labels(images_dir, labels_dir)