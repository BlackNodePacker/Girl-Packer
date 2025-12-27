# GameMediaTool/gui/components/manual_crop_dialog.py (Moved to components folder)

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor
from PySide6.QtCore import Qt, QRect, QPoint

class CropArea(QLabel):
    """A custom QLabel that allows drawing a selection rectangle."""
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setPixmap(pixmap)
        self.begin = QPoint()
        self.end = QPoint()
        self.rect = QRect()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.begin.isNull() and not self.end.isNull():
            painter = QPainter(self)
            pen = QPen(QColor(0, 255, 255, 200), 2, Qt.PenStyle.SolidLine)
            brush = QBrush(QColor(0, 255, 255, 70))
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        self.begin = event.position().toPoint()
        self.end = event.position().toPoint()
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event):
        self.end = event.position().toPoint()
        self.rect = QRect(self.begin, self.end).normalized()
        self.update()

class ManualCropDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manual Crop Tool - Draw a box on the image")
        
        self.original_pixmap = QPixmap(image_path)
        # Scale image for display to ensure it fits on screen
        scaled_pixmap = self.original_pixmap.scaled(1280, 720, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        self.crop_area = CropArea(scaled_pixmap)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.crop_area)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_crop_rect(self):
        """Converts the rectangle drawn on the scaled image back to original image coordinates."""
        drawn_rect = self.crop_area.rect
        scaled_pixmap = self.crop_area.pixmap()

        if not scaled_pixmap or scaled_pixmap.isNull() or scaled_pixmap.width() == 0 or scaled_pixmap.height() == 0:
            return QRect()

        # Calculate the scaling factor
        scale_x = self.original_pixmap.width() / scaled_pixmap.width()
        scale_y = self.original_pixmap.height() / scaled_pixmap.height()

        # Apply the scaling factor to the drawn rectangle
        original_x = int(drawn_rect.x() * scale_x)
        original_y = int(drawn_rect.y() * scale_y)
        original_width = int(drawn_rect.width() * scale_x)
        original_height = int(drawn_rect.height() * scale_y)
        
        return QRect(original_x, original_y, original_width, original_height)