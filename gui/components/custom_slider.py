# GameMediaTool/gui/components/custom_slider.py (Complete and Final)

from PySide6.QtWidgets import QSlider
from PySide6.QtGui import QPainter, QBrush, QColor, QPen
from PySide6.QtCore import Qt, Signal

class MarkerSlider(QSlider):
    marker_clicked = Signal(int)
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._markers = []

    def set_markers(self, markers):
        """Sets the list of markers, where each marker is a tuple (start_pos, end_pos, color)."""
        self._markers = markers
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._markers: return
        
        painter = QPainter(self)
        pen = QPen(Qt.PenStyle.NoPen)
        
        slider_height = self.height()
        marker_height = int(slider_height / 2.5)
        y_pos = int((slider_height - marker_height) / 2)
        
        for start_pos, end_pos, color in self._markers:
            start_pixel = int(start_pos * self.width())
            end_pixel = int(end_pos * self.width())
            
            painter.setBrush(QBrush(color))
            painter.setPen(pen)
            painter.drawRect(start_pixel, y_pos, end_pixel - start_pixel, marker_height)
            
    def mousePressEvent(self, event):
        """Maps click position to a marker index and emits the signal."""
        click_position = event.position().toPoint().x() / self.width()
        
        for i, (start_pos, end_pos, color) in enumerate(self._markers):
            if start_pos <= click_position <= end_pos:
                self.marker_clicked.emit(i)
                return
        
        super().mousePressEvent(event)