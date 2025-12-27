# GameMediaTool/gui/components/frame_extraction_dialog.py (New File)

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QDialogButtonBox,
    QLabel,
    QDoubleSpinBox,
    QSpinBox,
    QGroupBox,
)
from PySide6.QtCore import Qt


class FrameExtractionDialog(QDialog):
    def __init__(self, parent=None, default_interval=2, default_threshold=60.0):
        super().__init__(parent)
        self.setWindowTitle("Frame Extraction Settings")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        main_group = QGroupBox("Adjust Quantity vs. Quality")
        grid_layout = QGridLayout(main_group)

        # --- Interval Setting (Quantity) ---
        grid_layout.addWidget(QLabel("<b>Sample Interval (seconds):</b>"), 0, 0)
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 60)
        self.interval_spinbox.setValue(default_interval)
        self.interval_spinbox.setSuffix(" s")
        self.interval_spinbox.setToolTip("How often to grab a frame. Smaller number = MORE frames.")
        grid_layout.addWidget(self.interval_spinbox, 0, 1)

        # --- Blur Threshold Setting (Quality) ---
        grid_layout.addWidget(QLabel("<b>Sharpness Threshold:</b>"), 1, 0)
        self.threshold_spinbox = QDoubleSpinBox()
        self.threshold_spinbox.setRange(10.0, 500.0)
        self.threshold_spinbox.setValue(default_threshold)
        self.threshold_spinbox.setSingleStep(5.0)
        self.threshold_spinbox.setToolTip(
            "How strict the quality filter is. Smaller number = MORE frames (less sharp)."
        )
        grid_layout.addWidget(self.threshold_spinbox, 1, 1)

        layout.addWidget(main_group)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_settings(self):
        """Returns the selected settings as a dictionary."""
        return {
            "interval_seconds": self.interval_spinbox.value(),
            "blur_threshold": self.threshold_spinbox.value(),
        }
