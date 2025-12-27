# GameMediaTool/workflows/shoot_maker_workflow.py (Corrected with attribute fix)

import os
import cv2
from PySide6.QtCore import QObject, Signal, QThread

from tools.logger import get_logger
from ai.yolo.yolo_utils import detect_objects

logger = get_logger("ShootMakerWorkflow")


class AIAnalysisWorker(QObject):
    finished = Signal(dict)

    def __init__(self, media_paths, pipeline):
        super().__init__()
        self.media_paths = media_paths
        self.pipeline = pipeline
        # [THE FIX] Use the correct new getter 'get_shoots_tags'
        self.shoots_tags = self.pipeline.tag_manager.get_shoots_tags()

    def run(self):
        if not self.media_paths:
            self.finished.emit({})
            return

        highest_person_count = 0
        location_counts = {}

        sample_paths = self.media_paths[:3]

        for path in sample_paths:
            frame = None
            if path.lower().endswith((".mp4", ".avi", ".mkv", ".webm")):
                cap = cv2.VideoCapture(path)
                success, frame = cap.read()
                cap.release()
            elif path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                frame = cv2.imread(path)

            if frame is not None:
                detections = detect_objects(path, self.pipeline.yolo_model)

                person_count = sum(1 for d in detections if d["label"] == "person")
                if person_count > highest_person_count:
                    highest_person_count = person_count

                # [MODIFIED] Use the corrected self.shoots_tags variable
                if self.shoots_tags:
                    for det in detections:
                        if det["label"] in self.shoots_tags.get("location_tags", {}).values():
                            location_counts[det["label"]] = location_counts.get(det["label"], 0) + 1

        participant_map = {0: "Solo", 1: "Solo", 2: "Duo", 3: "Threesome"}
        participant_suggestion = participant_map.get(highest_person_count, "Orgy / Group")
        dominant_location_tag = (
            max(location_counts, key=location_counts.get) if location_counts else None
        )

        suggestions = {
            "participants": participant_suggestion,
            "location_tag": dominant_location_tag,
        }
        self.finished.emit(suggestions)


class ShootMakerWorkflow(QObject):
    available_sources_loaded = Signal(list)
    ai_suggestions_ready = Signal(dict)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.project = main_window.project
        self.pipeline = main_window.pipeline
        self.thread = None
        self.worker = None

    def load_available_sources(self, shoot_type: str):
        logger.info(f"Loading available sources for a '{shoot_type}'...")
        source_list = []
        if shoot_type == "Photo Shoot":
            all_frames = self.project.export_data.get("all_extracted_frames", [])
            source_list.extend(all_frames)
            if self.project.source_type == "folder":
                source_list.extend(self.project.source_image_paths)
            unique_sources = sorted(list(set(source_list)))
            self.available_sources_loaded.emit(unique_sources)

        elif shoot_type == "Video Shoot":
            source_list = self.project.export_data.get("all_created_clips", [])
            self.available_sources_loaded.emit(sorted(list(set(source_list))))

    def run_ai_analysis_for_suggestions(self, media_paths: list):
        self.thread = QThread(self)
        self.worker = AIAnalysisWorker(media_paths, self.pipeline)
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.ai_suggestions_ready)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def save_shoot_to_project(self, shoot_data: dict):
        try:
            shoot_type = shoot_data.get("shoot_type")
            shoot_key = shoot_data.get("shoot_key")
            config = shoot_data.get("config")
            media_items = shoot_data.get("media_items")
            if not all([shoot_type, shoot_key, config, media_items]):
                logger.error("Attempted to save shoot with incomplete data.")
                return

            export_key, media_key = ("", "")
            if shoot_type == "Photo Shoot":
                export_key = "_shared_photoshoots" if config.get("is_shared") else "photoshoots"
                media_key = "images"
            else:  # Video Shoot
                export_key = "_shared_videoshoots" if config.get("is_shared") else "videoshoots"
                media_key = "videos"

            if export_key not in self.project.export_data:
                self.project.export_data[export_key] = {}

            self.project.export_data[export_key][shoot_key] = {
                "config": config,
                media_key: media_items,
            }
            logger.info(f"Successfully saved '{shoot_key}' to project under '{export_key}'.")
        except Exception as e:
            logger.error(f"Failed to save shoot data to project: {e}", exc_info=True)
