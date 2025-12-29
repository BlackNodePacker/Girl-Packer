from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QTextEdit,
    QMessageBox,
)
from PySide6.QtCore import Signal
from tools.pack_analyzer import PackAnalyzer
from tools.logger import get_logger
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QTextEdit,
    QMessageBox,
)
from PySide6.QtCore import Signal
from tools.pack_analyzer import PackAnalyzer
from tools.logger import get_logger
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
import os

logger = get_logger("PackReviewPanel")


class PackReviewPanel(QWidget):
    """Panel to inspect a pack folder and trigger export via the main window.

    This is intentionally simple: it selects a folder, runs PackAnalyzer,
    shows a brief text report and allows reusing the application's export
    pipeline on the selected folder.
    """

    back_requested = Signal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.current_pack_path = ""

        main_layout = QVBoxLayout(self)
        title = QLabel("📦 Pack Review & Export")
        title.setObjectName("TitleLabel")
        main_layout.addWidget(title)

        h1 = QHBoxLayout()
        self.pick_button = QPushButton("Select Pack Folder")
        self.analyze_button = QPushButton("Analyze Pack")
        h1.addWidget(self.pick_button)
        h1.addWidget(self.analyze_button)
        main_layout.addLayout(h1)

        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        main_layout.addWidget(self.report_view)

        bottom_h = QHBoxLayout()
        self.back_button = QPushButton("⬅️ Back")
        self.export_button = QPushButton("Export This Pack")
        bottom_h.addWidget(self.back_button)
        bottom_h.addStretch()
        bottom_h.addWidget(self.export_button)
        main_layout.addLayout(bottom_h)

        self.pick_button.clicked.connect(self._pick_folder)
        self.analyze_button.clicked.connect(self._analyze)
        self.back_button.clicked.connect(self.back_requested.emit)
        self.export_button.clicked.connect(self._export)

    def _pick_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Pack Folder")
        if path:
            self.current_pack_path = path
            self.report_view.setPlainText(f"Selected: {path}\n")

    def _analyze(self):
        if not self.current_pack_path or not os.path.isdir(self.current_pack_path):
            QMessageBox.warning(self, "No Pack", "Please select a valid pack folder first.")
            return
        analyzer = PackAnalyzer(self.current_pack_path)
        report = analyzer.analyze()
        lines = [f"Rating: {report.get('rating')}", "\nPositives:"]
        for p in report.get("positives", []):
            lines.append(f" - {p}")
        lines.append("\nWarnings:")
        for w in report.get("warnings", []):
            lines.append(f" - {w}")
        lines.append("\nErrors:")
        for e in report.get("errors", []):
            lines.append(f" - {e}")
        self.report_view.setPlainText("\n".join(lines))

    def _export(self):
        if not self.current_pack_path or not os.path.isdir(self.current_pack_path):
            QMessageBox.warning(self, "No Pack", "Please select a valid pack folder first.")
            return

        try:
            name = os.path.basename(os.path.normpath(self.current_pack_path))
            self.main_window.project.character_name = name
            self.main_window.project.final_output_path = self.current_pack_path
        except Exception:
            pass

        # Hand off to main window export routine
        try:
            self.main_window._start_final_export()
        except Exception:
            QMessageBox.warning(self, "Export Error", "Failed to start export from main window.")
