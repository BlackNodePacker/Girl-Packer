import cv2
import json
from pathlib import Path
from tools.logger import get_logger

logger = get_logger("YOLO Utils")


def detect_objects(image_path, model, conf_threshold=0.25):
    if model is None:
        logger.error("YOLO model not provided to detect_objects function.")
        return []

    detections = []
    try:
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not read image file: {image_path}")
            return []

        # [CRUCIAL FIX] Convert the image from BGR (OpenCV's default) to RGB
        # (YOLO model typically expects RGB for correct color interpretation)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        results = model.predict(image_rgb)

        if results is None:
            return []

        for result in results:
            boxes = result.boxes
            for box in boxes:
                confidence = float(box.conf)
                if confidence > conf_threshold:
                    class_id = int(box.cls)
                    label = model.class_names[class_id]
                    # box.xyxy[0] يعطي الإحداثيات مباشرة بالبكسل (x1, y1, x2, y2)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    detections.append(
                        {"bbox": (x1, y1, x2, y2), "label": label, "confidence": confidence}
                    )

    except Exception as e:
        logger.error(f"Error during YOLO detection: {e}", exc_info=True)

    return detections


def get_class_names(model):
    """Returns class names from the YOLO model."""
    if model and hasattr(model, "names"):
        return list(model.names.values())
    return []
