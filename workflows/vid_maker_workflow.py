# GameMediaTool/workflows/vid_maker_workflow.py (Corrected worker initialization)

import os
from PySide6.QtCore import QObject, Signal, QThread

from gui.components.workers import VideoSplitterWorker
from tools.logger import get_logger
from utils.file_ops import sanitize_filename, ensure_folder

logger = get_logger("VidMakerWorkflow")


class VidMakerWorkflow(QObject):
    splitting_finished = Signal(dict)
    progress_updated = Signal(int)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.project = main_window.project
        self.pipeline = main_window.pipeline
        self.thread = None
        self.current_worker = None

    def run_video_splitting(self, clips_timestamps: list):
        """Creates and runs the VideoSplitterWorker in a background thread."""
        logger.info(
            f"Received {len(clips_timestamps)} timestamps. Starting video splitting worker."
        )
        temp_clips_folder = self._get_temp_folder("vids_clips")

        # [THE FIX] Pass the required 'self.pipeline' object to the worker's constructor.
        self.current_worker = VideoSplitterWorker(
            self.project.source_video_path, temp_clips_folder, clips_timestamps, self.pipeline
        )

        self.current_worker.finished.connect(self.splitting_finished)
        self._run_worker(self.current_worker)

    def _run_worker(self, worker_instance):
        """Generic method to create, configure, and run any worker in a QThread."""
        self.thread = QThread(self)
        worker_instance.moveToThread(self.thread)

        if hasattr(worker_instance, "progress"):
            worker_instance.progress.connect(self.progress_updated)

        worker_instance.finished.connect(self.thread.quit)
        worker_instance.finished.connect(worker_instance.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_worker_ref)

        self.thread.started.connect(worker_instance.run)
        self.thread.start()

        logger.info(f"Started worker '{type(worker_instance).__name__}' in a new thread.")

    def _clear_worker_ref(self):
        """Clears references to the worker and thread after they have finished."""
        self.current_worker = None
        self.thread = None

    def stop_current_task(self):
        """Allows stopping the current running worker."""
        if self.current_worker and hasattr(self.current_worker, "stop"):
            self.current_worker.stop()

    def _get_temp_folder(self, subfolder_name: str) -> str:
        """Creates and returns a path to a temporary folder for the current project."""
        char_name_safe = sanitize_filename(self.project.character_name)
        temp_folder = os.path.join("temp", char_name_safe, subfolder_name)
        ensure_folder(temp_folder)
        return temp_folder
