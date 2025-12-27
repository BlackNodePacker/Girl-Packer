# GameMediaTool/gui/components/vid_tagger_panel.py (MODIFIED to use unified JSONs for location)

import os
import shutil
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QLineEdit,
    QGroupBox,
    QMessageBox,
    QGridLayout,
    QListWidgetItem,
    QComboBox,
    QCheckBox,
    QAbstractItemView,
    QFrame,
)
from PySide6.QtCore import Qt, Signal

from .player_widget import PlayerWidget
from tools.logger import get_logger
from utils.file_ops import sanitize_filename

logger = get_logger("VidTaggerPanel_Final")


class VidTaggerPanel(QWidget):
    back_requested = Signal()
    export_requested = Signal(dict)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.clips_to_process = []
        self.clips_data = {}

        tm = main_window.tag_manager
        self.vid_tag_options = tm.get_vid_tags()
        # [MODIFIED] Get the new unified shoot tags file for locations
        self.shoots_tags = tm.get_shoots_tags()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        preview_hbox = QHBoxLayout()
        clips_group = QGroupBox("Files to Tag")
        clips_layout = QVBoxLayout(clips_group)
        self.clips_list_widget = QListWidget()
        self.clips_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        clips_layout.addWidget(self.clips_list_widget)
        preview_hbox.addWidget(clips_group, 1)
        self.preview_player = PlayerWidget()
        preview_hbox.addWidget(self.preview_player, 2)
        main_layout.addLayout(preview_hbox)

        tag_lists_hbox = QHBoxLayout()
        main_tags_group, self.main_tags_list = self._create_tag_list_widget(
            "Main Tags", self.vid_tag_options.get("main_tags", {})
        )
        clothing_main_tags_group, self.clothing_main_tags_list = self._create_tag_list_widget(
            "Clothing Based Main Tags", self.vid_tag_options.get("clothing_based_main_tags", {})
        )
        clothing_tags_group, self.clothing_tags_list = self._create_tag_list_widget(
            "Clothing Tags", self.vid_tag_options.get("clothing_tags", {})
        )

        tag_lists_hbox.addWidget(main_tags_group)
        tag_lists_hbox.addWidget(clothing_main_tags_group)
        tag_lists_hbox.addWidget(clothing_tags_group)

        toggles_group = QGroupBox("Modifiers")
        toggles_vbox = QVBoxLayout(toggles_group)
        self.reset_tags_check = QCheckBox("Reset tags after applying")
        self.only_suffix_check = QCheckBox("_only suffix")
        self.not_prefix_check = QCheckBox("not_ prefix")
        self.orgasm_suffix_check = QCheckBox("_orgasm suffix")
        self.female_prefix_check = QCheckBox("female_ prefix")
        self.lesbian_prefix_check = QCheckBox("lesbian_ prefix")
        for check in [
            self.reset_tags_check,
            self.only_suffix_check,
            self.not_prefix_check,
            self.orgasm_suffix_check,
            self.female_prefix_check,
            self.lesbian_prefix_check,
        ]:
            toggles_vbox.addWidget(check)
        toggles_vbox.addStretch()
        tag_lists_hbox.addWidget(toggles_group)
        main_layout.addLayout(tag_lists_hbox)

        bottom_grid = QGridLayout()
        corruption_widget, self.corruption_combo = self._create_combo(
            "Corruption:", [""] + list(self.vid_tag_options.get("corruption_level", {}).keys())
        )
        participants_widget, self.participants_combo = self._create_combo(
            "Participants:", [""] + list(self.vid_tag_options.get("participants", {}).keys())
        )
        # [MODIFIED] Populate location combo from the new unified source
        location_widget, self.location_combo = self._create_combo(
            "Location:", [""] + list(self.shoots_tags.get("location_tags", {}).keys())
        )

        bottom_grid.addWidget(corruption_widget, 0, 0)
        bottom_grid.addWidget(participants_widget, 0, 1)
        bottom_grid.addWidget(location_widget, 1, 0)
        main_layout.addLayout(bottom_grid)

        self.filename_preview = QLineEdit("Filename preview...")
        self.filename_preview.setReadOnly(True)
        main_layout.addWidget(self.filename_preview)

        button_hbox = QHBoxLayout()
        self.back_button = QPushButton("⬅️ Back")
        self.apply_button = QPushButton("Apply Tags to Selected")
        self.export_button = QPushButton("✔️ Finalize & Save to Project")
        self.export_button.setObjectName("ConfirmButton")
        button_hbox.addWidget(self.back_button)
        button_hbox.addStretch()
        button_hbox.addWidget(self.apply_button)
        button_hbox.addWidget(self.export_button)
        main_layout.addLayout(button_hbox)

    def _create_tag_list_widget(self, title, data):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        for category, items in data.items():
            cat_item = QListWidgetItem(f"=={category}==")
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            list_widget.addItem(cat_item)
            for name, tag in items.items():
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, tag)
                list_widget.addItem(item)
        layout.addWidget(list_widget)
        return group, list_widget

    def _create_combo(self, label_text, items):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(label_text)
        combo = QComboBox()
        combo.addItems(items)
        layout.addWidget(label)
        layout.addWidget(combo)
        return widget, combo

    def _connect_signals(self):
        self.clips_list_widget.currentRowChanged.connect(self.play_selected_clip)
        all_controls = [
            self.main_tags_list,
            self.clothing_main_tags_list,
            self.clothing_tags_list,
            self.corruption_combo,
            self.participants_combo,
            self.location_combo,
        ]
        for control in all_controls:
            if isinstance(control, QListWidget):
                control.itemSelectionChanged.connect(self.update_suggested_filename)
            elif isinstance(control, QComboBox):
                control.currentTextChanged.connect(self.update_suggested_filename)
        for chk in [
            self.only_suffix_check,
            self.not_prefix_check,
            self.orgasm_suffix_check,
            self.female_prefix_check,
            self.lesbian_prefix_check,
        ]:
            chk.stateChanged.connect(self.update_suggested_filename)
        self.back_button.clicked.connect(self.on_back_pressed)
        self.apply_button.clicked.connect(self.apply_tags_to_selected)
        self.export_button.clicked.connect(self.finalize_and_export)

    def update_suggested_filename(self):
        main_tags = {item.data(Qt.UserRole) for item in self.main_tags_list.selectedItems()}
        main_tags.update(
            {item.data(Qt.UserRole) for item in self.clothing_main_tags_list.selectedItems()}
        )
        main_tag_str = ",".join(sorted(list(main_tags)))
        if self.orgasm_suffix_check.isChecked():
            main_tag_str += "_orgasm"
        if self.female_prefix_check.isChecked():
            main_tag_str = "female_" + main_tag_str
        if self.lesbian_prefix_check.isChecked():
            main_tag_str = "lesbian_" + main_tag_str
        sub_tags = {item.data(Qt.UserRole) for item in self.clothing_tags_list.selectedItems()}
        if self.corruption_combo.currentIndex() > 0:
            sub_tags.add(
                self.vid_tag_options["corruption_level"][self.corruption_combo.currentText()]
            )
        if self.participants_combo.currentIndex() > 0:
            sub_tags.add(
                self.vid_tag_options["participants"][self.participants_combo.currentText()]
            )
        # [MODIFIED] Get location tag from the new unified source
        if self.location_combo.currentIndex() > 0:
            sub_tags.add(self.shoots_tags["location_tags"][self.location_combo.currentText()])
        sub_tag_list = sorted(list(sub_tags))
        if self.only_suffix_check.isChecked():
            sub_tag_list = [f"{tag}_only" for tag in sub_tag_list]
        sub_tag_str = ",".join(sub_tag_list)
        if not main_tag_str and not sub_tag_str:
            self.filename_preview.setText("Select tags...")
            return
        final_name = main_tag_str
        if sub_tag_str:
            final_name = f"{main_tag_str}-{sub_tag_str}" if main_tag_str else sub_tag_str
        if self.not_prefix_check.isChecked():
            final_name = "not_" + final_name
        self.filename_preview.setText(sanitize_filename(final_name) + ".webm")

    def apply_tags_to_selected(self):
        selected_items = self.clips_list_widget.selectedItems()
        if not selected_items:
            return QMessageBox.warning(self, "No Files", "Please select files.")
        final_filename = self.filename_preview.text()
        if not final_filename or final_filename.startswith("Select tags"):
            return QMessageBox.warning(self, "No Tags", "Please select tags.")
        for item in selected_items:
            path = item.data(Qt.UserRole)
            self.clips_data[path]["final_filename"] = final_filename
            item.setText(f"✓ {os.path.basename(path)}  ->  {final_filename}")
        logger.info(f"Applied tags to {len(selected_items)} items.")
        if self.reset_tags_check.isChecked():
            self.reset_all_tags()

    def finalize_and_export(self):
        tagged_data = self.get_tagged_data()
        if not tagged_data:
            return QMessageBox.warning(self, "No Tagged Clips", "No clips have been tagged.")
        logger.info(f"Finalizing and exporting {len(tagged_data)} tagged clips.")
        self.export_requested.emit(tagged_data)

    def get_tagged_data(self):
        return {path: data for path, data in self.clips_data.items() if "final_filename" in data}

    def reset_all_tags(self):
        for lst in [self.main_tags_list, self.clothing_main_tags_list, self.clothing_tags_list]:
            lst.clearSelection()
        for cmb in [self.corruption_combo, self.participants_combo, self.location_combo]:
            cmb.setCurrentIndex(0)
        for chk in [
            self.only_suffix_check,
            self.not_prefix_check,
            self.orgasm_suffix_check,
            self.female_prefix_check,
            self.lesbian_prefix_check,
            self.reset_tags_check,
        ]:
            chk.setChecked(False)
        self.update_suggested_filename()

    def load_clips(self, clips_data_with_ai: dict):
        self.clips_data = clips_data_with_ai
        self.clips_list_widget.clear()
        for path in self.clips_data.keys():
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.UserRole, path)
            self.clips_list_widget.addItem(item)
        if self.clips_list_widget.count() > 0:
            self.clips_list_widget.setCurrentRow(0)

    def play_selected_clip(self, row_index: int):
        if 0 <= row_index < self.clips_list_widget.count():
            path = self.clips_list_widget.item(row_index).data(Qt.UserRole)
            self.preview_player.load_video(path)

    def on_back_pressed(self):
        self.preview_player.release_player()
        self.back_requested.emit()
