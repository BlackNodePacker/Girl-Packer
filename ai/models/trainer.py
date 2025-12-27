"""
ملف تدريب النماذج على البيانات المصنفة.
"""

from pathlib import Path
from tools.logger import logger


class Trainer:
    def __init__(self, yolo_model, cnn_model):
        self.yolo = yolo_model
        self.cnn = cnn_model

    def train(self, labeled_dir: Path):
        logger.info(f"Training models with data in {labeled_dir}")

    def predict(self, frames_dir: Path, crops_dir: Path):
        logger.info(f"Predicting frames in {frames_dir} and saving crops to {crops_dir}")
        for frame_path in frames_dir.glob("*.jpg"):
            yolo_results = self.yolo.detect(frame_path)
            cnn_results = self.cnn.classify(frame_path)
            # حفظ النتائج أو التعامل معها لاحقًا
