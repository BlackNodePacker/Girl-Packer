import os
import uuid
import cv2
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QGroupBox,
    QListWidgetItem,
    QMessageBox,
    QRadioButton,
    QCheckBox,
    QComboBox,
    QApplication,
    QGridLayout,
    QInputDialog,
    QFrame,
    QToolBar,
)
from PySide6.QtCore import Qt, Signal, QSize, QRect
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QAction

try:
    import qtawesome as qta

    QTAWESOME_LOADED = True
except ImportError:
    QTAWESOME_LOADED = False

from .image_viewer_widget import ImageViewerWidget
from utils.file_ops import sanitize_filename, ensure_folder
from tools.logger import get_logger

logger = get_logger("ImageWorkshopPanel")


class LayerItemWidget(QWidget):
    visibility_changed = Signal(dict, bool)
    delete_requested = Signal(QListWidgetItem)

    def __init__(self, detection, color, item_ref):
        super().__init__()
        self.item_ref = item_ref
        self.detection = detection
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        x1, y1, x2, y2 = detection.get("bbox", [0, 0, 0, 0])
        box_text = f" ({int(x1)}, {int(y1)}) - ({int(x2)}, {int(y2)})"

        confidence_text = (
            f" ({int(detection.get('confidence', 0) * 100)}%)"
            if "confidence" in detection and detection.get("confidence", 0) < 1.0
            else ""
        )
        self.label = QLabel(f"[{detection['label']}]{confidence_text} {box_text}")

        color_label = QLabel("■")
        color_label.setStyleSheet(f"color: {color.name()}; font-size: 16px;")

        delete_button = QPushButton("X")
        delete_button.setFixedSize(24, 24)
        delete_button.setObjectName("SmallDeleteButton")

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(color_label)
        layout.addWidget(delete_button)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        layout.insertWidget(0, self.checkbox)

        self.checkbox.stateChanged.connect(
            lambda state: self.visibility_changed.emit(
                self.detection, state == Qt.CheckState.Checked
            )
        )
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.item_ref))

    def set_checked(self, is_checked):
        self.checkbox.setChecked(is_checked)

    def update_text(self, new_bbox):
        """Updates the coordinate text when the box is modified."""
        x1, y1, x2, y2 = [int(c) for c in new_bbox]
        confidence_text = (
            f" ({int(self.detection.get('confidence', 0) * 100)}%)"
            if self.detection.get("confidence", 0) < 1.0
            else ""
        )
        box_text = f" ({x1}, {y1}) - ({x2}, {y2})"
        self.label.setText(f"[{self.detection['label']}]{confidence_text} {box_text}")


class ImageWorkshopPanel(QWidget):
    back_requested = Signal()
    # [FIX] يجب أن تكون الإشارة بدون تحديد نوع البيانات هنا (للسلامة)
    processing_requested = Signal(dict)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.yolo_labels = self.main_window.pipeline.yolo_model.class_names if self.main_window.pipeline.yolo_model else []
        self.yolo_results_cache = {}
        # [FIX] تغيير اسم البفر ليعكس أنه يمسك البيانات لكل إطار
        self.frame_tag_buffer = {}  # Key: frame_path, Value: list of tagged_items
        self.frame_paths = []
        self.current_frame_index = -1
        self.current_frame_path = None
        self.current_selected_detection = None
        self.current_source_key = "unknown"

        self.color_map = {
            "person": QColor(220, 220, 220, 100),
            "face": QColor(52, 152, 219, 200),
            "boobs": QColor(230, 126, 34, 200),
            "pussy": QColor(142, 68, 173, 200),
            "ass": QColor(243, 156, 18, 200),
            "bra": QColor(231, 76, 60, 200),
            "panty": QColor(155, 89, 182, 200),
            "default": QColor(0, 255, 255, 150),
        }
        self.init_colors_from_yolo()

        self._setup_ui()
        self._connect_signals()

    def init_colors_from_yolo(self):
        for label in self.yolo_labels:
            if label not in self.color_map:
                r = (hash(label) * 10) % 255
                g = (hash(label) * 50) % 255
                b = (hash(label) * 100) % 255
                self.color_map[label] = QColor(r, g, b, 150)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        title = QLabel("🎨 Image Workshop & YOLO Studio")
        title.setObjectName("TitleLabel")
        main_layout.addWidget(title)

        main_hbox = QHBoxLayout()

        center_panel = QGroupBox("Editor")
        center_layout = QVBoxLayout(center_panel)

        self.yolo_toolbar = QToolBar("YOLO Editor Toolbar")
        self.yolo_toolbar.setIconSize(QSize(24, 24))

        self.select_mode_action = self._create_action(
            "fa5s.mouse-pointer", "Select/Move Tool", self._on_select_mode_clicked, True
        )
        self.draw_mode_action = self._create_action(
            "fa5s.edit", "Draw New Box", self._on_draw_mode_clicked, True
        )
        self.delete_action = self._create_action(
            "fa5s.trash-alt", "Delete Selected Box", self._on_delete_clicked
        )

        self.yolo_toolbar.addAction(self.select_mode_action)
        self.yolo_toolbar.addAction(self.draw_mode_action)
        self.yolo_toolbar.addSeparator()
        self.yolo_toolbar.addAction(self.delete_action)

        center_layout.addWidget(self.yolo_toolbar)
        self.image_viewer = ImageViewerWidget()
        center_layout.addWidget(self.image_viewer)
        main_hbox.addWidget(center_panel, 5)

        right_panel = QGroupBox("Tagging Studio")
        self.details_layout = QVBoxLayout(right_panel)
        self._setup_details_panel()
        main_hbox.addWidget(right_panel, 3)

        main_layout.addLayout(main_hbox)

        bottom_bar = QHBoxLayout()
        # [NEW] إضافة أزرار التنقل
        self.prev_frame_button = QPushButton("◀️ Previous")
        self.next_frame_button = QPushButton("Next ▶️")
        self.frame_counter_label = QLabel("Frame: 0/0")

        back_button = QPushButton("⬅️ Back")
        self.confirm_all_button = QPushButton("✔️ Confirm All & Finalize")
        self.confirm_all_button.setObjectName("ConfirmButton")

        bottom_bar.addWidget(back_button)
        bottom_bar.addSpacing(20)
        bottom_bar.addWidget(self.prev_frame_button)
        bottom_bar.addWidget(self.frame_counter_label)
        bottom_bar.addWidget(self.next_frame_button)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.confirm_all_button)
        main_layout.addLayout(bottom_bar)

        back_button.clicked.connect(self.back_requested.emit)

    def _create_action(self, icon_name, tooltip, slot, checkable=False):
        icon = qta.icon(icon_name) if QTAWESOME_LOADED else QPixmap()
        action = QAction(icon, tooltip, self)
        action.setToolTip(tooltip)
        action.triggered.connect(slot)
        action.setCheckable(checkable)
        return action

    def _setup_details_panel(self):
        layers_group = QGroupBox("Detected Layers")
        layers_layout = QVBoxLayout(layers_group)
        self.layers_list_widget = QListWidget()
        self.layers_list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layers_layout.addWidget(self.layers_list_widget)
        self.details_layout.addWidget(layers_group, 1)

        self.suggestion_group = QGroupBox("Selected Item Details")
        self.suggestion_group.hide()
        suggestion_layout = QGridLayout(self.suggestion_group)

        suggestion_layout.addWidget(QLabel("<b>YOLO Type:</b>"), 0, 0)
        self.yolo_override_combo = QComboBox()
        self.yolo_override_combo.addItems(sorted(self.yolo_labels))
        suggestion_layout.addWidget(self.yolo_override_combo, 0, 1)

        suggestion_layout.addWidget(QLabel("<b>Base Type:</b>"), 1, 0)
        self.base_type_combo = QComboBox()
        suggestion_layout.addWidget(self.base_type_combo, 1, 1)

        suggestion_layout.addWidget(QLabel("<b>Sub-Type:</b>"), 2, 0)
        self.subtype_combo = QComboBox()
        suggestion_layout.addWidget(self.subtype_combo, 2, 1)

        state_group = QGroupBox("State Modifiers (Suffixes)")
        state_layout = QVBoxLayout(state_group)

        corruption_layout = QHBoxLayout()
        corruption_layout.addWidget(QLabel("Corruption (-):"))
        self.corruption_radios = {}
        radio_none = QRadioButton("None")
        radio_none.setChecked(True)
        corruption_layout.addWidget(radio_none)
        self.corruption_radios[""] = radio_none

        for name, tag in (
            self.main_window.tag_manager.get_vid_tags().get("corruption_level", {}).items()
        ):
            radio = QRadioButton(name.split("(")[0])
            self.corruption_radios[tag] = radio
            corruption_layout.addWidget(radio)
        state_layout.addLayout(corruption_layout)

        suffix_layout = QHBoxLayout()
        self.cum_checkbox = QCheckBox("_cum")
        self.creampie_checkbox = QCheckBox("_creampie")
        suffix_layout.addWidget(self.cum_checkbox)
        suffix_layout.addWidget(self.creampie_checkbox)
        suffix_layout.addStretch()
        state_layout.addLayout(suffix_layout)

        suggestion_layout.addWidget(state_group, 3, 0, 1, 2)

        self.confirm_item_button = QPushButton("✔️ Confirm Item")
        self.confirm_item_button.setObjectName("AddButton")
        suggestion_layout.addWidget(self.confirm_item_button, 4, 0, 1, 2)

        self.details_layout.addWidget(self.suggestion_group, 2)
        self.details_layout.addStretch(1)

    def _connect_signals(self):
        self.confirm_all_button.clicked.connect(self._check_and_finish_workshop)
        self.image_viewer.box_clicked.connect(self._on_box_clicked)
        self.layers_list_widget.itemClicked.connect(
            lambda item: self._on_box_clicked(item.data(Qt.UserRole))
        )
        self.confirm_item_button.clicked.connect(self._confirm_current_item)

        self.yolo_override_combo.currentTextChanged.connect(self._on_yolo_override_changed)
        self.base_type_combo.currentTextChanged.connect(self._on_base_type_changed)
        self.image_viewer.new_box_drawn.connect(self._on_new_box_drawn)
        self.image_viewer.box_modified.connect(self._handle_box_modified_in_viewer)

        # [NEW CONNECTION]
        self.prev_frame_button.clicked.connect(self._load_previous_frame)
        self.next_frame_button.clicked.connect(self._load_next_frame)

    def _update_list_item_text(self, detection_id, new_bbox=None):
        for i in range(self.layers_list_widget.count()):
            item = self.layers_list_widget.item(i)
            det = item.data(Qt.UserRole)
            if det and det.get("id") == detection_id:
                widget = self.layers_list_widget.itemWidget(item)
                if widget and new_bbox:
                    widget.update_text(new_bbox)
                    det["bbox"] = new_bbox
                    item.setData(Qt.UserRole, det)
                return

    def _handle_box_modified_in_viewer(self, detection: dict):
        detection_id = detection.get("id")
        new_bbox = detection.get("bbox")

        if detection_id and new_bbox:
            path = self.current_frame_path
            detections = self.yolo_results_cache.get(path, {}).get('detections', [])

            for d in detections:
                if d.get("id") == detection_id:
                    d["bbox"] = new_bbox
                    d["manual"] = True
                    break

            self._update_list_item_text(detection_id, new_bbox)
            logger.info(f"Box ID {detection_id} modified and cache/list updated.")

    def _on_layer_item_delete_requested(self, item_to_delete: QListWidgetItem):
        detection_to_delete = item_to_delete.data(Qt.UserRole)
        if detection_to_delete:
            reply = QMessageBox.question(
                self, "Confirm Delete", "Are you sure you want to delete this box?"
            )
            if reply == QMessageBox.StandardButton.Yes:
                path = self.current_frame_path
                detections = self.yolo_results_cache.get(path, {}).get('detections', [])
                id_to_delete = detection_to_delete.get("id")

                if id_to_delete:
                    # إزالة من قائمة YOLO الأصلية
                    self.yolo_results_cache[path]['detections'] = [
                        d for d in detections if d.get("id") != id_to_delete
                    ]

                    # إزالة من قائمة Tags المؤكدة
                    if path in self.frame_tag_buffer:
                        self.frame_tag_buffer[path] = [
                            item
                            for item in self.frame_tag_buffer[path]
                            if item["yolo_detection"].get("id") != id_to_delete
                        ]

                    logger.info(f"Deleted box from layer list: {detection_to_delete['label']}")

                    self.current_selected_detection = None
                    self.suggestion_group.hide()
                    self._display_current_frame()
                    self.image_viewer.set_selection(None)

    def _on_select_mode_clicked(self):
        self.image_viewer.set_mode(self.image_viewer.MODE_SELECT)
        self.draw_mode_action.setChecked(False)
        self.select_mode_action.setChecked(True)

    def _on_draw_mode_clicked(self):
        self.image_viewer.set_mode(self.image_viewer.MODE_DRAW)
        self.select_mode_action.setChecked(False)
        self.draw_mode_action.setChecked(True)

    def _on_delete_clicked(self):
        if not self.current_selected_detection:
            QMessageBox.warning(self, "No Selection", "Please select a box to delete first.")
            return

        detection_id = self.current_selected_detection.get("id")

        if detection_id:
            path = self.current_frame_path
            detections = self.yolo_results_cache.get(path, {}).get('detections', [])

            # إزالة من قائمة YOLO الأصلية
            self.yolo_results_cache[path]['detections'] = [d for d in detections if d.get("id") != detection_id]

            # إزالة من قائمة Tags المؤكدة
            if path in self.frame_tag_buffer:
                self.frame_tag_buffer[path] = [
                    item
                    for item in self.frame_tag_buffer[path]
                    if item["yolo_detection"].get("id") != detection_id
                ]

            logger.info(f"Deleted box via toolbar: {self.current_selected_detection['label']}")
            self.current_selected_detection = None
            self.suggestion_group.hide()
            self._display_current_frame()
            self.image_viewer.set_selection(None)
        else:
            QMessageBox.warning(
                self, "Error", "Could not find the selected item in the list to delete."
            )

    def _on_new_box_drawn(self, rect: QRect):
        logger.info(f"New box drawn at coordinates: {rect.getCoords()}")

        labels = sorted(self.yolo_labels)
        label, ok = QInputDialog.getItem(
            self, "New Box", "Select a label for the new box:", labels, 0, False
        )

        if ok and label:
            new_detection = {
                "id": str(uuid.uuid4()),
                "bbox": [float(c) for c in rect.getCoords()],
                "label": label,
                "confidence": 1.0,
                "manual": True,
            }
            # يجب التأكد من وجود current_frame_path في cache
            if self.current_frame_path not in self.yolo_results_cache:
                self.yolo_results_cache[self.current_frame_path] = {'detections': [], 'label_path': None}

            self.yolo_results_cache[self.current_frame_path]['detections'].append(new_detection)

            self._display_current_frame()
            self._on_box_clicked(new_detection)

        self._on_select_mode_clicked()

    def load_data(self, frame_paths, yolo_results, tasks):
        self.yolo_results_cache = yolo_results
        self.frame_tag_buffer = {path: [] for path in frame_paths}  # إعادة تهيئة البفر لكل إطار
        self.frame_paths = frame_paths
        self.current_frame_index = 0

        if self.frame_paths:
            self._display_current_frame()

        self._on_select_mode_clicked()

    def _load_previous_frame(self):
        if self.current_frame_index > 0:
            self.current_frame_index -= 1
            self._display_current_frame()

    def _load_next_frame(self):
        if self.current_frame_index < len(self.frame_paths) - 1:
            self.current_frame_index += 1
            self._display_current_frame()

    def _display_current_frame(self):
        if not (0 <= self.current_frame_index < len(self.frame_paths)):
            # This case should typically be handled by _check_and_finish_workshop
            self.frame_counter_label.setText("Frame: 0/0")
            self.prev_frame_button.setEnabled(False)
            self.next_frame_button.setEnabled(False)
            return

        self.current_frame_path = self.frame_paths[self.current_frame_index]
        self.image_viewer.set_image(self.current_frame_path)
        self.suggestion_group.hide()
        self.layers_list_widget.clear()
        self.current_selected_detection = None

        self.frame_counter_label.setText(
            f"Frame: {self.current_frame_index + 1}/{len(self.frame_paths)}"
        )
        self.prev_frame_button.setEnabled(self.current_frame_index > 0)
        self.next_frame_button.setEnabled(self.current_frame_index < len(self.frame_paths) - 1)

        detections = self.yolo_results_cache.get(self.current_frame_path, {}).get('detections', [])
        self.image_viewer.clear_boxes()

        for det in detections:
            if "id" not in det:
                det["id"] = str(uuid.uuid4())

            color = self.color_map.get(det["label"], self.color_map["default"])
            self.image_viewer.add_box(det, det["label"], color)

            item = QListWidgetItem()
            widget = LayerItemWidget(det, color, item)
            widget.visibility_changed.connect(self.image_viewer.set_box_visibility)
            widget.delete_requested.connect(self._on_layer_item_delete_requested)

            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.UserRole, det)

            self.layers_list_widget.addItem(item)
            self.layers_list_widget.setItemWidget(item, widget)

            # [FIX] التحقق مما إذا كان قد تم تأكيد هذا العنصر سابقًا لجعله محدداً في القائمة
            is_confirmed = next(
                (
                    True
                    for item in self.frame_tag_buffer.get(self.current_frame_path, [])
                    if item["yolo_detection"].get("id") == det["id"]
                ),
                False,
            )
            widget.set_checked(True)  # دائماً نجعله مرئياً
            if is_confirmed:
                item.setBackground(QColor(150, 255, 150, 50))  # إشارة مرئية للعناصر المؤكدة

    def _on_box_clicked(self, detection: dict):

        self.current_selected_detection = detection
        self.image_viewer.set_selection(detection)
        self.suggestion_group.show()

        current_yolo_label = detection.get("label", "unknown")
        options = sorted(self.yolo_labels)
        if current_yolo_label in options:
            options.remove(current_yolo_label)
        options.insert(0, current_yolo_label)

        self.yolo_override_combo.blockSignals(True)
        self.yolo_override_combo.clear()
        self.yolo_override_combo.addItems(options)
        self.yolo_override_combo.setCurrentText(current_yolo_label)
        self.yolo_override_combo.blockSignals(False)

        cnn_suggestion = "---"
        try:
            full_image = cv2.imread(self.current_frame_path)
            x1, y1, x2, y2 = [int(c) for c in detection["bbox"]]
            cropped_image = full_image[y1:y2, x1:x2]

            # التأكد من صحة التنسيق هنا
            if (
                cropped_image.size > 0
                and hasattr(self.main_window.pipeline, "classify_asset")
                and self.main_window.pipeline.classify_asset
            ):
                cnn_suggestion = self.main_window.pipeline.classify_asset(cropped_image)

            logger.info(f"CNN suggested: '{cnn_suggestion}' for YOLO label '{current_yolo_label}'")
        except Exception as e:
            logger.error(f"CNN classification failed: {e}")

        self._on_yolo_override_changed(
            current_yolo_label, cnn_suggestion_for_base_type=cnn_suggestion
        )

        self._load_existing_tags(detection)

    def _load_existing_tags(self, detection_data: dict):

        self._reset_tagging_ui()

        detection_id = detection_data.get("id")

        tagged_item = next(
            (
                item
                for item in self.frame_tag_buffer.get(self.current_frame_path, [])
                if item["yolo_detection"].get("id") == detection_id
            ),
            None,
        )

        if tagged_item:
            logger.info(
                f"Loading existing tags for ID {detection_id}: {tagged_item.get('final_name')}"
            )

            # [FIX] يجب تحديث الـ YOLO Override Combo أولاً إذا كان التاغ موجوداً
            yolo_override_label = tagged_item.get(
                "yolo_label_override", detection_data.get("label")
            )

            # لإعادة تحميل القوائم المنسدلة بناءً على التاغ المحفوظ
            self._on_yolo_override_changed(yolo_override_label)

            base_idx = self.base_type_combo.findText(tagged_item.get("base_type"))
            if base_idx >= 0:
                self.base_type_combo.setCurrentIndex(base_idx)

                final_class_tag = tagged_item.get("final_class_tag")
                if self.current_source_key == "clothing":
                    source_map = self.main_window.tag_manager.get_clothing_map().get(
                        tagged_item.get("base_type"), {}
                    )
                    # البحث عن مفتاح القاموس باستخدام القيمة (final_class_tag)
                    final_class_text_lookup = next(
                        (k for k, v in source_map.items() if v == final_class_tag), final_class_tag
                    )
                else:
                    final_class_text_lookup = final_class_tag

                sub_idx = self.subtype_combo.findText(final_class_text_lookup)
                if sub_idx >= 0:
                    self.subtype_combo.setCurrentIndex(sub_idx)

                final_name = tagged_item.get("final_name", "").lower()

                state_match = next(
                    (
                        tag
                        for tag in self.corruption_radios.keys()
                        if tag and f"-{tag}" in final_name
                    ),
                    None,
                )
                if state_match and state_match in self.corruption_radios:
                    self.corruption_radios[state_match].setChecked(True)
                else:
                    self.corruption_radios[""].setChecked(True)

                self.cum_checkbox.setChecked("_cum" in final_name)
                self.creampie_checkbox.setChecked("_creampie" in final_name)
        else:
            self._reset_tagging_ui()

    def _reset_tagging_ui(self):
        # [FIX] يجب أن نعيد ضبط الـ Base Type فقط بعد تحميل البيانات
        # self.base_type_combo.setCurrentIndex(0)
        self.subtype_combo.clear()

        for tag, radio in self.corruption_radios.items():
            if tag == "":
                radio.setChecked(True)
            else:
                radio.setChecked(False)

        self.cum_checkbox.setChecked(False)
        self.creampie_checkbox.setChecked(False)

    def _on_yolo_override_changed(self, new_label, cnn_suggestion_for_base_type=None):
        tm = self.main_window.tag_manager
        source_map, self.current_source_key = {}, "unknown"

        if new_label in ["person"] or new_label.startswith("fullbody"):
            source_map, self.current_source_key = tm.get_fullbody_map(), "fullbody"
        elif new_label.startswith("portrait") or new_label in [
            "face",
            "boobs",
            "pussy",
            "ass",
            "legs",
        ]:
            source_map, self.current_source_key = tm.get_bodyparts_map(), "bodypart"
        else:
            source_map, self.current_source_key = tm.get_clothing_map(), "clothing"

        self.base_type_combo.blockSignals(True)
        self.base_type_combo.clear()
        base_types = ["---"] + list(source_map.keys())
        self.base_type_combo.addItems(base_types)

        if cnn_suggestion_for_base_type and cnn_suggestion_for_base_type in source_map:
            self.base_type_combo.setCurrentText(cnn_suggestion_for_base_type)

        self.base_type_combo.blockSignals(False)
        self._on_base_type_changed(self.base_type_combo.currentText())

    def _on_base_type_changed(self, base_type_text):
        self.subtype_combo.blockSignals(True)
        self.subtype_combo.clear()
        self.subtype_combo.addItems(["---"])

        if base_type_text and base_type_text != "---":
            tm = self.main_window.tag_manager
            source_map = {}

            if self.current_source_key == "fullbody":
                source_map = tm.get_fullbody_map()
            elif self.current_source_key == "bodypart":
                source_map = tm.get_bodyparts_map()
            elif self.current_source_key == "clothing":
                source_map = tm.get_clothing_map()

            subtypes_data = source_map.get(base_type_text, {})

            if isinstance(subtypes_data, dict):
                # نأخذ المفاتيح كنصوص العرض
                self.subtype_combo.addItems(list(subtypes_data.keys()))
            elif isinstance(subtypes_data, list):
                self.subtype_combo.addItems(subtypes_data)

        self.subtype_combo.blockSignals(False)

    def _confirm_current_item(self):
        try:
            from utils.file_ops import sanitize_filename
        except ImportError:
            pass

        if not self.current_selected_detection or self.subtype_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Incomplete", "Please select a valid Sub-Type.")
            return

        base_type_text = self.base_type_combo.currentText()
        final_class_text = self.subtype_combo.currentText()

        tm = self.main_window.tag_manager
        final_class_tag = ""
        base_type_tag = ""

        # [NEW] إضافة هذين المتغيرين لتمريرهما إلى الـ FinalProcessorWorker
        final_class = ""
        asset_category = self.current_source_key  # 'clothing', 'bodypart', 'fullbody'

        if self.current_source_key == "clothing":
            source_map = tm.get_clothing_map()

            yolo_label_for_sizing = self.current_selected_detection.get(
                "label", "default_asset"
            ).lower()
            base_type_tag = yolo_label_for_sizing  # للاستخدام في تحديد مقاسات الصور (Resize)

            final_class_tag = source_map.get(base_type_text, {}).get(final_class_text)
            final_class = f"{base_type_text}_{final_class_text.replace(' ', '_').lower()}"  # لاسم مجلد التدريب

        elif self.current_source_key in ["bodypart", "fullbody"]:
            if self.current_source_key == "fullbody":
                source_map = tm.get_fullbody_map()
            else:
                source_map = tm.get_bodyparts_map()

            base_type_tag = base_type_text
            final_class_tag = final_class_text
            final_class = final_class_text  # لاسم مجلد التدريب

        if not final_class_tag:
            QMessageBox.critical(
                self,
                "Tag Error",
                f"Could not determine final tag for {base_type_text} / {final_class_text}",
            )
            return

        final_tag_parts = [final_class_tag]

        corruption_tag = next(
            (tag for tag, radio in self.corruption_radios.items() if radio.isChecked()), ""
        )
        if corruption_tag:
            final_tag_parts.append(f"-{corruption_tag}")

        if self.cum_checkbox.isChecked():
            final_tag_parts.append("_cum")
        if self.creampie_checkbox.isChecked():
            final_tag_parts.append("_creampie")

        final_name_tag = "".join(final_tag_parts)

        cover_type = None
        body_part_cover = None

        # [NEW LOGIC] حساب Cover Type و Body Part Cover
        if self.current_source_key == "clothing":
            # تحديد cover_type
            tag_root = final_class_tag.split("_")[-1]
            if tag_root in ["thong", "panties", "briefs", "panty"]:
                cover_type = "panties"
            elif tag_root in ["bra", "sportbra", "bikinitop"]:
                cover_type = "bra"
            elif tag_root in ["shirt", "tanktop", "dress", "swimsuit_onepiece"]:
                cover_type = "upper"
            elif tag_root in ["shorts", "skirts", "jeans", "trousers"]:
                cover_type = "lower"
            else:
                cover_type = "clothing_misc"

            # تحديد body_part_cover بناءً على ما يغطيه
            if "boobs" in base_type_text.lower() or "bra" in cover_type:
                body_part_cover = "boobs_cover"
            elif "pussy" in base_type_text.lower() or "panties" in cover_type:
                body_part_cover = "pussy_cover"
            elif "ass" in base_type_text.lower():
                body_part_cover = "ass_cover"

        elif self.current_source_key == "bodypart":
            cover_type = base_type_tag
            body_part_cover = f"{base_type_tag}_cover"

        if not cover_type:
            cover_type = "misc"
        if not body_part_cover:
            body_part_cover = "default_cover"

        new_tagged_item = {
            "yolo_detection": self.current_selected_detection,
            "base_type": base_type_text,
            "final_class_tag": final_class_tag,
            "final_name": final_name_tag,
            "yolo_label_override": self.yolo_override_combo.currentText(),
            "cover_type": cover_type,
            "body_part_cover": body_part_cover,
            # [NEW ADDITION] إضافة هذه البيانات لعملية المعالجة النهائية
            "final_class": final_class,
            "asset_category": asset_category,
            "base_type_tag": base_type_tag,
        }

        logger.info(
            f"Confirmed Item. Tag: {new_tagged_item['final_name']}, Category: {asset_category}"
        )

        current_path = self.current_frame_path
        if current_path not in self.frame_tag_buffer:
            self.frame_tag_buffer[current_path] = []

        detection_id = self.current_selected_detection.get("id")

        # استبدال العنصر القديم إذا كان موجوداً
        self.frame_tag_buffer[current_path] = [
            item
            for item in self.frame_tag_buffer[current_path]
            if item["yolo_detection"].get("id") != detection_id
        ]

        self.frame_tag_buffer[current_path].append(new_tagged_item)

        QMessageBox.information(self, "Confirmed", f"Item confirmed with tag: {final_name_tag}")

        # [FIX] نحدد العنصر في القائمة كـ مؤكد
        for i in range(self.layers_list_widget.count()):
            item = self.layers_list_widget.item(i)
            det = item.data(Qt.UserRole)
            if det and det.get("id") == detection_id:
                item.setBackground(QColor(150, 255, 150, 50))
                break

        self.current_selected_detection = None
        self.suggestion_group.hide()
        self.image_viewer.set_selection(None)

    def _check_and_finish_workshop(self):

        # [FIX] يجب أن تكون بنية البيانات المرسلة هي: {frame_path: [list_of_instructions], ...}
        # كما يتوقعها FinalProcessorWorker
        final_payload = {}
        missing_tags_count = 0

        for path in self.frame_paths:
            yolo_dets = self.yolo_results_cache.get(path, {}).get('detections', [])
            confirmed_tags = self.frame_tag_buffer.get(path, [])

            # حساب عدد الاكتشافات التي لم يتم تأكيدها بعد
            confirmed_ids = {item["yolo_detection"]["id"] for item in confirmed_tags}
            unconfirmed_count = len(
                [det for det in yolo_dets if det.get("id") not in confirmed_ids]
            )
            missing_tags_count += unconfirmed_count

            # إضافة التعليمات المؤكدة فقط إلى الـ payload
            if confirmed_tags:
                final_payload[path] = confirmed_tags

        if missing_tags_count > 0:
            reply = QMessageBox.question(
                self,
                "Unconfirmed Items",
                f"There are **{missing_tags_count}** remaining YOLO boxes that you haven't confirmed/tagged. Do you want to proceed with only the confirmed items?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        if not final_payload:
            QMessageBox.warning(self, "No Items", "No items have been confirmed. Cannot finalize.")
            return

        # إرسال البيانات بالصيغة الصحيحة
        self.processing_requested.emit(final_payload)
        if hasattr(self.main_window, 'show_processing_screen'):
            self.main_window.show_processing_screen()
        else:
            logger.warning("show_processing_screen method not found in MainWindow")
