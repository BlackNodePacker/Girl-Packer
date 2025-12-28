# GameMediaTool/ai/pipeline.py (Corrected with json import and logic)

import os
import sys
import json
from typing import Dict, Any

import cv2
import numpy as np
import torch
from torchvision import transforms

from .yolo.yolo_model import YOLOModel
from .cnn.cnn_model import create_pytorch_model
from tools.logger import get_logger

logger = get_logger("AIPipeline")

# Define model paths
def get_model_base():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'ai', 'models')
    else:
        return os.path.join(os.path.dirname(__file__), 'models')

model_base = get_model_base()
YOLO_MODEL_PATH = os.path.join(model_base, "best.pt")
ASSET_MODEL_PATH = os.path.join(model_base, "asset_classifier.pth")
ASSET_CLASS_MAP_PATH = os.path.join(model_base, "asset_class_map.json")
ACTION_MODEL_PATH = os.path.join(model_base, "action_classifier.pth")
ACTION_CLASS_MAP_PATH = os.path.join(model_base, "action_class_map.json")


class Pipeline:
    def __init__(self, tag_manager):
        self.tag_manager = tag_manager
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Pipeline initialized. Using device: {self.device}")

        # Load all models
        self.yolo_model = self._load_yolo_model(YOLO_MODEL_PATH)
        self.asset_classifier, self.asset_class_map = self._load_cnn_model(
            ASSET_MODEL_PATH, ASSET_CLASS_MAP_PATH, "Asset Classifier"
        )
        self.action_classifier, self.action_class_map = self._load_cnn_model(
            ACTION_MODEL_PATH, ACTION_CLASS_MAP_PATH, "Action Classifier"
        )

        self.transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Resize((224, 224), antialias=True),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    def _load_yolo_model(self, path):
        logger.info(f"Loading YOLO model from {path}...")
        yolo_wrapper = YOLOModel(path)
        if yolo_wrapper.model:
            return yolo_wrapper
        else:
            logger.error("YOLO model loading failed. Predictions will be disabled.")
            return None

    def _load_cnn_model(self, model_path, class_map_path, model_name):
        try:
            logger.info(f"Loading {model_name} class map from {class_map_path}...")
            with open(class_map_path, "r") as f:
                # [THE FIX] Swap the key and value to match the JSON format {class_name: index}
                # and create a dictionary of {index: class_name}
                json_data = json.load(f)
                class_map = {int(v): k for k, v in json_data.items()}

            num_classes = len(class_map)
            logger.info(f"Loading {model_name} model for {num_classes} classes...")
            model = create_pytorch_model(num_classes)
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            model.to(self.device)
            model.eval()
            logger.info(f"{model_name} model loaded successfully.")
            return model, class_map
        except Exception as e:
            logger.error(f"Failed to load {model_name} model from {model_path}: {e}", exc_info=True)
            return None, None

    def classify_asset(self, image: np.ndarray) -> str:
        if self.asset_classifier is None:
            logger.warning("Asset classifier not loaded")
            return "unknown_asset"

        logger.debug("Classifying asset")
        with torch.no_grad():
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            tensor = self.transform(image_rgb).unsqueeze(0).to(self.device)
            outputs = self.asset_classifier(tensor)
            _, predicted = torch.max(outputs, 1)
            class_idx = predicted.item()
            tag = self.asset_class_map.get(class_idx, "unknown_asset")
            logger.debug(f"Asset classified as: {tag}")
            return tag

    def suggest_action(self, image: np.ndarray) -> str:
        if self.action_classifier is None:
            logger.warning("Action classifier not loaded")
            return "unknown_action"

        logger.debug("Suggesting action")
        with torch.no_grad():
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            tensor = self.transform(image_rgb).unsqueeze(0).to(self.device)
            outputs = self.action_classifier(tensor)
            _, predicted = torch.max(outputs, 1)
            class_idx = predicted.item()
            tag = self.action_class_map.get(class_idx, "unknown_action")
            logger.debug(f"Action suggested: {tag}")
            return tag
