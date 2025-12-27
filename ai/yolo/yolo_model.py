# GameMediaTool/ai/yolo/yolo_model.py

from ultralytics import YOLO
from tools.logger import get_logger
from pathlib import Path
import cv2
import json

logger = get_logger("YOLOModel")

# ⚠️ المسار النهائي لملف الأوزان: ai/models/best.pt
YOLO_WEIGHTS_PATH = "ai/models/best.pt" 

class YOLOModel:
    def __init__(self, model_path):
        """
        Initializes and loads the YOLO model from the given path.
        """
        try:
            # التحقق من وجود ملف الأوزان قبل التحميل
            if not Path(model_path).exists():
                 # [التعديل هنا] يمكن أن نبدأ من نموذج مُدرب مسبقًا
                logger.warning(f"YOLO weights not found at {model_path}. Initializing with 'yolov8n.pt' and will save the best model to this path after training.")
                self.model = YOLO('yolov8n.pt') # نموذج نانو مُدرب مسبقاً للبدء منه
            else:
                self.model = YOLO(model_path)
                
            self.class_names = list(self.model.names.values())
            logger.info(f"YOLO model loaded from {model_path} with {len(self.class_names)} classes.")
            logger.debug(f"Available YOLO classes: {self.class_names}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model from {model_path}: {e}", exc_info=True)
            self.model = None
            self.class_names = []

    def predict(self, image):
        # ... (باقي كود دالة predict بدون تغيير) ...
        if self.model is None:
            logger.error("YOLO model is not loaded, cannot perform prediction.")
            return None
            
        try:
            # هنا نفترض أن image هو NumPy array بترميز RGB
            return self.model(image, verbose=False)
        except Exception as e:
            logger.error(f"An error occurred during YOLO prediction: {e}", exc_info=True)
            return None

    @staticmethod
    def train(data_path: str, model_save_path: str):
        """
        Starts the YOLO model training process.
        
        Args:
            data_path (str): المسار إلى ملف data.yaml الخاص بتدريب YOLO.
            model_save_path (str): مسار حفظ الأوزان النهائية (مثل ai/models/best.pt).
        """
        logger.info(f"Starting YOLO training using configuration from: {data_path}")
        try:
            # يبدأ التدريب من أوزان سابقة أو من yolov8n إذا لم تُحدد أوزان بدء
            model = YOLO('yolov8n.pt')
            
            # [التعديل هنا] نستخدم دالة train الخاصة بمكتبة ultralytics
            # name='temp_yolo_run' لضمان عدم إنشاء مجلدات log غير ضرورية، ونستخدم save=True
            results = model.train(
                data=data_path, 
                epochs=50, 
                imgsz=640, 
                save=True, 
                project=Path(model_save_path).parent,
                name='temp_yolo_run',
                exist_ok=True # لتجنب الأخطاء إذا كان المجلد موجوداً
            )
            
            # يتم حفظ أفضل نموذج تلقائياً كـ 'best.pt' في مجلد 'runs/detect/temp_yolo_run'
            # نحتاج إلى نقل أو إعادة تسمية الملف 'best.pt' إلى المسار النهائي المطلوب: model_save_path
            
            final_best_path = Path(model_save_path).parent / 'temp_yolo_run' / 'weights' / 'best.pt'
            
            if final_best_path.exists():
                # إعادة تسمية ونقل الملف إلى مسار الحفظ المطلوب
                final_best_path.rename(model_save_path)
                logger.info(f"YOLO best model saved successfully to: {model_save_path}")
            else:
                logger.error(f"YOLO 'best.pt' was not found after training in the expected run directory.")

            return True

        except Exception as e:
            logger.error(f"YOLO training failed: {e}", exc_info=True)
            return False