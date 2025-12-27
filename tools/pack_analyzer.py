# GameMediaTool/tools/pack_analyzer.py

import os
import json
from PIL import Image # Use Pillow to get image dimensions instead of renpy
from .logger import get_logger

logger = get_logger("PackAnalyzer")

class PackAnalyzer:
    def __init__(self, pack_root_path):
        self.pack_root = pack_root_path
        self.char_name = os.path.basename(pack_root_path)
        self.rating = 0.0
        self.positives = []
        self.warnings = []
        self.errors = []
        self.report = {}

    def analyze(self):
        logger.info(f"Analyzing pack: {self.char_name}")
        
        # This is where the logic from GirlRating would go.
        # We'll build a simplified version for now.

        self._analyze_folder_structure()
        self._analyze_vids()
        self._analyze_fullbody()
        
        # Return a summary
        self.report = {
            "rating": round(self.rating, 2),
            "positives": self.positives,
            "warnings": self.warnings,
            "errors": self.errors
        }
        return self.report

    def _analyze_folder_structure(self):
        required_folders = ["vids", "body_images", "fullbody"]
        for folder in required_folders:
            if os.path.isdir(os.path.join(self.pack_root, folder)):
                self.rating += 5
                self.positives.append(f"Contains '{folder}' directory.")
            else:
                self.rating -= 10
                self.errors.append(f"Missing required directory: '{folder}'.")

    def _analyze_vids(self):
        vids_dir = os.path.join(self.pack_root, "vids")
        if not os.path.isdir(vids_dir): return
        
        videos = [f for f in os.listdir(vids_dir) if f.lower().endswith('.webm')]
        if len(videos) > 10:
            self.rating += 20
            self.positives.append(f"Good video variety ({len(videos)} clips).")
        elif len(videos) > 0:
            self.rating += 10
            self.positives.append(f"Has {len(videos)} video clips.")
        else:
            self.rating -= 5
            self.warnings.append("No .webm videos found in 'vids' folder.")

    def _analyze_fullbody(self):
        fullbody_dir = os.path.join(self.pack_root, "fullbody")
        if not os.path.isdir(fullbody_dir): return

        images = [f for f in os.listdir(fullbody_dir) if f.lower().endswith(('.png', '.webp'))]
        if len(images) > 5:
            self.rating += 15
            self.positives.append(f"Good variety of fullbody images ({len(images)}).")
        elif len(images) > 0:
            self.rating += 5
            self.positives.append("Has fullbody images.")
        else:
            self.warnings.append("No images found in 'fullbody' folder.")

        # Example of checking image dimensions using Pillow
        for img_name in images:
            try:
                with Image.open(os.path.join(fullbody_dir, img_name)) as img:
                    width, height = img.size
                    if height < 1000:
                        self.warnings.append(f"Low resolution fullbody image: {img_name} ({height}p).")
            except Exception as e:
                self.errors.append(f"Could not read image file: {img_name}. Error: {e}")