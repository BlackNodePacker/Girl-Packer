# GameMediaTool/gui/character_setup_panel.py (Corrected with QDialog import)

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QLineEdit, QGroupBox, QSizePolicy, QComboBox, QListWidget,
                               QCheckBox, QTabWidget, QGridLayout, QListWidgetItem,
                               QScrollArea, QFrame, QFileDialog, QMessageBox, QDialog) # <-- [THE FIX] QDialog added
from PySide6.QtCore import Qt, Signal, QDir

from .components.custom_trait_dialog import CustomTraitDialog
from utils.file_ops import sanitize_filename, list_files
from tools.logger import get_logger

logger = get_logger("CharacterSetupPanel")

class CharacterSetupPanel(QWidget):
    project_started = Signal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window; self.project = main_window.project; self.settings = main_window.settings
        self.last_input_path = self.settings.value("last_input_path", QDir.homePath())
        self.trait_checkboxes = {}; self.custom_traits_data = []
        main_layout = QVBoxLayout(self); main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container = QWidget(); container.setMaximumWidth(1200); container_layout = QVBoxLayout(container)
        top_hbox_layout = QHBoxLayout()
        top_hbox_layout.addLayout(self._create_left_column(), 1)
        top_hbox_layout.addWidget(self._create_right_column(), 2)
        container_layout.addLayout(top_hbox_layout)
        self.start_button = QPushButton("🚀 Continue to Dashboard"); self.start_button.setObjectName("ConfirmButton"); self.start_button.setFixedHeight(40)
        container_layout.addWidget(self.start_button)
        main_layout.addWidget(container); self._connect_signals()
        self.details_group.setVisible(self.create_char_config_checkbox.isChecked())

    def _create_left_column(self):
        layout = QVBoxLayout()
        project_group = QGroupBox("Step 1: Project Setup"); project_layout = QGridLayout(project_group)
        self.select_video_button = QPushButton("🎬 Select Video..."); self.select_folder_button = QPushButton("🖼️ Select Image Folder...")
        self.source_path_label = QLineEdit("No source selected."); self.source_path_label.setReadOnly(True)
        project_layout.addWidget(QLabel("<b>Source:</b>"), 0, 0); project_layout.addWidget(self.select_video_button, 0, 1); project_layout.addWidget(self.select_folder_button, 0, 2); project_layout.addWidget(self.source_path_label, 1, 1, 1, 2)
        project_layout.addWidget(QLabel("<b>Character Name:</b>"), 2, 0); self.name_input = QLineEdit(); self.name_input.setPlaceholderText("e.g., Violet Starr"); project_layout.addWidget(self.name_input, 2, 1, 1, 2)
        project_layout.addWidget(QLabel("<b>Character Type:</b>"), 3, 0); self.char_type_combo = QComboBox(); self.char_type_combo.addItems(["Girl", "Mother"]); project_layout.addWidget(self.char_type_combo, 3, 1)
        project_layout.addWidget(QLabel("<b>Modder Name:</b>"), 4, 0); self.modder_input = QLineEdit(); self.modder_input.setPlaceholderText("Your Name/Handle"); project_layout.addWidget(self.modder_input, 4, 1, 1, 2)
        layout.addWidget(project_group)
        options_group = QGroupBox("Step 2: Project Options"); options_layout = QVBoxLayout(options_group)
        self.create_char_config_checkbox = QCheckBox("Create Character Config (Traits, etc.)"); self.create_char_config_checkbox.setChecked(True)
        self.add_custom_trait_button = QPushButton("➕ Add New Custom Trait")
        options_layout.addWidget(self.create_char_config_checkbox); options_layout.addWidget(self.add_custom_trait_button)
        layout.addWidget(options_group); layout.addStretch(); return layout

    def _create_right_column(self):
        self.details_group = QGroupBox("Step 3: Character Details"); details_layout = QVBoxLayout(self.details_group)
        self.tabs = QTabWidget(); self._populate_traits_tabs(); details_layout.addWidget(self.tabs)
        custom_traits_group = self._create_custom_traits_group(); details_layout.addWidget(custom_traits_group)
        return self.details_group

    def _populate_traits_tabs(self):
        traits_data = self.main_window.tag_manager.get_character_traits()
        for main_cat, sub_cats in traits_data.items():
            tab = QWidget(); tab_layout = QVBoxLayout(tab); scroll_content = QWidget(); scroll_layout = QVBoxLayout(scroll_content)
            for sub_cat, traits in sub_cats.items():
                group = QGroupBox(sub_cat); grid = QGridLayout(group); row, col = 0, 0
                for name, data in traits.items():
                    tag = data.get('tag', sanitize_filename(name)); cb = QCheckBox(name); cb.setToolTip(data.get('description', '')); self.trait_checkboxes[tag] = cb; grid.addWidget(cb, row, col)
                    col += 1;
                    if col >= 2: col=0; row+=1
                scroll_layout.addWidget(group)
            scroll_layout.addStretch(); scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setWidget(scroll_content); tab_layout.addWidget(scroll_area); self.tabs.addTab(tab, main_cat)

    def _create_custom_traits_group(self):
        custom_group = QGroupBox("Custom Traits List"); custom_layout = QHBoxLayout(custom_group)
        self.custom_traits_list = QListWidget(); custom_layout.addWidget(self.custom_traits_list)
        buttons_vbox = QVBoxLayout(); edit_button = QPushButton("Edit"); delete_button = QPushButton("Delete")
        edit_button.clicked.connect(self._open_edit_trait_dialog); delete_button.clicked.connect(self._delete_selected_trait)
        buttons_vbox.addWidget(edit_button); buttons_vbox.addWidget(delete_button); buttons_vbox.addStretch(); custom_layout.addLayout(buttons_vbox)
        return custom_group

    def _connect_signals(self):
        self.create_char_config_checkbox.toggled.connect(self.details_group.setVisible)
        self.select_video_button.clicked.connect(self._select_video); self.select_folder_button.clicked.connect(self._select_image_folder)
        self.start_button.clicked.connect(self._start_project); self.add_custom_trait_button.clicked.connect(self._open_add_trait_dialog)

    def _refresh_custom_traits_list(self):
        self.custom_traits_list.clear()
        for trait_data in self.custom_traits_data:
            item = QListWidgetItem(f"{trait_data['display_name']} ({trait_data['tag_name']})")
            item.setData(Qt.UserRole, trait_data); self.custom_traits_list.addItem(item)

    def _open_add_trait_dialog(self):
        dialog = CustomTraitDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if new_data: self.custom_traits_data.append(new_data); self._refresh_custom_traits_list()

    def _open_edit_trait_dialog(self):
        selected_item = self.custom_traits_list.currentItem()
        if not selected_item: return
        initial_data = selected_item.data(Qt.UserRole); dialog = CustomTraitDialog(initial_data=initial_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if new_data: index = self.custom_traits_list.currentRow(); self.custom_traits_data[index] = new_data; self._refresh_custom_traits_list(); self.custom_traits_list.setCurrentRow(index)

    def _delete_selected_trait(self):
        current_row = self.custom_traits_list.currentRow()
        if current_row < 0: return
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this custom trait?")
        if reply == QMessageBox.StandardButton.Yes: self.custom_traits_data.pop(current_row); self._refresh_custom_traits_list()

    def _start_project(self):
        if not (self.project.source_video_path or self.project.source_image_paths): return QMessageBox.warning(self, "Input Missing", "Please select a source.")
        if not self.name_input.text().strip(): return QMessageBox.warning(self, "Input Missing", "Please enter a character name.")
        self.project.character_name = self.name_input.text().strip(); self.project.character_type = self.char_type_combo.currentText(); self.project.source_type = 'video' if self.project.source_video_path else 'folder'
        char_details = {"modder": self.modder_input.text().strip(), "create_char_config": self.create_char_config_checkbox.isChecked()}
        if char_details["create_char_config"]:
            char_details["traits"] = [tag for tag, cb in self.trait_checkboxes.items() if cb.isChecked()]; char_details["custom_traits"] = self.custom_traits_data
        self.project.character_details = char_details
        logger.info(f"Starting project '{self.project.character_name}'."); self.project_started.emit()

    def _select_video(self):
        fp,_ = QFileDialog.getOpenFileName(self, "Select Source Video", self.last_input_path, "Video Files (*.mp4 *.mov *.avi *.mkv)");
        if fp: self.project.source_video_path=fp; self.project.source_image_paths=[]; self.last_input_path=os.path.dirname(fp); self.settings.setValue("last_input_path", self.last_input_path); self.source_path_label.setText(os.path.basename(fp))
    def _select_image_folder(self):
        fp = QFileDialog.getExistingDirectory(self, "Select Image Folder", self.last_input_path)
        if fp: self.project.source_image_paths=list_files(fp, extensions=('.png','.jpg','.jpeg','.webp')); self.project.source_video_path=None; self.last_input_path=fp; self.settings.setValue("last_input_path", self.last_input_path); self.source_path_label.setText(f"{os.path.basename(fp)} ({len(self.project.source_image_paths)} images)")