# GameMediaTool/gui/components/video_clipper_panel.py (Updated with full player controls)

import sys
import vlc
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QMessageBox,
    QComboBox,
    QListWidgetItem,
    QDialog,
    QApplication,
    QGridLayout,
    QSpinBox,
    QRadioButton,
)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QPalette, QColor, QCursor

from .player_widget import PlayerWidget
from .custom_slider import MarkerSlider
from tools import video_splitter
from tools.logger import get_logger

logger = get_logger("ClipperPanel")


# ... (AutoSplitDialog and ClipItemWidget classes remain unchanged) ...
class AutoSplitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auto-Split Options")
        layout = QGridLayout(self)
        self.duration_radio = QRadioButton("Split by Duration (seconds)")
        self.duration_radio.setChecked(True)
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 600)
        self.duration_spinbox.setValue(10)
        self.number_radio = QRadioButton("Split by Number of Clips")
        self.number_spinbox = QSpinBox()
        self.number_spinbox.setRange(1, 1000)
        self.number_spinbox.setValue(5)
        self.ai_radio = QRadioButton("🤖 Suggest Stable Scenes (AI)")
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.duration_radio, 0, 0)
        layout.addWidget(self.duration_spinbox, 0, 1)
        layout.addWidget(self.number_radio, 1, 0)
        layout.addWidget(self.number_spinbox, 1, 1)
        layout.addWidget(self.ai_radio, 2, 0, 1, 2)
        layout.addWidget(ok_button, 3, 0)
        layout.addWidget(cancel_button, 3, 1)

    def get_split_parameters(self):
        if self.duration_radio.isChecked():
            return {"mode": "duration", "value": self.duration_spinbox.value()}
        if self.number_radio.isChecked():
            return {"mode": "number", "value": self.number_spinbox.value()}
        if self.ai_radio.isChecked():
            return {"mode": "ai_suggest", "value": None}
        return None


class ClipItemWidget(QWidget):
    delete_requested = Signal(int)

    def __init__(self, text, row_index, parent=None):
        super().__init__(parent)
        self.row_index = row_index
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        self.label = QLabel(text)
        delete_button = QPushButton("❌")
        delete_button.setFixedSize(30, 30)
        delete_button.setObjectName("DeleteButton")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.row_index))
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(delete_button)


class VideoClipperPanel(QWidget):
    clips_confirmed = Signal(list)
    back_requested = Signal()

    SEGMENT_COLORS = [
        QColor(255, 105, 180, 150),
        QColor(100, 149, 237, 150),
        QColor(60, 179, 113, 150),
        QColor(255, 165, 0, 150),
        QColor(147, 112, 219, 150),
    ]

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.video_path = None
        self.clips = []
        self.current_clip = {"start": -1, "end": -1}
        self.true_duration_ms = -1
        self._setup_ui()
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self._connect_signals()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        title = QLabel("🎬 Clip Editor")
        title.setObjectName("TitleLabel")
        self.main_layout.addWidget(title)
        content_layout = QHBoxLayout()
        video_section_layout = QVBoxLayout()
        self.player_widget = PlayerWidget(self)
        video_section_layout.addWidget(self.player_widget)
        self.video_slider = MarkerSlider(Qt.Orientation.Horizontal)
        self.video_slider.setRange(0, 1000)
        video_section_layout.addWidget(self.video_slider)

        # [MODIFIED] Re-adding the full controls
        controls_layout = QHBoxLayout()
        self.rewind_button = QPushButton("⏪︎")
        self.play_pause_button = QPushButton("▶")
        self.stop_button = QPushButton("⏹️")
        self.forward_button = QPushButton("⏩︎")
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "0.75x", "1x", "1.5x", "2x"])
        self.speed_combo.setCurrentText("1x")
        controls_layout.addWidget(self.rewind_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.forward_button)
        controls_layout.addSpacing(15)
        controls_layout.addWidget(QLabel("Speed:"))
        controls_layout.addWidget(self.speed_combo)
        controls_layout.addStretch()
        self.time_label = QLabel("00:00.00 / 00:00.00")
        controls_layout.addWidget(self.time_label)
        video_section_layout.addLayout(controls_layout)

        sub_controls_layout = QHBoxLayout()
        self.start_clip_button = QPushButton("🔽 Mark Start")
        self.end_clip_button = QPushButton("🔼 Mark End & Add")
        self.auto_split_button = QPushButton("✨ Auto-Split...")
        self.end_clip_button.setObjectName("AddButton")
        sub_controls_layout.addStretch()
        sub_controls_layout.addWidget(self.auto_split_button)
        sub_controls_layout.addWidget(self.start_clip_button)
        sub_controls_layout.addWidget(self.end_clip_button)
        video_section_layout.addLayout(sub_controls_layout)
        content_layout.addLayout(video_section_layout, 3)
        clip_list_section_layout = QVBoxLayout()
        clip_list_section_layout.addWidget(QLabel("Clipped Segments:"))
        self.clip_list_widget = QListWidget()
        clip_list_section_layout.addWidget(self.clip_list_widget)
        content_layout.addLayout(clip_list_section_layout, 1)
        self.main_layout.addLayout(content_layout)
        bottom_bar = QHBoxLayout()
        self.back_button = QPushButton("⬅️ Back")
        self.confirm_clips_button = QPushButton("✔️ Confirm Clips & Continue")
        self.confirm_clips_button.setObjectName("ConfirmButton")
        bottom_bar.addWidget(self.back_button)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.confirm_clips_button)
        self.main_layout.addLayout(bottom_bar)
        self.reset_clip_buttons()
        self.back_button.clicked.connect(self.on_back_pressed)

    def _connect_signals(self):
        self.video_slider.sliderMoved.connect(self.set_player_position)
        self.play_pause_button.clicked.connect(self.player_widget.toggle_play_pause)
        self.stop_button.clicked.connect(self.stop_video)

        # [MODIFIED] Re-connecting the restored button signals
        self.rewind_button.clicked.connect(lambda: self.player_widget.seek_video(-10000))
        self.forward_button.clicked.connect(lambda: self.player_widget.seek_video(10000))
        self.speed_combo.currentTextChanged.connect(self.set_playback_rate)

        self.start_clip_button.clicked.connect(lambda: self.mark_bound("start"))
        self.end_clip_button.clicked.connect(lambda: self.mark_bound("end"))
        self.auto_split_button.clicked.connect(self.open_auto_split_dialog)
        self.confirm_clips_button.clicked.connect(self.confirm_clips)
        self.timer.timeout.connect(self.update_ui)
        self.video_slider.marker_clicked.connect(self.jump_to_clip_index)
        self.clip_list_widget.currentRowChanged.connect(self.jump_to_selected_clip)

    def set_playback_rate(self, rate_text):
        if self.player_widget:
            try:
                rate = float(rate_text.replace("x", ""))
                self.player_widget.set_rate(rate)
            except ValueError:
                logger.warning(f"Could not parse rate: {rate_text}")

    # ... (Rest of the file's methods are unchanged) ...
    def on_back_pressed(self):
        self.player_widget.release_player()
        self.back_requested.emit()

    def load_video(self, video_path):
        self.video_path = video_path
        self.clips.clear()
        self.clip_list_widget.clear()
        self.reset_clip_buttons()
        self.video_slider.set_markers([])
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.true_duration_ms = int(video_splitter.get_video_duration(video_path) * 1000)
        QApplication.restoreOverrideCursor()
        self.player_widget.load_video(video_path)
        QTimer.singleShot(100, self.player_widget.pause)
        self.timer.start()

    def open_auto_split_dialog(self):
        if not self.video_path:
            return
        dialog = AutoSplitDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            params = dialog.get_split_parameters()
            if not params:
                return
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                if params["mode"] == "ai_suggest":
                    generated_clips_data = self.main_window.pipeline.suggest_clips(self.video_path)
                    generated_clips_data = [{"start": s, "end": e} for s, e in generated_clips_data]
                else:
                    generated_clips_data, _ = video_splitter.generate_clip_timestamps(
                        self.video_path, params
                    )
            finally:
                QApplication.restoreOverrideCursor()
            if generated_clips_data:
                self.clips.clear()
                self.clip_list_widget.clear()
                [self.add_clip_to_list(c["start"], c["end"]) for c in generated_clips_data]

    def add_clip_to_list(self, start_ms, end_ms):
        clip = {"start": int(start_ms), "end": int(end_ms)}
        self.clips.append(clip)
        row_index = len(self.clips) - 1
        item_text = f"Clip {row_index + 1}: [{self._ms_to_time(clip['start'])} -> {self._ms_to_time(clip['end'])}]"
        list_item = QListWidgetItem(self.clip_list_widget)
        item_widget = ClipItemWidget(item_text, row_index)
        item_widget.delete_requested.connect(self.remove_clip)
        list_item.setSizeHint(item_widget.sizeHint())
        self.clip_list_widget.addItem(list_item)
        self.clip_list_widget.setItemWidget(list_item, item_widget)
        self.update_markers()

    def remove_clip(self, index_to_remove):
        if 0 <= index_to_remove < len(self.clips):
            self.clips.pop(index_to_remove)
        self.clip_list_widget.takeItem(index_to_remove)
        for i in range(self.clip_list_widget.count()):
            item = self.clip_list_widget.item(i)
            widget = self.clip_list_widget.itemWidget(item)
            if widget:
                widget.row_index = i
                start, end = self.clips[i]["start"], self.clips[i]["end"]
                widget.label.setText(
                    f"Clip {i + 1}: [{self._ms_to_time(start)} -> {self._ms_to_time(end)}]"
                )
        self.update_markers()

    def mark_bound(self, bound):
        if not self.player_widget.get_media():
            return
        current_time_ms = self.player_widget.get_time()
        if bound == "start":
            self.current_clip["start"] = current_time_ms
            self.start_clip_button.setText(f"Start: {self._ms_to_time(current_time_ms)}")
        elif bound == "end":
            start_ms = self.current_clip.get("start", -1)
            if start_ms >= 0 and current_time_ms > start_ms:
                self.add_clip_to_list(start_ms, current_time_ms)
                self.reset_clip_buttons()
        self.update_markers()

    def reset_clip_buttons(self):
        self.current_clip = {"start": -1, "end": -1}
        self.start_clip_button.setText("🔽 Mark Start")
        self.update_markers()

    def update_markers(self):
        length = self.true_duration_ms
        markers = []
        if length <= 0:
            return self.video_slider.set_markers([])
        for i, clip in enumerate(self.clips):
            markers.append(
                (
                    clip["start"] / length,
                    clip["end"] / length,
                    self.SEGMENT_COLORS[i % len(self.SEGMENT_COLORS)],
                )
            )
        if self.current_clip["start"] != -1:
            markers.append(
                (
                    self.current_clip["start"] / length,
                    self.player_widget.get_position(),
                    self.SEGMENT_COLORS[len(self.clips) % len(self.SEGMENT_COLORS)],
                )
            )
        self.video_slider.set_markers(markers)

    def confirm_clips(self):
        """Gathers selected clips and emits the confirmation signal."""
        if not self.clips:
            QMessageBox.warning(self, "No Clips", "No clips have been added.")
            return

        # [THE FIX] The stop_video() call is removed from here.
        # MainWindow will now handle stopping the player.
        self.clips_confirmed.emit(self.clips)

    def stop_video(self):
        self.player_widget.stop_video()
        self.timer.stop()
        self.reset_clip_buttons()

    def update_ui(self):
        if not self.player_widget.get_media():
            return
        current_time_ms = self.player_widget.get_time()
        total_time_ms = self.true_duration_ms
        if total_time_ms > 0 and not self.video_slider.isSliderDown():
            self.video_slider.setValue(int((current_time_ms / total_time_ms) * 1000))
        self.time_label.setText(
            f"{self._ms_to_time(current_time_ms)} / {self._ms_to_time(total_time_ms)}"
        )
        self.play_pause_button.setText("⏸️" if self.player_widget.is_playing() else "▶")
        self.update_markers()

    def set_player_position(self, value):
        self.player_widget.set_position(value / 1000.0)

    def jump_to_selected_clip(self, row):
        if 0 <= row < len(self.clips):
            self.player_widget.set_time(self.clips[row]["start"])

    def jump_to_clip_index(self, index):
        if 0 <= index < self.clip_list_widget.count():
            self.clip_list_widget.setCurrentRow(index)

    def _ms_to_time(self, ms):
        if ms < 0:
            ms = 0
        s, ms_rem = divmod(int(ms), 1000)
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}.{int(ms_rem/10):02d}"
