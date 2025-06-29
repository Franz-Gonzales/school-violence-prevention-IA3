import os

def validate_dataset(images_dir, labels_dir):
    # Obtener lista de nombres de imágenes (sin extensión)
    image_files = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
    image_names = {os.path.splitext(f)[0] for f in image_files}

    # Obtener lista de nombres de archivos .txt
    label_files = [f for f in os.listdir(labels_dir) if f.endswith('.txt') and os.path.isfile(os.path.join(labels_dir, f))]
    label_names = {os.path.splitext(f)[0] for f in label_files}

    # Verificar imágenes sin etiquetas
    missing_labels = image_names - label_names
    if missing_labels:
        print(f"\n--- Alerta: {len(missing_labels)} imágenes sin archivos .txt correspondientes ---")
        for name in sorted(missing_labels):
            print(f"Imagen sin etiqueta: {name}")
    else:
        print("\nTodas las imágenes tienen etiquetas correspondientes.")

    # Verificar etiquetas vacías
    empty_labels = []
    for label_file in label_files:
        label_path = os.path.join(labels_dir, label_file)
        with open(label_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                empty_labels.append(label_file)
    
    if empty_labels:
        print(f"\n--- Alerta: {len(empty_labels)} archivos .txt vacíos detectados ---")
        for label in sorted(empty_labels):
            print(f"Etiqueta vacía: {label}")
    else:
        print("\nTodos los archivos .txt contienen datos.")

    # Resumen final
    print("\n--- Resumen de la validación del dataset ---")
    print(f"Total de imágenes: {len(image_names)}")
    print(f"Total de etiquetas: {len(label_names)}")
    print(f"Imágenes sin etiquetas: {len(missing_labels)}")
    print(f"Etiquetas vacías: {len(empty_labels)}")

    if not missing_labels and not empty_labels:
        print("\n¡Validación completada con éxito! Todo está en orden.")
    else:
        print("\n¡Validación completada con advertencias! Revisa los problemas reportados.")

# Rutas de las carpetas (modifica estas variables según tus necesidades)
images_dir = r"C:\Users\franz\Downloads\dataset_people_augmented\images\val"  # Carpeta con las imágenes
labels_dir = r"C:\Users\franz\Downloads\dataset_people_augmented\labels\val"    # Carpeta con los archivos .txt de anotaciones

# Ejecutar la validación
validate_dataset(images_dir, labels_dir)