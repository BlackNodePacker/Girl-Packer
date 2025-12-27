# GameMediaTool/tools/cropper.py

import cv2
import os
from utils.file_ops import ensure_folder
from .logger import get_logger
from pathlib import Path

logger = get_logger("Cropper")


def crop_and_resize(image_path: str, person_bbox: tuple, crop_target: str, config: dict):
    """
    Crops a specific part from an image based on a person's bounding box and a target,
    then resizes it and returns the image data as a NumPy array.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not read image {image_path}")
            return None

        target_sizes = config.get("image", {}).get("target_sizes", {})
        target_size = target_sizes.get(crop_target)

        px1, py1, px2, py2 = person_bbox
        p_width = px2 - px1
        p_height = py2 - py1

        # Improved proportional cropping logic based on human anatomy
        if crop_target == "fullbody":
            crop_box = person_bbox
        elif crop_target == "face":
            # Top 25% of the height, centered horizontally
            crop_box = (
                px1 + int(p_width * 0.15),
                py1,
                px2 - int(p_width * 0.15),
                py1 + int(p_height * 0.3),
            )
        elif crop_target == "boobs":
            # Upper torso
            crop_box = (px1, py1 + int(p_height * 0.2), px2, py1 + int(p_height * 0.5))
        elif crop_target == "ass":
            # Lower torso, from the back
            crop_box = (px1, py1 + int(p_height * 0.4), px2, py1 + int(p_height * 0.75))
        elif crop_target == "pussy":
            # Lower frontal torso, centered
            crop_box = (
                px1 + int(p_width * 0.25),
                py1 + int(p_height * 0.5),
                px2 - int(p_width * 0.25),
                py1 + int(p_height * 0.8),
            )
        elif crop_target == "legs":
            # Bottom half of the person
            crop_box = (px1, py1 + int(p_height * 0.5), px2, py2)
        else:
            # Default for unknown targets or general clothing
            crop_box = person_bbox

        x1, y1, x2, y2 = [max(0, int(val)) for val in crop_box]

        if x1 >= x2 or y1 >= y2:
            logger.warning(
                f"Invalid crop box calculated for {crop_target} in {image_path}. Skipping."
            )
            return None

        cropped_img = img[y1:y2, x1:x2]

        if cropped_img.size == 0:
            logger.warning(f"Resulting crop for {crop_target} in {image_path} is empty. Skipping.")
            return None

        if target_size:
            resized_img = cv2.resize(
                cropped_img, tuple(target_size), interpolation=cv2.INTER_LANCZOS4
            )
        else:
            resized_img = cropped_img

        return resized_img

    except Exception as e:
        logger.error(f"Error during crop and resize for {image_path}: {e}")
        return None
