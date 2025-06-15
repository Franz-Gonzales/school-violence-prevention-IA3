import onnxruntime as ort
import numpy as np
from typing import Dict, Any
from app.config import configuracion
from app.ai.timesformer_processor import TimesFormerProcessor
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)

class DetectorViolencia:
    def __init__(self):
        self.processor = TimesFormerProcessor()
        self.config = configuracion.TIMESFORMER_CONFIG
        self.threshold = configuracion.VIOLENCE_THRESHOLD
        self.buffer_frames = []
        self.violencia_detectada = False
        self.probabilidad_violencia = 0.0
        self.setup_model()
    
    def setup_model(self):
        try:
            # Configurar ONNX Runtime
            options = ort.SessionOptions()
            options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            options.intra_op_num_threads = 4
            
            # Forzar FP16
            options.add_session_config_entry('session.gpu.fp16_enable', '1')
            
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] \
                if configuracion.USE_GPU else ['CPUExecutionProvider']
            
            model_path = configuracion.obtener_ruta_modelo(configuracion.TIMESFORMER_MODEL)
            self.model = ort.InferenceSession(
                str(model_path), 
                providers=providers,
                sess_options=options
            )
            
            print("✅ Modelo TimesFormer ONNX (FP16) cargado exitosamente")
            
        except Exception as e:
            print(f"❌ Error cargando modelo ONNX: {str(e)}")
            raise
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Aplica softmax a un array de logits"""
        e_x = np.exp(x - np.max(x))  # Resta el máximo para estabilidad numérica
        return e_x / e_x.sum()
    
    def agregar_frame(self, frame: np.ndarray):
        """Agrega un frame al buffer circular"""
        self.buffer_frames.append(frame.copy())
        if len(self.buffer_frames) > self.config["num_frames"]:
            self.buffer_frames.pop(0)
    
    def detectar(self) -> Dict[str, Any]:
        """Realiza la detección de violencia en los frames del buffer - CORREGIDO"""
        try:
            if len(self.buffer_frames) < self.config["num_frames"]:
                print(f"Buffer incompleto: {len(self.buffer_frames)}/{self.config['num_frames']} frames")
                return {
                    'violencia_detectada': False,
                    'probabilidad': 0.0,
                    'mensaje': f'Buffer incompleto ({len(self.buffer_frames)}/{self.config["num_frames"]} frames)'
                }
            
            print(f"Procesando {len(self.buffer_frames)} frames para detección")
            
            # Preprocesar frames en FP16
            input_tensor = self.processor.preprocess_frames(self.buffer_frames)
            if input_tensor is None:
                print("Error: input_tensor es None")
                return {'violencia_detectada': False, 'probabilidad': 0.0}
            
            print(f"Shape del tensor de entrada: {input_tensor.shape}")
            
            # Realizar inferencia
            outputs = self.model.run(
                None, 
                {self.model.get_inputs()[0].name: input_tensor}
            )
            
            # Calcular probabilidades
            logits = outputs[0][0].astype(np.float32)
            probs = self._softmax(logits)
            
            # Obtener predicción
            prob_violencia = float(probs[1])
            es_violencia = prob_violencia >= self.threshold
            
            print(f"Probabilidad de violencia: {prob_violencia:.3f}")
            if es_violencia:
                print("¡ALERTA! Violencia detectada")
            
            self.violencia_detectada = es_violencia
            self.probabilidad_violencia = prob_violencia
            
            # *** NUEVA INFORMACIÓN: Marcar todos los frames analizados ***
            resultado = {
                'violencia_detectada': es_violencia,
                'probabilidad': prob_violencia,
                'probabilidad_violencia': prob_violencia,  # Campo adicional para consistencia
                'clase': self.config["labels"][1] if es_violencia else self.config["labels"][0],
                'mensaje': 'ALERTA: Violencia detectada' if es_violencia else 'No se detectó violencia',
                'frames_analizados': len(self.buffer_frames),  # *** NUEVO ***
                'frames_en_secuencia': self.buffer_frames.copy() if es_violencia else [],  # *** NUEVO ***
                'batch_completo': True  # *** NUEVO ***
            }
            
            return resultado
                
        except Exception as e:
            print(f"Error en detección de violencia: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {
                'violencia_detectada': False,
                'probabilidad': 0.0,
                'mensaje': f'Error: {str(e)}',
                'frames_analizados': 0,
                'frames_en_secuencia': [],
                'batch_completo': False
            }
    
    def reiniciar(self):
        """Reinicia el estado del detector"""
        self.buffer_frames.clear()
        self.violencia_detectada = False
        self.probabilidad_violencia = 0.0
        logger.info("Detector de violencia reiniciado")
        print("Detector de violencia reiniciado")