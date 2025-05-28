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
        """Realiza la detección de violencia en los frames del buffer"""
        if len(self.buffer_frames) < self.config["num_frames"]:
            return {
                'violencia_detectada': False,
                'probabilidad': 0.0,
                'mensaje': f'Buffer incompleto ({len(self.buffer_frames)}/{self.config["num_frames"]} frames)'
            }
        
        try:
            # Preprocesar frames en FP16
            input_tensor = self.processor.preprocess_frames(self.buffer_frames)
            input_tensor = input_tensor.astype(np.float16)
            
            # Realizar inferencia
            outputs = self.model.run(
                None, 
                {self.model.get_inputs()[0].name: input_tensor}
            )
            
            # Calcular probabilidades
            logits = outputs[0][0].astype(np.float32)
            probs = self._softmax(logits)  # Usando el método _softmax definido
            
            # Obtener predicción
            prob_violencia = float(probs[1])
            es_violencia = prob_violencia >= self.threshold
            
            self.violencia_detectada = es_violencia
            self.probabilidad_violencia = prob_violencia
            
            return {
                'violencia_detectada': es_violencia,
                'probabilidad': prob_violencia,
                'clase': self.config["labels"][1] if es_violencia else self.config["labels"][0],
                'mensaje': 'ALERTA: Violencia detectada' if es_violencia else 'No se detectó violencia',
                'personas_involucradas': 0  # Se actualizará desde el pipeline con el conteo real
            }
            
        except Exception as e:
            print(f"Error en detección: {str(e)}")
            return {
                'violencia_detectada': False,
                'probabilidad': 0.0,
                'mensaje': f'Error: {str(e)}'
            }
    
    def reiniciar(self):
        """Reinicia el estado del detector"""
        self.buffer_frames.clear()
        self.violencia_detectada = False
        self.probabilidad_violencia = 0.0
        logger.info("Detector de violencia reiniciado")
        print("Detector de violencia reiniciado")