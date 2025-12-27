# GameMediaTool/gui/components/contact_sheet_panel.py (Corrected with QCheckBox import)

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                               QListWidget, QListWidgetItem, QAbstractItemView,
                               QScrollArea, QApplication, QGridLayout, QCheckBox) # <-- [THE FIX] QCheckBox added
from PySide6.QtCore import Qt, Signal, QSize, QThread, QObject
from PySide6.QtGui import QPixmap, QColor, QPalette

from tools.logger import get_logger

logger = get_logger("ContactSheetPanel")

class FrameWidget(QWidget):
    """A small widget to display a single frame thumbnail with a checkbox."""
    frame_selected = Signal(str, bool)
    THUMBNAIL_SIZE = 160

    def __init__(self, frame_path, parent=None):
        super().__init__(parent)
        self.frame_path = frame_path
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE)
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail.setStyleSheet("background-color: #222; border: 1px solid #444;")
        
        pixmap = QPixmap(frame_path)
        
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumbnail.setPixmap(scaled_pixmap)
        else:
            self.thumbnail.setText("Load Error")

        self.checkbox = QCheckBox(os.path.basename(frame_path))
        self.checkbox.setChecked(False) # Default to NOT selected
        self.checkbox.stateChanged.connect(self._emit_selection_state)

        layout.addWidget(self.thumbnail)
        layout.addWidget(self.checkbox)

    def _emit_selection_state(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        self.frame_selected.emit(self.frame_path, is_checked)

class FrameLoaderWorker(QObject):
    """Worker to load frame paths in the background to avoid freezing the UI."""
    frame_loaded = Signal(str)
    finished = Signal()

    def __init__(self, frame_paths):
        super().__init__()
        self.frame_paths = frame_paths
        self.is_running = True

    def run(self):
        for path in self.frame_paths:
            if not self.is_running: break
            self.frame_loaded.emit(path)
        self.finished.emit()
    
    def stop(self):
        self.is_running = False

class ContactSheetPanel(QWidget):
    frames_confirmed = Signal(list)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_frames = set()

        main_layout = QVBoxLayout(self)
        title = QLabel("🎞️ Select Frames for Processing")
        title.setObjectName("TitleLabel")
        main_layout.addWidget(title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area)

        bottom_bar = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.deselect_all_button = QPushButton("Deselect All")
        self.confirm_button = QPushButton("✔️ Confirm Selection & Start AI Analysis")
        self.confirm_button.setObjectName("ConfirmButton")
        
        bottom_bar.addWidget(self.select_all_button)
        bottom_bar.addWidget(self.deselect_all_button)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.confirm_button)
        main_layout.addLayout(bottom_bar)

        self.select_all_button.clicked.connect(self._select_all)
        self.deselect_all_button.clicked.connect(self._deselect_all)
        self.confirm_button.clicked.connect(self.confirm_selection)
        
        self.thread = None
        self.worker = None

    def load_frames(self, frame_paths):
        logger.info(f"Loading {len(frame_paths)} frames into the contact sheet.")
        self.clear_grid()
        self.selected_frames = set() # Start with an empty set

        if self.thread and self.thread.isRunning():
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()

        self.thread = QThread()
        self.worker = FrameLoaderWorker(frame_paths)
        self.worker.moveToThread(self.thread)

        self.worker.frame_loaded.connect(self._add_frame_widget)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: logger.info("Finished loading all frame widgets into contact sheet."))
        
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def _add_frame_widget(self, frame_path):
        row, col = divmod(self.grid_layout.count(), 5) # 5 widgets per row
        frame_widget = FrameWidget(frame_path)
        frame_widget.frame_selected.connect(self._on_frame_selected)
        self.grid_layout.addWidget(frame_widget, row, col)

    def _on_frame_selected(self, frame_path, is_selected):
        if is_selected:
            self.selected_frames.add(frame_path)
        else:
            self.selected_frames.discard(frame_path)

    def confirm_selection(self):
        if not self.selected_frames:
            QMessageBox.warning(self, "No Frames Selected", "Please select at least one frame to continue.")
            return
        logger.info(f"User confirmed {len(self.selected_frames)} frames.")
        self.frames_confirmed.emit(sorted(list(self.selected_frames)))

    def clear_grid(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.selected_frames.clear()

    def _select_all(self):
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, FrameWidget):
                widget.checkbox.setChecked(True)

    def _deselect_all(self):
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, FrameWidget):
                widget.checkbox.setChecked(False)