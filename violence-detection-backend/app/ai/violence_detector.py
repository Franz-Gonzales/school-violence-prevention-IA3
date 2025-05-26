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
        self.setup_model()
    
    def setup_model(self):
        try:
            # Configurar ONNX Runtime
            options = ort.SessionOptions()
            options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            options.intra_op_num_threads = 4
            
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] \
                if configuracion.USE_GPU else ['CPUExecutionProvider']
            
            model_path = configuracion.obtener_ruta_modelo(configuracion.TIMESFORMER_MODEL)
            self.model = ort.InferenceSession(
                str(model_path), 
                providers=providers,
                sess_options=options
            )
            
            logger.info("✅ Modelo TimesFormer ONNX cargado exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo ONNX: {str(e)}")
            raise
    
    def agregar_frame(self, frame: np.ndarray):
        self.buffer_frames.append(frame.copy())
        if len(self.buffer_frames) > self.config["num_frames"]:
            self.buffer_frames.pop(0)
    
    def detectar(self) -> Dict[str, Any]:
        if len(self.buffer_frames) < self.config["num_frames"]:
            return {
                'violencia_detectada': False,
                'probabilidad': 0.0,
                'mensaje': f'Buffer incompleto ({len(self.buffer_frames)}/{self.config["num_frames"]} frames)'
            }
        
        try:
            # Preprocesar frames
            input_tensor = self.processor.preprocess_frames(self.buffer_frames)
            
            # Realizar inferencia
            outputs = self.model.run(
                None, 
                {self.model.get_inputs()[0].name: input_tensor}
            )
            
            # Aplicar softmax
            logits = outputs[0][0]
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / exp_logits.sum()
            
            # Obtener predicción
            prob_violencia = float(probs[1])
            es_violencia = prob_violencia >= self.threshold
            
            return {
                'violencia_detectada': es_violencia,
                'probabilidad': prob_violencia,
                'clase': self.config["labels"][1] if es_violencia else self.config["labels"][0],
                'mensaje': 'Violencia detectada' if es_violencia else 'No se detectó violencia'
            }
            
        except Exception as e:
            logger.error(f"Error en detección: {str(e)}")
            return {
                'violencia_detectada': False,
                'probabilidad': 0.0,
                'mensaje': f'Error: {str(e)}'
            }