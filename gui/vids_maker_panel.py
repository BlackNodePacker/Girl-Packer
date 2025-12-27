# GameMediaTool/gui/vids_maker_panel.py (Final version with freeze fix)

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from PySide6.QtCore import Signal

from .components import VideoClipperPanel 
from .components import VidTaggerPanel

from tools.logger import get_logger

logger = get_logger("VidsMakerPanel_UI")

class VidsMakerPanel(QWidget):
    back_requested = Signal()
    export_complete = Signal()
    splitting_requested = Signal(list)
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.step_stack = QStackedWidget()
        main_layout.addWidget(self.step_stack)

        self.clipper_step = VideoClipperPanel(main_window)
        self.tagger_step = VidTaggerPanel(main_window)
        
        self.step_stack.addWidget(self.clipper_step)
        self.step_stack.addWidget(self.tagger_step)
        
        self._connect_internal_signals()

    def _connect_internal_signals(self):
        self.clipper_step.clips_confirmed.connect(self.splitting_requested)
        # [MODIFIED] Both back buttons now go through the cleanup function
        self.clipper_step.back_requested.connect(self._cleanup_and_go_back)
        self.tagger_step.back_requested.connect(self.go_to_clipper)
        self.tagger_step.export_requested.connect(self.on_export_requested)

    def _cleanup_and_go_back(self):
        """[NEW] Central function to clean up resources before leaving the panel."""
        logger.info("Cleaning up VidMakerPanel resources...")
        self.clipper_step.player_widget.release_player()
        self.tagger_step.preview_player.release_player()
        self.back_requested.emit()

    def activate(self):
        self.go_to_clipper()
        video_path = self.main_window.project.source_video_path
        if video_path and os.path.exists(video_path):
            self.clipper_step.load_video(video_path)
        else:
            QMessageBox.warning(self, "No Video", "Vid Maker requires a valid video source.")
            self._cleanup_and_go_back()

    def go_to_clipper(self):
        self.tagger_step.preview_player.release_player()
        self.step_stack.setCurrentWidget(self.clipper_step)
        
    def on_splitting_finished(self, clips_data_with_ai: dict):
        if not clips_data_with_ai:
            QMessageBox.warning(self, "Analysis Failed", "Could not process clips for tagging.")
            self._cleanup_and_go_back()
            return
            
        logger.info(f"UI received {len(clips_data_with_ai)} clips with AI data to tag.")
        self.tagger_step.load_clips(clips_data_with_ai)
        self.step_stack.setCurrentWidget(self.tagger_step)

    def on_export_requested(self, tagged_data: dict):
        project_data = self.main_window.project.export_data
        project_data['tagged_videos'] = tagged_data
        
        QMessageBox.information(self, "Vid Maker Complete", 
                                f"Work saved to project. {len(tagged_data)} vids were tagged.")
        
        self.export_complete.emit()
        self._cleanup_and_go_back() # [MODIFIED] Call the cleanup function on successful export