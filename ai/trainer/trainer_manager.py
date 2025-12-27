# GameMediaTool/ai/trainer/trainer_manager.py

from tools.logger import get_logger
from ai.cnn.cnn_model import train_pytorch_model
# 🚀 التعديل هنا: استورد الثابت مباشرةً مع الكلاس
from ai.yolo.yolo_model import YOLOModel, YOLO_WEIGHTS_PATH 
from pathlib import Path
import os
import shutil
import random
import json
from typing import Dict, List, Any

logger = get_logger("TrainerManager")

# --- CNN Configurations ---
# ⚠️ المجلد الذي يجب على الـ GUI حفظ كل الصور والبيانات الجديدة فيه
CNN_BASE_DATA_DIR = "assets/cnn_data_pool" 
# ملف يجمع مسارات/أسماء الصور وفئاتها (يجب أن يتم إنشاؤه بواسطة الـ GUI)
CNN_POOL_JSON = Path(CNN_BASE_DATA_DIR) / "cnn_pool_data.json"
CNN_TRAINING_DIR = "assets/cnn_training_data"
CNN_MODEL_SAVE_PATH = "ai/models/clothing_classifier.pth"
CNN_CLASS_MAP_PATH = "ai/models/cnn_class_map.json" 

# --- YOLO Configurations ---
# ⚠️ المجلد الذي يجب على الـ GUI حفظ كل الصور والـ labels فيه
YOLO_BASE_DATA_DIR = "assets/yolo_data_pool" 
YOLO_IMAGES_POOL = Path(YOLO_BASE_DATA_DIR) / "images"
YOLO_LABELS_POOL = Path(YOLO_BASE_DATA_DIR) / "labels"
YOLO_TRAINING_DIR = "assets/yolo_training_data"
YOLO_DATA_YAML_PATH = Path(YOLO_TRAINING_DIR) / "data.yaml"
YOLO_MODEL_SAVE_PATH = YOLO_WEIGHTS_PATH


class TrainerManager:
    """تدير عمليات التدريب لجميع نماذج الذكاء الاصطناعي (CNN, YOLO)"""
    def __init__(self, config=None):
        self.config = config if config else {}
        logger.info("TrainerManager initialized.")

    def _split_cnn_data(self, pool_json_path: Path, output_dir: Path, split_ratio: float = 0.8):
        """
        يقسم البيانات من ملف JSON (الذي تم إنشاؤه بواسطة الـ GUI) إلى مجلدات train/val
        بناءً على الفئات.
        """
        if not pool_json_path.is_file():
            logger.error(f"CNN Pool Data JSON not found at: {pool_json_path}. Skipping split.")
            return False
        
        try:
            with open(pool_json_path, 'r') as f:
                data_pool: Dict[str, str] = json.load(f) # {filename: class_name}
        except Exception as e:
            logger.error(f"Failed to read CNN pool JSON: {e}")
            return False

        shutil.rmtree(output_dir, ignore_errors=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        train_dir, val_dir = output_dir / 'train', output_dir / 'val'
        
        # تجميع الملفات حسب الفئة
        classes_data: Dict[str, List[str]] = {}
        for filename, class_name in data_pool.items():
            classes_data.setdefault(class_name, []).append(filename)

        total_images = 0
        for class_name, files in classes_data.items():
            random.shuffle(files)
            split_index = int(len(files) * split_ratio)
            train_files, val_files = files[:split_index], files[split_index:]
            
            (train_dir / class_name).mkdir(parents=True, exist_ok=True)
            (val_dir / class_name).mkdir(parents=True, exist_ok=True)
            
            # نسخ الملفات من المجلد الجذري (نحن نفترض أن الصور الأصلية بجوار ملف الـ JSON)
            source_folder = pool_json_path.parent
            for filename in train_files:
                shutil.copy2(source_folder / filename, train_dir / class_name / filename)
            for filename in val_files:
                shutil.copy2(source_folder / filename, val_dir / class_name / filename)
            
            total_images += len(files)

        logger.info(f"CNN Data Split complete. Total images: {total_images}.")
        return total_images > 0

    def _split_yolo_data(self, image_pool: Path, label_pool: Path, output_dir: Path, split_ratio: float = 0.8):
        """
        يقسم صور YOLO وملفات الـ labels من مجلدات التجميع إلى مجلدات train/val.
        """
        if not image_pool.is_dir() or not label_pool.is_dir():
            logger.error(f"YOLO Pool folders not found: {image_pool} or {label_pool}. Skipping split.")
            return False

        shutil.rmtree(output_dir, ignore_errors=True)
        
        (output_dir / 'images' / 'train').mkdir(parents=True, exist_ok=True)
        (output_dir / 'images' / 'val').mkdir(parents=True, exist_ok=True)
        (output_dir / 'labels' / 'train').mkdir(parents=True, exist_ok=True)
        (output_dir / 'labels' / 'val').mkdir(parents=True, exist_ok=True)

        all_images = [f for f in image_pool.iterdir() if f.suffix in ['.jpg', '.jpeg', '.png', '.webp']]
        random.shuffle(all_images)
        
        split_index = int(len(all_images) * split_ratio)
        train_images = all_images[:split_index]
        val_images = all_images[split_index:]
        
        total_copied = 0
        for img_list, phase in zip([train_images, val_images], ['train', 'val']):
            for img_path in img_list:
                label_path = label_pool / f"{img_path.stem}.txt"
                if label_path.exists():
                    shutil.copy2(img_path, output_dir / 'images' / phase / img_path.name)
                    shutil.copy2(label_path, output_dir / 'labels' / phase / label_path.name)
                    total_copied += 1
                else:
                    logger.warning(f"Missing YOLO label for image: {img_path.name}. Skipping image.")
        
        logger.info(f"YOLO Data Split complete. Total images/labels copied: {total_copied}.")
        return total_copied > 0

    def train_all_models(self):
        """تبدأ عملية تدريب جميع النماذج بعد تقسيم البيانات."""
        logger.info("Starting training process for all models...")
        
        # 1. تقسيم بيانات CNN
        cnn_data_ready = self._split_cnn_data(CNN_POOL_JSON, Path(CNN_TRAINING_DIR))

        if cnn_data_ready:
            try:
                # تدريب نموذج CNN لتصنيف الملابس (التدريب التزايدي)
                logger.info(f"Triggering CNN incremental training with data from '{CNN_TRAINING_DIR}'...")
                train_pytorch_model(
                    data_dir=CNN_TRAINING_DIR, 
                    model_save_path=CNN_MODEL_SAVE_PATH, 
                    map_save_path=CNN_CLASS_MAP_PATH, 
                    num_epochs=15
                )
                logger.info("CNN Training completed. Model is now updated.")
            except Exception as e:
                logger.error(f"An error occurred during CNN training: {e}")

        # 2. تقسيم بيانات YOLO
        yolo_data_ready = self._split_yolo_data(YOLO_IMAGES_POOL, YOLO_LABELS_POOL, Path(YOLO_TRAINING_DIR))

        if yolo_data_ready:
            # 3. تدريب نموذج YOLO للكشف عن الأشياء (Object Detection)
            try:
                data_yaml_path = self.config.get("yolo_data_yaml", YOLO_DATA_YAML_PATH)
                
                if not Path(data_yaml_path).is_file():
                    logger.error(f"YOLO configuration file not found: {data_yaml_path}")
                    logger.info("Skipping YOLO training. Please create the data.yaml file.")
                else:
                    logger.info(f"Triggering YOLO model training using config: {data_yaml_path}")
                    
                    YOLOModel.train(
                        data_path=data_yaml_path, 
                        model_save_path=YOLO_MODEL_SAVE_PATH
                    )
                    logger.info("YOLO Training process finished.")
                
            except Exception as e:
                logger.error(f"An error occurred during YOLO training: {e}")
        
        logger.info("Training process completed.")
        return True