import os
import random
import numpy as np
import cv2
import av
import torch
from torchvision import transforms
from tqdm import tqdm

# Directorios
input_dir = r"C:\GONZALES\dataset_violencia\dataset_violencia\train\violencia_directa"
output_dir = r"C:\GONZALES\dataset_violencia\video_aumentation\violence"
os.makedirs(output_dir, exist_ok=True)

def read_video_av(video_path):
    """Lee un video utilizando PyAV y devuelve una lista de frames en formato numpy."""
    try:
        container = av.open(video_path)
        video_stream = container.streams.video[0]
        
        # Extraer FPS como float
        fps = float(video_stream.average_rate)
        
        frames = []
        for frame in container.decode(video=0):
            # Convertir directamente a numpy array en formato RGB
            img = frame.to_ndarray(format='rgb24')
            frames.append(img)
        
        return frames, fps
    except Exception as e:
        print(f"Error al leer el video {video_path}: {str(e)}")
        return None, None

def save_video(frames, output_path, fps=30.0):
    """Guarda una lista de frames como un video usando OpenCV."""
    if not frames:
        print("No hay frames para guardar")
        return False
    
    try:
        height, width = frames[0].shape[:2]
        
        # Asegurarse que fps sea un float
        fps = float(fps)
        
        # Verificar que fps sea válido
        if fps <= 0 or np.isnan(fps):
            print(f"FPS inválido ({fps}), usando 30.0 por defecto")
            fps = 30.0
            
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not writer.isOpened():
            print(f"No se pudo abrir el escritor de video para {output_path}")
            return False
        
        for frame in frames:
            # Asegurarse de que el frame es BGR (lo que OpenCV necesita)
            if frame.shape[2] == 3:  # Si tiene 3 canales, asumir RGB
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                frame_bgr = frame
                
            # Asegurarse de que sea uint8
            if frame_bgr.dtype != np.uint8:
                frame_bgr = np.clip(frame_bgr, 0, 255).astype(np.uint8)
                
            writer.write(frame_bgr)
        
        writer.release()
        return True
    except Exception as e:
        print(f"Error al guardar el video: {str(e)}")
        return False

def apply_horizontal_flip(frames):
    """Aplica flip horizontal a cada frame."""
    return [cv2.flip(frame, 1) for frame in frames]

def apply_brightness_adjustment(frames, factor=None):
    """Ajusta el brillo de cada frame."""
    if factor is None:
        factor = random.uniform(0.7, 1.3)
    
    adjusted_frames = []
    for frame in frames:
        # Convertir a HSV para manipular el brillo
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        hsv = hsv.astype(np.float32)
        
        # Ajustar el brillo (canal V en HSV)
        hsv[:,:,2] = np.clip(hsv[:,:,2] * factor, 0, 255)
        
        # Convertir de vuelta a RGB
        adjusted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        adjusted_frames.append(adjusted)
    
    return adjusted_frames

def apply_contrast_adjustment(frames, factor=None):
    """Ajusta el contraste de cada frame."""
    if factor is None:
        factor = random.uniform(0.7, 1.3)
    
    adjusted_frames = []
    for frame in frames:
        # Fórmula para ajustar contraste manteniendo el valor medio
        mean = np.mean(frame, axis=(0, 1), keepdims=True)
        adjusted = np.clip((frame - mean) * factor + mean, 0, 255).astype(np.uint8)
        adjusted_frames.append(adjusted)
    
    return adjusted_frames

def apply_rotation(frames, angle=None):
    """Aplica una rotación a cada frame preservando las dimensiones."""
    if angle is None:
        angle = random.uniform(-15, 15)
    
    rotated_frames = []
    for frame in frames:
        h, w = frame.shape[:2]
        center = (w / 2, h / 2)
        
        # Matriz de rotación
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Aplicar rotación
        rotated = cv2.warpAffine(frame, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        rotated_frames.append(rotated)
    
    return rotated_frames

def apply_temporal_reverse(frames):
    """Invierte el orden temporal de los frames."""
    return frames[::-1]

def apply_speed_change(frames, factor=None):
    """Cambia la velocidad del video muestreando frames."""
    if factor is None:
        factor = random.uniform(0.8, 1.2)
    
    n_frames = len(frames)
    
    if factor < 1.0:  # Más lento
        # Interpolar frames para tener más
        indices = np.arange(0, n_frames - 1, factor)
        new_frames = []
        
        for i in range(len(indices)):
            idx = indices[i]
            idx_floor = int(np.floor(idx))
            idx_ceil = int(np.ceil(idx))
            
            if idx_floor == idx_ceil:
                new_frames.append(frames[idx_floor])
            else:
                # Interpolación lineal entre frames
                alpha = idx - idx_floor
                frame = (1 - alpha) * frames[idx_floor] + alpha * frames[idx_ceil]
                new_frames.append(frame.astype(np.uint8))
                
        return new_frames
    else:  # Más rápido
        # Seleccionar menos frames
        step = factor
        indices = np.arange(0, n_frames, step)
        indices = indices.astype(int)
        indices = indices[indices < n_frames]
        
        return [frames[i] for i in indices]

def apply_color_jitter(frames, hue_factor=None, saturation_factor=None):
    """Aplica modificaciones al tono y saturación."""
    if hue_factor is None:
        hue_factor = random.uniform(-0.1, 0.1)  # Pequeños cambios en el tono
    
    if saturation_factor is None:
        saturation_factor = random.uniform(0.7, 1.3)
    
    adjusted_frames = []
    for frame in frames:
        # Convertir a HSV para manipular tono y saturación
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
        
        # Ajustar tono (canal H en HSV)
        hsv[:,:,0] = (hsv[:,:,0] + hue_factor * 180) % 180
        
        # Ajustar saturación (canal S en HSV)
        hsv[:,:,1] = np.clip(hsv[:,:,1] * saturation_factor, 0, 255)
        
        # Convertir de vuelta a RGB
        adjusted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        adjusted_frames.append(adjusted)
    
    return adjusted_frames

def apply_center_crop(frames, crop_factor=None):
    """Aplica un recorte central al video."""
    if crop_factor is None:
        crop_factor = random.uniform(0.8, 0.95)  # Recorta entre el 5% y el 20%
    
    cropped_frames = []
    if frames:
        h, w = frames[0].shape[:2]
        
        # Calcular dimensiones del recorte
        new_h = int(h * crop_factor)
        new_w = int(w * crop_factor)
        
        # Calcular coordenadas del recorte
        start_x = (w - new_w) // 2
        start_y = (h - new_h) // 2
        
        for frame in frames:
            cropped = frame[start_y:start_y+new_h, start_x:start_x+new_w]
            
            # Redimensionar al tamaño original
            cropped = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
            cropped_frames.append(cropped)
    
    return cropped_frames

def apply_augmentation(frames, aug_type):
    """Aplica la augmentación especificada a los frames."""
    if aug_type == "horizontal_flip":
        return apply_horizontal_flip(frames)
    elif aug_type == "brightness":
        return apply_brightness_adjustment(frames)
    elif aug_type == "contrast":
        return apply_contrast_adjustment(frames)
    elif aug_type == "rotation":
        return apply_rotation(frames)
    elif aug_type == "temporal_reverse":
        return apply_temporal_reverse(frames)
    elif aug_type == "speed_change":
        return apply_speed_change(frames)
    elif aug_type == "color_jitter":
        return apply_color_jitter(frames)
    elif aug_type == "center_crop":
        return apply_center_crop(frames)
    else:
        print(f"Tipo de augmentación no reconocido: {aug_type}")
        return frames

def main():
    # Obtener archivos de video
    video_files = [f for f in os.listdir(input_dir) if f.endswith(('.mp4', '.avi'))]
    if not video_files:
        print("¡No se encontraron archivos de video en el directorio de entrada!")
        return
    
    print(f"Se encontraron {len(video_files)} videos para procesar")

    # Tipos de augmentación disponibles
    augmentation_types = [
        "horizontal_flip", 
        # "brightness",
        # "rotation"
        # "contrast",          # comentado
        # "temporal_reverse",  # comentado
        # "speed_change",      # comentado
        # "color_jitter",      # comentado
        # "center_crop"        # comentado
    ]
    
    # Contador para videos procesados con éxito
    videos_procesados = 0
    videos_con_error = 0
    
    # Procesar cada video con cada tipo de augmentación
    total_operaciones = len(video_files) * len(augmentation_types)
    with tqdm(total=total_operaciones) as pbar:
        for video_file in video_files:
            video_path = os.path.join(input_dir, video_file)
            
            # Leer el video una sola vez
            frames, original_fps = read_video_av(video_path)
            if frames is None or not frames:
                print(f"No se pudieron obtener frames de {video_file}, saltando...")
                videos_con_error += 1
                pbar.update(len(augmentation_types))  # Actualizar la barra por todas las augmentaciones que se saltarán
                continue
            
            # Corregir FPS si es necesario
            if original_fps is None or original_fps <= 0 or np.isnan(original_fps):
                print(f"FPS no válidos ({original_fps}) para {video_file}, usando 30.0")
                original_fps = 30.0
            
            # Verificar datos del video
            print(f"Video: {video_file}, Frames: {len(frames)}, FPS: {original_fps}")
            
            # Aplicar cada tipo de augmentación al video
            for aug_type in augmentation_types:
                try:
                    # Aplicar augmentación
                    augmented_frames = apply_augmentation(frames.copy(), aug_type)
                    if not augmented_frames:
                        print(f"La augmentación {aug_type} no produjo frames para {video_file}")
                        pbar.update(1)
                        continue
                    
                    # Crear nombre para el video procesado
                    base_name = os.path.splitext(video_file)[0]
                    output_filename = f"{base_name}_{aug_type}.mp4"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    # Guardar video aumentado
                    success = save_video(augmented_frames, output_path, fps=original_fps)
                    if success:
                        videos_procesados += 1
                        print(f"Video guardado: {output_filename}")
                    else:
                        print(f"No se pudo guardar el video {output_filename}")
                        videos_con_error += 1
                
                except Exception as e:
                    print(f"Error procesando {video_file} con {aug_type}: {str(e)}")
                    videos_con_error += 1
                
                pbar.update(1)

    print(f"\nProceso completado:")
    print(f"- Videos procesados exitosamente: {videos_procesados}")
    print(f"- Videos/operaciones con error: {videos_con_error}")
    print(f"- Total de videos generados: {videos_procesados}")
    print(f"Los videos aumentados se guardaron en: {output_dir}")

if __name__ == "__main__":
    main()