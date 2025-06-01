import cv2
import sys

def test_gstreamer_support():
    """Verifica si OpenCV fue compilado con soporte GStreamer"""
    build_info = cv2.getBuildInformation()
    if 'GStreamer' in build_info and 'YES' in build_info.split('GStreamer')[1].split('\n')[0]:
        print("✓ GStreamer está habilitado en OpenCV")
        return True
    else:
        print("✗ GStreamer NO está habilitado en OpenCV")
        return False

def open_camera_gstreamer(camera_id=0, width=640, height=480, fps=30):
    """
    Abre la cámara usando GStreamer pipeline
    
    Args:
        camera_id: ID de la cámara (0 para cámara por defecto)
        width: Ancho del video
        height: Alto del video
        fps: Frames por segundo
    """
    
    # Pipeline GStreamer para Windows
    # Usa ksvideosrc para cámaras DirectShow en Windows
    gstreamer_pipeline = (
        f"ksvideosrc device-index={camera_id} ! "
        f"video/x-raw,format=YUY2,width={width},height={height},framerate={fps}/1 ! "
        f"videoconvert ! "
        f"video/x-raw,format=BGR ! "
        f"appsink drop=1"
    )
    
    print(f"Pipeline GStreamer: {gstreamer_pipeline}")
    
    # Crear captura de video con GStreamer
    cap = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)
    
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara con GStreamer")
        return None
    
    print("✓ Cámara abierta exitosamente con GStreamer")
    return cap

def open_camera_directshow(camera_id=0, width=640, height=480, fps=30):
    """
    Alternativa usando DirectShow (fallback)
    """
    cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        print("✓ Cámara abierta con DirectShow")
        return cap
    else:
        print("Error: No se pudo abrir la cámara con DirectShow")
        return None

def main():
    # Verificar soporte GStreamer
    if not test_gstreamer_support():
        print("Advertencia: Continuando sin verificar GStreamer...")
    
    # Configuración de la cámara
    CAMERA_ID = 0
    WIDTH = 640
    HEIGHT = 480
    FPS = 30
    
    # Intentar abrir cámara con GStreamer
    cap = open_camera_gstreamer(CAMERA_ID, WIDTH, HEIGHT, FPS)
    
    # Si falla, usar DirectShow como alternativa
    if cap is None:
        print("Intentando con DirectShow...")
        cap = open_camera_directshow(CAMERA_ID, WIDTH, HEIGHT, FPS)
    
    if cap is None:
        print("Error: No se pudo abrir ninguna cámara")
        sys.exit(1)
    
    # Mostrar información de la cámara
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Resolución: {actual_width}x{actual_height}")
    print(f"FPS: {actual_fps}")
    print("Presiona 'q' para salir")
    
    # Loop principal de captura
    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("Error: No se pudo leer el frame")
                break
            
            # Opcional: mostrar contador de frames
            frame_count += 1
            cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Mostrar el frame
            cv2.imshow('Camara - OpenCV + GStreamer', frame)
            
            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
    
    finally:
        # Limpiar recursos
        cap.release()
        cv2.destroyAllWindows()
        print("Recursos liberados")

if __name__ == "__main__":
    main()