# GameMediaTool/utils/labels_generator.py
import os
from tools.logger import get_logger

logger = get_logger("Labels Generator")

def generate_labels(frames_info: dict) -> dict:
    """
    Analyzes frame information from AI detection and generates final labels.
    
    Args:
        frames_info (dict): A dictionary where keys are frame paths and values are 
                            lists of AI detections (label, confidence, etc.).

    Returns:
        dict: A dictionary of final labels for each frame.
    """
    logger.info("Starting automatic labeling...")
    
    final_labels = {}
    for frame_path, detections in frames_info.items():
        labels = set()
        for det in detections:
            # Simple rule-based labeling for demonstration
            if "fullbody" in det["label"]:
                labels.add("fullbody")
            elif "boobs" in det["label"]:
                labels.add("boobs")
            elif "ass" in det["label"]:
                labels.add("ass")
            elif "pussy" in det["label"]:
                labels.add("pussy")
            
            # Additional labels based on clothing
            if "topless" in det["label"] or "bare" in det["label"]:
                labels.add("topless")
            if "bottomless" in det["label"]:
                labels.add("bottomless")

        final_labels[frame_path] = list(labels)
    
    logger.info("Automatic labeling completed.")
    return final_labels