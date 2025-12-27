# GameMediaTool/workflows/photo_maker_workflow.py (Corrected with one-time cleanup)

import os
import shutil
from PySide6.QtCore import QObject, Signal, QThread
from gui.components.workers import FrameExtractorWorker, YOLOWorker, FinalProcessorWorker
from tools.logger import get_logger
from utils.file_ops import sanitize_filename, ensure_folder

logger = get_logger("PhotoMakerWorkflow")


class PhotoMakerWorkflow(QObject):
    extraction_finished = Signal(list)
    yolo_analysis_finished = Signal(dict, list, set)
    final_processing_finished = Signal(list)
    progress_updated = Signal(int)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.project = main_window.project
        self.pipeline = main_window.pipeline
        self.thread = None
        self.worker = None
        logger.info("PhotoMakerWorkflow initialized")

    def start_workflow(self, source_type: str, settings: dict = None):
        logger.info(f"Starting PhotoMaker workflow with source_type: {source_type}, settings: {settings}")
        if source_type in ["video", "clips"]:
            source_paths = (
                self.project.export_data.get("all_created_clips", [])
                if source_type == "clips"
                else [self.project.source_video_path]
            )
            if not source_paths:
                logger.warning("No source paths found, emitting empty extraction finished")
                self.extraction_finished.emit([])
                return

            # [THE FIX] Perform the cleanup ONCE here, before starting the worker.
            output_folder = self._get_temp_folder("extracted_frames")
            if os.path.isdir(output_folder):
                logger.warning(f"Cleaning previous extraction results from: {output_folder}")
                shutil.rmtree(output_folder)
            ensure_folder(output_folder)
            logger.debug(f"Output folder prepared: {output_folder}")

            self._run_frame_extraction(source_paths, settings, output_folder)
        elif source_type == "folder":
            logger.info("Emitting source image paths for folder source")
            self.extraction_finished.emit(self.project.source_image_paths)

    def _run_frame_extraction(self, video_paths: list, settings: dict, output_folder: str):
        settings = settings or {}
        blur_thresh = settings.get("blur_threshold", 60.0)
        interval = settings.get("interval_seconds", 1)

        logger.info(
            f"Starting frame extraction with blur threshold: {blur_thresh} and interval: {interval}s"
        )
        logger.debug(f"Video paths: {video_paths}, output: {output_folder}")

        worker = FrameExtractorWorker(
            video_paths, output_folder, blur_threshold=blur_thresh, interval_seconds=interval
        )
        self._run_worker(worker, self.extraction_finished)

    def run_yolo_analysis(self, selected_paths: list):
        logger.info(f"Starting YOLO analysis on {len(selected_paths)} paths")
        tasks = {"body_assets", "clothing_assets"}
        worker = YOLOWorker(self.pipeline, selected_paths)
        worker.finished.connect(
            lambda results: self.yolo_analysis_finished.emit(results, selected_paths, tasks)
        )
        self._run_worker(worker, None)

    def run_final_processing(self, instructions: dict):
        logger.info(f"Starting final processing with instructions: {list(instructions.keys())}")
        worker = FinalProcessorWorker(self.main_window, instructions)
        self._run_worker(worker, self.final_processing_finished)

    def _run_worker(self, worker_instance, finished_signal):
        self.thread = QThread(self)
        self.worker = worker_instance
        self.worker.moveToThread(self.thread)

        if finished_signal:
            self.worker.finished.connect(finished_signal)
        if hasattr(self.worker, "progress"):
            self.worker.progress.connect(self.progress_updated)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

        logger.info(f"Started worker '{type(self.worker).__name__}' in a new thread.")

    def stop_current_task(self):
        if self.worker and hasattr(self.worker, "stop"):
            logger.info("Stopping current worker task")
            self.worker.stop()
        else:
            logger.debug("No worker to stop or no stop method")

    def _get_temp_folder(self, subfolder_name: str) -> str:
        char_name_safe = sanitize_filename(self.project.character_name)
        temp_folder = os.path.join("temp", char_name_safe, subfolder_name)
        ensure_folder(temp_folder)
        logger.debug(f"Temp folder ensured: {temp_folder}")
        return temp_folder
