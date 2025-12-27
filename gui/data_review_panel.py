# GameMediaTool/gui/data_review_panel.py (ملف جديد)

import os
import shutil
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QGroupBox,
    QScrollArea,
    QGridLayout,
    QFrame,
    QMessageBox,
    QComboBox,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen

from tools.logger import get_logger
from utils.file_ops import sanitize_filename

logger = get_logger("DataReviewPanel")


# سنستخدم نفس الويدجت الخاص باختيار الفريمات من contact_sheet_panel
# يمكنك نسخ هذا الكلاس أو استيراده إذا كنت تفضل تقسيمه
class SelectableFrameWidget(QFrame):
    """ويدجت لعرض صورة مصغرة يمكن تحديدها."""

    def __init__(self, frame_path, parent=None):
        super().__init__(parent)
        self.frame_path = frame_path
        self.is_selected = False
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(160, 120)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(frame_path)
        self.image_label.setPixmap(
            pixmap.scaled(QSize(150, 90), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        main_layout.addWidget(self.image_label)
        self.update()

    def mousePressEvent(self, event):
        self.is_selected = not self.is_selected
        self.update()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_selected:
            painter = QPainter(self)
            pen = QPen(QColor(46, 204, 113), 4, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self.rect().adjusted(2, 2, -2, -2))


class DataReviewPanel(QWidget):
    back_requested = Signal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.review_base_path = ""
        self.image_widgets = []

        main_layout = QVBoxLayout(self)
        title = QLabel("🔬 AI Data Review & Correction")
        title.setObjectName("TitleLabel")
        main_layout.addWidget(title)

        main_hbox = QHBoxLayout()

        # --- قائمة المجلدات (اليسار) ---
        left_panel = QGroupBox("AI-Predicted Classes")
        left_layout = QVBoxLayout(left_panel)
        self.folder_list_widget = QListWidget()
        left_layout.addWidget(self.folder_list_widget)
        main_hbox.addWidget(left_panel, 1)

        # --- شبكة الصور (اليمين) ---
        right_panel = QGroupBox("Images in Selected Class")
        right_layout = QVBoxLayout(right_panel)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        grid_container = QWidget()
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll_area.setWidget(grid_container)
        right_layout.addWidget(scroll_area)
        main_hbox.addWidget(right_panel, 4)

        main_layout.addLayout(main_hbox)

        # --- شريط الأدوات السفلي ---
        bottom_bar = QHBoxLayout()
        self.back_button = QPushButton("⬅️ Back to AI Center")
        bottom_bar.addWidget(self.back_button)
        bottom_bar.addStretch()
        bottom_bar.addWidget(QLabel("Move Selected To:"))
        self.move_to_combo = QComboBox()
        self.move_button = QPushButton("➡️ Move")
        self.move_button.setObjectName("AddButton")
        bottom_bar.addWidget(self.move_to_combo)
        bottom_bar.addWidget(self.move_button)
        main_layout.addLayout(bottom_bar)

        self._connect_signals()

    def _connect_signals(self):
        self.back_button.clicked.connect(self.back_requested.emit)
        self.folder_list_widget.currentRowChanged.connect(self.on_folder_selected)
        self.move_button.clicked.connect(self.move_selected_images)

    def activate(self):
        logger.info("Data Review Panel activated.")
        self.load_review_data()

    def load_review_data(self):
        char_name_safe = sanitize_filename(self.main_window.project.character_name)
        # هذا هو المجلد الذي أنشأه الـ pipeline
        self.review_base_path = os.path.join("temp", char_name_safe, "review_needed")

        self.folder_list_widget.clear()
        self.move_to_combo.clear()

        if not os.path.isdir(self.review_base_path):
            QMessageBox.warning(
                self,
                "No Data",
                "No data has been generated for review yet. Please run 'Step 2: Generate Data' first.",
            )
            return

        class_folders = sorted(
            [
                d
                for d in os.listdir(self.review_base_path)
                if os.path.isdir(os.path.join(self.review_base_path, d))
            ]
        )

        for folder_name in class_folders:
            folder_path = os.path.join(self.review_base_path, folder_name)
            image_count = len(
                [f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg"))]
            )
            self.folder_list_widget.addItem(f"{folder_name} ({image_count} images)")

        self.move_to_combo.addItems(class_folders)

    def on_folder_selected(self, index):
        if index < 0:
            return

        # Clear previous images
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.image_widgets.clear()

        # استخراج اسم المجلد من النص
        folder_text = self.folder_list_widget.item(index).text()
        folder_name = folder_text.split(" (")[0]
        folder_path = os.path.join(self.review_base_path, folder_name)

        image_files = sorted(
            [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.lower().endswith((".png", ".jpg"))
            ]
        )

        row, col, max_cols = 0, 0, 5
        for img_path in image_files:
            widget = SelectableFrameWidget(img_path)
            self.image_widgets.append(widget)
            self.grid_layout.addWidget(widget, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def move_selected_images(self):
        destination_folder_name = self.move_to_combo.currentText()
        if not destination_folder_name:
            QMessageBox.warning(self, "No Destination", "Please select a destination class.")
            return

        selected_image_widgets = [w for w in self.image_widgets if w.is_selected]
        if not selected_image_widgets:
            QMessageBox.warning(self, "No Selection", "Please select one or more images to move.")
            return

        destination_path = os.path.join(self.review_base_path, destination_folder_name)
        moved_count = 0

        for widget in selected_image_widgets:
            source_path = widget.frame_path
            dest_file_path = os.path.join(destination_path, os.path.basename(source_path))
            try:
                shutil.move(source_path, dest_file_path)
                moved_count += 1
            except Exception as e:
                logger.error(f"Failed to move {source_path} to {destination_path}: {e}")

        QMessageBox.information(
            self,
            "Move Complete",
            f"Successfully moved {moved_count} images to '{destination_folder_name}'.",
        )

        # إعادة تحميل كل شيء لتحديث الأرقام والواجهة
        self.load_review_data()
        # مسح الشبكة لأن المجلد الحالي تغير
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.image_widgets.clear()
