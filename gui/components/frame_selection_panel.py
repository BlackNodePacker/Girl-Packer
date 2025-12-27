# GameMediaTool/gui/components/frame_selection_panel.py (Corrected and final)

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QMessageBox, QListWidgetItem
from PySide6.QtCore import Signal

try:
    import qtawesome as qta
    QTAWESOME_LOADED = True
except ImportError:
    QTAWESOME_LOADED = False

from tools.logger import get_logger
from utils.file_ops import ensure_folder, sanitize_filename
from .player_widget import PlayerWidget
from tools.frame_extractor import extract_frames # This import is now correct

logger = get_logger("FrameSelectionPanel")

class FrameSelectionPanel(QWidget):
    frames_confirmed = Signal(list)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clips_to_process = []; self.selected_frames = {}; self.current_clip_index = -1; self.snapshot_dir = ""
        final_layout = QVBoxLayout(self); top_layout = QHBoxLayout()
        clip_list_layout = QVBoxLayout(); clip_list_layout.addWidget(QLabel("Clips to Process:")); self.clip_list_widget = QListWidget(); self.clip_list_widget.setToolTip("Click on a clip to play it"); clip_list_layout.addWidget(self.clip_list_widget); top_layout.addLayout(clip_list_layout, 1)
        self.player_widget = PlayerWidget(); top_layout.addWidget(self.player_widget, 3)
        bottom_bar = QHBoxLayout(); self.back_button = self._create_button('fa5s.arrow-left', "Back"); self.auto_snapshot_button = self._create_button('fa5s.robot', "Auto-Snapshot", color='orange'); self.snapshot_button = self._create_button('fa5s.camera', " Take Snapshot", color='cyan'); self.confirm_button = self._create_button('fa5s.check-double', "Confirm Frames & Continue"); self.confirm_button.setObjectName("ConfirmButton")
        bottom_bar.addWidget(self.back_button); bottom_bar.addStretch(); bottom_bar.addWidget(self.auto_snapshot_button); bottom_bar.addWidget(self.snapshot_button); bottom_bar.addSpacing(20); bottom_bar.addWidget(self.confirm_button)
        final_layout.addLayout(top_layout); final_layout.addLayout(bottom_bar)
        self.clip_list_widget.currentRowChanged.connect(self.play_selected_clip); self.back_button.clicked.connect(self.back_requested.emit); self.snapshot_button.clicked.connect(self.take_snapshot); self.auto_snapshot_button.clicked.connect(self.auto_snapshot); self.confirm_button.clicked.connect(self.confirm_frames)

    def auto_snapshot(self):
        if self.current_clip_index < 0: return
        clip_path = self.clips_to_process[self.current_clip_index]
        logger.info(f"Starting auto-snapshot for {clip_path}...")
        
        # [MODIFIED] Call the new function with its updated signature
        extracted_paths = extract_frames(
            video_path=clip_path, 
            output_folder=self.snapshot_dir,
            interval_seconds=1 # Use a smaller interval for more options from short clips
        )
        
        if extracted_paths:
            for path in extracted_paths:
                self.add_frame_to_selection(clip_path, path)
            logger.info(f"Auto-snapshot complete. Added {len(extracted_paths)} frames.")
        else:
            QMessageBox.warning(self, "Auto-Snapshot Failed", "Could not extract any frames from this clip.")
    
    def _create_button(self, icon_name, text, color='white'):
        if QTAWESOME_LOADED:
            try: return QPushButton(qta.icon(icon_name, color=color), f" {text}" if text else "")
            except Exception: return QPushButton(text)
        else: return QPushButton(text)
    def load_clips(self, clip_paths: list, snapshot_dir: str):
        self.player_widget.stop_video(); self.clip_list_widget.clear(); self.selected_frames.clear()
        self.clips_to_process = clip_paths; self.snapshot_dir = snapshot_dir; ensure_folder(self.snapshot_dir)
        for i, clip_path in enumerate(clip_paths): self.clip_list_widget.addItem(QListWidgetItem(f"Clip {i+1}: {os.path.basename(clip_path)}"))
        if self.clips_to_process: self.clip_list_widget.setCurrentRow(0)
    def play_selected_clip(self, index: int):
        if 0 <= index < len(self.clips_to_process): self.current_clip_index = index; self.player_widget.load_video(self.clips_to_process[index])
    def take_snapshot(self):
        if self.current_clip_index < 0: return
        self.player_widget.pause()
        clip_path = self.clips_to_process[self.current_clip_index]; clip_name = os.path.splitext(os.path.basename(clip_path))[0]; timestamp_ms = self.player_widget.get_time()
        sane_clip_name = sanitize_filename(clip_name); filename = f"{sane_clip_name}_snapshot_at_{timestamp_ms}ms.png"; filepath = os.path.join(self.snapshot_dir, filename)
        result = self.player_widget.mediaplayer.video_take_snapshot(0, filepath, 0, 0); self.player_widget.play()
        if result == 0: self.add_frame_to_selection(clip_path, filepath)
        else: logger.error(f"Failed to take snapshot. VLC result code: {result}"); QMessageBox.critical(self, "Error", "Could not save snapshot.")
    def add_frame_to_selection(self, clip_path, frame_path):
        if clip_path not in self.selected_frames: self.selected_frames[clip_path] = []
        if frame_path not in self.selected_frames[clip_path]:
            self.selected_frames[clip_path].append(frame_path); count = len(self.selected_frames[clip_path])
            base_name = os.path.basename(clip_path); self.clip_list_widget.item(self.current_clip_index).setText(f"Clip {self.current_clip_index+1}: {base_name} ({count} snapshots)")
    def confirm_frames(self):
        final_frame_list = sorted([frame for frames in self.selected_frames.values() for frame in frames])
        if not final_frame_list: QMessageBox.warning(self, "No Frames Selected", "Please take at least one snapshot."); return
        self.player_widget.stop_video(); self.frames_confirmed.emit(final_frame_list)