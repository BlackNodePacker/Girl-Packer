# GameMediaTool/gui/components/image_viewer_widget.py (Final fix for drag/resize logic)

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QCursor
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QSize

from tools.logger import get_logger

logger = get_logger("ImageViewerWidget")


class ImageViewerWidget(QWidget):
    box_clicked = Signal(dict)
    new_box_drawn = Signal(QRect)
    box_modified = Signal(dict)

    MODE_SELECT = "select"
    MODE_DRAW = "draw"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.original_width = 1
        self.original_height = 1
        self.boxes = []
        self.selected_box_detection = None

        self.current_mode = self.MODE_SELECT
        self.is_drawing = False
        self.draw_start_point = QPoint()
        self.draw_end_point = QPoint()

        self.is_dragging = False
        self.drag_start_point = QPoint()
        self.drag_handle = None

        self.setMouseTracking(True)
        self.update()

    def set_mode(self, mode: str):
        self.current_mode = mode
        self.update_cursor()

    def set_cursor(self, cursor: Qt.CursorShape):
        super().setCursor(cursor)

    def set_image(self, image_path: str):
        self.pixmap = QPixmap(image_path)
        self.original_width = self.pixmap.width() if not self.pixmap.isNull() else 1
        self.original_height = self.pixmap.height() if not self.pixmap.isNull() else 1
        self.boxes = []
        self.selected_box_detection = None
        self.update()

    def add_box(self, detection: dict, label: str, color=QColor(0, 255, 255, 200)):
        if "visible" not in detection:
            detection["visible"] = True

        rect_coords = detection.get("bbox")
        if rect_coords and len(rect_coords) == 4:
            x1, y1, x2, y2 = rect_coords
            rect = QRect(int(x1), int(y1), int(x2 - x1), int(y2 - y1))
            self.boxes.append((rect, label, color, detection))
            self.update()

    def clear_boxes(self):
        """[FIX] implements the missing clear_boxes method."""
        self.boxes = []
        self.selected_box_detection = None
        self.update()

    def set_box_visibility(self, detection: dict, visible: bool):
        """Sets the visibility of a specific bounding box by its ID."""
        target_id = detection.get("id")
        if not target_id:
            return

        for i, (rect, label, color, stored_detection) in enumerate(self.boxes):
            if stored_detection.get("id") == target_id:
                stored_detection["visible"] = visible
                break

        if (
            self.selected_box_detection
            and self.selected_box_detection.get("id") == target_id
            and not visible
        ):
            self.set_selection(None)

        self.update()

    def set_selection(self, detection: dict):
        self.selected_box_detection = detection
        self.update()

    def get_geometry_helpers(self):
        if not self.pixmap or self.pixmap.isNull() or self.original_width <= 1:
            return None

        scaled_pixmap = self.pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x_offset = (self.width() - scaled_pixmap.width()) // 2
        y_offset = (self.height() - scaled_pixmap.height()) // 2
        scale_x = scaled_pixmap.width() / self.original_width if self.original_width > 0 else 0
        scale_y = scaled_pixmap.height() / self.original_height if self.original_height > 0 else 0

        return scaled_pixmap, x_offset, y_offset, scale_x, scale_y

    def get_scaled_rect(self, rect: QRect) -> QRect:
        geo = self.get_geometry_helpers()
        if not geo:
            return QRect()
        _, _, _, scale_x, scale_y = geo
        return QRect(
            int(rect.x() * scale_x),
            int(rect.y() * scale_y),
            int(rect.width() * scale_x),
            int(rect.height() * scale_y),
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        geo = self.get_geometry_helpers()

        if not geo:
            painter.fillRect(self.rect(), QColor(33, 37, 41))
            return

        scaled_pixmap, x_offset, y_offset, _, _ = geo
        painter.fillRect(self.rect(), QColor(33, 37, 41))
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)

        # Draw all boxes
        for rect, label, color, detection in self.boxes:
            if not detection.get("visible", True):
                continue

            is_selected = self.selected_box_detection and self.selected_box_detection.get(
                "id"
            ) == detection.get("id")

            pen_color = QColor(255, 255, 0) if is_selected else color
            pen_width = 3 if is_selected else 2

            scaled_rect = self.get_scaled_rect(rect)
            scaled_rect.translate(x_offset, y_offset)

            painter.setPen(QPen(pen_color, pen_width, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(scaled_rect)

            # Draw resize handles for selected box
            if is_selected:
                painter.setBrush(QColor(255, 255, 0))
                for handle in self._get_resize_handles(scaled_rect):
                    painter.drawRect(handle)

        # Draw the current drawing rectangle
        if self.is_drawing:
            draw_rect = QRect(self.draw_start_point, self.draw_end_point).normalized()
            painter.setPen(QPen(QColor(255, 0, 255), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(draw_rect)

    def _get_original_coords(self, point_on_widget: QPoint) -> QPoint:
        geo = self.get_geometry_helpers()
        if not geo:
            return QPoint()

        _, x_offset, y_offset, scale_x, scale_y = geo
        point_on_scaled = point_on_widget - QPoint(x_offset, y_offset)

        if scale_x == 0 or scale_y == 0:
            return QPoint()

        return QPoint(int(point_on_scaled.x() / scale_x), int(point_on_scaled.y() / scale_y))

    def _get_resize_handles(self, rect: QRect):
        size = 8
        h = size // 2
        return [
            QRect(rect.topLeft() - QPoint(h, h), QSize(size, size)),
            QRect(rect.topRight() - QPoint(h, h), QSize(size, size)),
            QRect(rect.bottomLeft() - QPoint(h, h), QSize(size, size)),
            QRect(rect.bottomRight() - QPoint(h, h), QSize(size, size)),
        ]

    def _get_handle_at_point(self, point: QPoint):
        if not self.selected_box_detection:
            return None

        x1, y1, x2, y2 = self.selected_box_detection["bbox"]
        rect = QRect(int(x1), int(y1), int(x2 - x1), int(y2 - y1))

        geo = self.get_geometry_helpers()
        if not geo:
            return None

        _, x_offset, y_offset, _, _ = geo
        scaled_rect = self.get_scaled_rect(rect)
        scaled_rect.translate(x_offset, y_offset)

        handles = self._get_resize_handles(scaled_rect)
        handle_names = ["top_left", "top_right", "bottom_left", "bottom_right"]

        for name, handle in zip(handle_names, handles):
            if handle.contains(point):
                return name

        if (
            self.selected_box_detection
            and self.selected_box_detection.get("visible", True)
            and scaled_rect.contains(point)
        ):
            return "move"

        return None

    def update_cursor(self, point=None):
        if self.current_mode == self.MODE_DRAW:
            self.setCursor(Qt.CrossCursor)
            return

        if self.is_dragging:
            return

        point = point or self.mapFromGlobal(QCursor.pos())
        handle = self._get_handle_at_point(point)

        if handle in ["top_left", "bottom_right"]:
            self.setCursor(Qt.SizeFDiagCursor)
        elif handle in ["top_right", "bottom_left"]:
            self.setCursor(Qt.SizeBDiagCursor)
        elif handle == "move":
            self.setCursor(Qt.SizeAllCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or not self.pixmap:
            return super().mousePressEvent(event)

        pos = event.position().toPoint()

        if self.current_mode == self.MODE_DRAW:
            self.is_drawing = True
            self.draw_start_point = pos
            self.draw_end_point = pos

        elif self.current_mode == self.MODE_SELECT:
            handle = self._get_handle_at_point(pos)
            if handle:
                self.is_dragging = True
                self.drag_start_point = pos
                self.drag_handle = handle

                # **[التعديل الرئيسي]**: عند بدء عملية تغيير الحجم، قم بحفظ الإحداثيات الأصلية
                # للركن المقابل (الذي لا يتحرك) لتثبيته كمرجع.
                if self.drag_handle in ["top_left", "top_right", "bottom_left", "bottom_right"]:
                    x1, y1, x2, y2 = self.selected_box_detection["bbox"]
                    current_rect = QRect(int(x1), int(y1), int(x2 - x1), int(y2 - y1))

                    if self.drag_handle == "top_left":
                        self.fixed_point = current_rect.bottomRight()
                    elif self.drag_handle == "top_right":
                        self.fixed_point = current_rect.bottomLeft()
                    elif self.drag_handle == "bottom_left":
                        self.fixed_point = current_rect.topRight()
                    elif self.drag_handle == "bottom_right":
                        self.fixed_point = current_rect.topLeft()

            else:
                clicked_detection = None
                orig_pos = self._get_original_coords(pos)
                for rect, _, _, detection in reversed(self.boxes):
                    if detection.get("visible", True) and rect.contains(orig_pos):
                        clicked_detection = detection
                        break
                if clicked_detection:
                    self.box_clicked.emit(clicked_detection)
                else:
                    self.set_selection(None)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()

        if not self.is_dragging and not self.is_drawing:
            self.update_cursor(pos)
            return super().mouseMoveEvent(event)

        if self.is_drawing:
            self.draw_end_point = pos

        elif self.is_dragging and self.selected_box_detection:
            if not self.selected_box_detection.get("visible", True):
                self.is_dragging = False
                self.drag_handle = None
                self.update_cursor(pos)
                return

            geo = self.get_geometry_helpers()
            if not geo:
                return
            _, _, _, scale_x, scale_y = geo
            if scale_x == 0 or scale_y == 0:
                return

            # **[التعديل الرئيسي]: تحويل النقطة الحالية إلى إحداثيات الصورة الأصلية**
            current_orig_pos = self._get_original_coords(pos)

            x1_orig, y1_orig, x2_orig, y2_orig = self.selected_box_detection["bbox"]

            if self.drag_handle == "move":
                # منطق الحركة: يعتمد على الفرق بين النقطة الحالية ونقطة البداية
                delta = pos - self.drag_start_point
                dx_orig = delta.x() / scale_x
                dy_orig = delta.y() / scale_y

                x1_orig += dx_orig
                y1_orig += dy_orig
                x2_orig += dx_orig
                y2_orig += dy_orig

                # تحديث نقطة البداية للسحب فقط في حالة الحركة
                self.drag_start_point = pos

            elif self.drag_handle in ["top_left", "top_right", "bottom_left", "bottom_right"]:
                # منطق تغيير الحجم: يعتمد على النقطة الحالية والنقطة الثابتة

                # استخدام النقطة الثابتة ونقطة الماوس الحالية لإنشاء مستطيل جديد
                new_rect = QRect(self.fixed_point, current_orig_pos).normalized()

                x1_orig, y1_orig = new_rect.topLeft().x(), new_rect.topLeft().y()
                x2_orig, y2_orig = new_rect.bottomRight().x(), new_rect.bottomRight().y()

            # Clamp coordinates to image bounds
            x_min = max(0.0, x1_orig)
            y_min = max(0.0, y1_orig)
            x_max = min(self.original_width, x2_orig)
            y_max = min(self.original_height, y2_orig)

            if x_max > x_min and y_max > y_min:
                # التأكد من عدم تجاوز نقطة الحد (الحركة)
                new_width = x_max - x_min
                new_height = y_max - y_min

                # للحركة فقط: التأكد من عدم خروج البوكس عن الصورة
                if self.drag_handle == "move":
                    x1_final = x_min
                    y1_final = y_min
                    x2_final = x_min + new_width
                    y2_final = y_min + new_height
                else:
                    # لتغيير الحجم: استخدام X_min/Y_min كنقطة علوية يسارية و X_max/Y_max كنقطة سفلية يمينية
                    x1_final = x_min
                    y1_final = y_min
                    x2_final = x_max
                    y2_final = y_max

                self.selected_box_detection["bbox"] = (x1_final, y1_final, x2_final, y2_final)

                # Update the bounding box in the self.boxes list
                for i, (rect, label, color, detection) in enumerate(self.boxes):
                    if detection.get("id") == self.selected_box_detection.get("id"):
                        new_qrect = QRect(
                            int(x1_final),
                            int(y1_final),
                            int(x2_final - x1_final),
                            int(y2_final - y1_final),
                        )
                        self.boxes[i] = (new_qrect, label, color, detection)
                        break

                self.box_modified.emit(self.selected_box_detection)
            else:
                self.is_dragging = False
                self.drag_handle = None

        self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mouseReleaseEvent(event)

        if self.is_drawing:
            self.is_drawing = False
            start_orig = self._get_original_coords(self.draw_start_point)
            end_orig = self._get_original_coords(self.draw_end_point)
            new_rect = QRect(start_orig, end_orig).normalized()

            x_min = max(0, new_rect.left())
            y_min = max(0, new_rect.top())
            x_max = min(self.original_width, new_rect.right())
            y_max = min(self.original_height, new_rect.bottom())

            final_rect = QRect(x_min, y_min, x_max - x_min, y_max - y_min).normalized()

            if final_rect.width() > 5 and final_rect.height() > 5:
                self.new_box_drawn.emit(final_rect)

        self.is_dragging = False
        self.drag_handle = None
        # **[إضافة]**: مسح النقطة الثابتة بعد الانتهاء من تغيير الحجم
        if hasattr(self, "fixed_point"):
            del self.fixed_point
        self.update()
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()
