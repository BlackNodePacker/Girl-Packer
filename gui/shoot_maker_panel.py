# GameMediaTool/gui/shoot_maker_panel.py (MODIFIED with UI change for Participant IDs)

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidget, QLineEdit, QTextEdit,
                               QGroupBox, QGridLayout, QMessageBox, QRadioButton, QStackedWidget,
                               QListWidgetItem, QComboBox, QCheckBox, QSpinBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from .components import PlayerWidget
from utils.file_ops import sanitize_filename
from tools.logger import get_logger

logger = get_logger("ShootMakerPanel_UI")

class ShootMakerPanel(QWidget):
    back_requested = Signal()
    sources_requested = Signal(str)
    ai_analysis_requested = Signal(list)
    save_shoot_requested = Signal(dict)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.shoot_data_buffer = {}
        self.current_shoot_type = None
        
        tm = self.main_window.tag_manager
        self.shoots_tags = tm.get_shoots_tags()

        main_layout = QVBoxLayout(self)
        self.step_stack = QStackedWidget()
        main_layout.addWidget(self.step_stack)
        
        self._setup_step1_type_selection()
        self._setup_step2_main_editor()
        
        self.step_stack.addWidget(self.step1_widget)
        self.step_stack.addWidget(self.step2_widget)
        
        self._connect_signals()

    def _setup_step1_type_selection(self):
        self.step1_widget = QWidget()
        layout = QVBoxLayout(self.step1_widget)
        group = QGroupBox("Step 1: Choose Shoot Type")
        group_layout = QVBoxLayout(group)

        self.photo_shoot_radio = QRadioButton("📸 Create a Photo Shoot")
        self.video_shoot_radio = QRadioButton("🎥 Create a Video Shoot")
        self.is_shared_checkbox = QCheckBox("Mark as a Shared Shoot")
        self.photo_shoot_radio.setChecked(True)
        
        self.start_shoot_button = QPushButton("Next: Select Media ➡️")
        self.start_shoot_button.setObjectName("ConfirmButton")
        self.back_to_dashboard_button1 = QPushButton("⬅️ Back to Dashboard")
        
        group_layout.addWidget(self.photo_shoot_radio)
        group_layout.addWidget(self.video_shoot_radio)
        group_layout.addSpacing(10)
        group_layout.addWidget(self.is_shared_checkbox)
        group_layout.addSpacing(10)
        group_layout.addWidget(self.start_shoot_button)
        group_layout.addWidget(self.back_to_dashboard_button1)
        
        layout.addStretch()
        layout.addWidget(group)
        layout.addStretch()
    
    def _create_right_panel(self):
        layout = QVBoxLayout()
        details_group = QGroupBox("Shoot Details (Config)")
        details_layout = QGridLayout(details_group)
        
        details_layout.addWidget(QLabel("Shoot Name:"), 0, 0)
        self.name_input = QLineEdit()
        details_layout.addWidget(self.name_input, 0, 1)
        
        details_layout.addWidget(QLabel("Display Name:"), 1, 0)
        self.display_name_input = QLineEdit()
        details_layout.addWidget(self.display_name_input, 1, 1)
        
        details_layout.addWidget(QLabel("Shoot Subtype:"), 2, 0)
        self.shoot_subtype_combo = QComboBox()
        self.shoot_subtype_combo.addItems(["--- Select ---"] + list(self.shoots_tags.get('shoot_subtypes', {}).keys()))
        details_layout.addWidget(self.shoot_subtype_combo, 2, 1)
        
        details_layout.addWidget(QLabel("Participants:"), 3, 0)
        self.participants_combo = QComboBox()
        self.participants_combo.addItems(["--- (Auto) ---"] + list(self.shoots_tags.get('participant_tags', {}).keys()))
        details_layout.addWidget(self.participants_combo, 3, 1)
        
        details_layout.addWidget(QLabel("Location:"), 4, 0)
        self.location_combo = QComboBox()
        self.location_combo.addItems(["--- (Auto) ---"] + list(self.shoots_tags.get('location_tags', {}).keys()))
        details_layout.addWidget(self.location_combo, 4, 1)
        
        details_layout.addWidget(QLabel("Theme:"), 5, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["--- Optional ---"] + list(self.shoots_tags.get('theme_tags', {}).keys()))
        details_layout.addWidget(self.theme_combo, 5, 1)
        
        # [NEW FEATURE] Add Participant IDs field here
        self.participant_ids_label = QLabel("Participant IDs:")
        self.participant_ids_input = QLineEdit()
        self.participant_ids_input.setPlaceholderText("e.g., character_one, character_two")
        details_layout.addWidget(self.participant_ids_label, 6, 0)
        details_layout.addWidget(self.participant_ids_input, 6, 1)
        self.participant_ids_label.hide()
        self.participant_ids_input.hide()
        
        details_layout.addWidget(QLabel("Description:"), 7, 0)
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(60)
        details_layout.addWidget(self.description_input, 7, 1)
        
        details_layout.addWidget(QLabel("Cost:"), 8, 0)
        self.cost_spinbox = QSpinBox()
        self.cost_spinbox.setRange(0, 9999)
        self.cost_spinbox.setValue(100)
        details_layout.addWidget(self.cost_spinbox, 8, 1)
        
        layout.addWidget(details_group)
        layout.addStretch()
        return layout

    def _connect_signals(self):
        # [MODIFIED] Connect the shared checkbox to the new field's visibility
        self.is_shared_checkbox.toggled.connect(self._on_shared_toggled)
        # --- Other signals ---
        self.start_shoot_button.clicked.connect(self._on_start_shoot)
        self.back_to_dashboard_button1.clicked.connect(self.back_requested.emit)
        self.add_button.clicked.connect(self._add_to_shoot)
        self.remove_button.clicked.connect(self._remove_from_shoot)
        self.move_up_button.clicked.connect(lambda: self._move_item(-1))
        self.move_down_button.clicked.connect(lambda: self._move_item(1))
        self.available_list.currentRowChanged.connect(lambda: self._preview_media(self.available_list))
        self.shoot_list.currentRowChanged.connect(lambda: self._preview_media(self.shoot_list))
        self.action_group_combo.currentTextChanged.connect(self._on_action_group_changed)
        self.apply_tags_button.clicked.connect(self._apply_item_tags)
        self.save_button.clicked.connect(self._on_save_shoot)
        
    def _on_shared_toggled(self, checked):
        # [MODIFIED] This now controls the visibility of the field in the right-hand panel
        self.participant_ids_label.setVisible(checked)
        self.participant_ids_input.setVisible(checked)
        if checked:
            char_id = sanitize_filename(self.main_window.project.character_name).lower().replace(' ', '_')
            self.participant_ids_input.setText(char_id)
        else:
            self.participant_ids_input.clear()
    
    # --- The rest of the file remains the same, but is included for completeness ---
    def _setup_step2_main_editor(self):
        self.step2_widget = QWidget(); main_layout = QVBoxLayout(self.step2_widget); title = QLabel("Step 2: Build & Configure Your Shoot"); title.setObjectName("TitleLabel"); main_layout.addWidget(title)
        top_layout = QHBoxLayout(); top_layout.addLayout(self._create_left_panel(), 2); top_layout.addLayout(self._create_center_panel(), 4); top_layout.addLayout(self._create_right_panel(), 3); main_layout.addLayout(top_layout)
        bottom_bar = QHBoxLayout(); back_button = QPushButton("⬅️ Back to Type Selection"); self.save_button = QPushButton("✔️ Save Shoot to Project"); self.save_button.setObjectName("ConfirmButton"); bottom_bar.addWidget(back_button); bottom_bar.addStretch(); bottom_bar.addWidget(self.save_button); main_layout.addLayout(bottom_bar)
        back_button.clicked.connect(lambda: self.step_stack.setCurrentWidget(self.step1_widget))
    
    def _create_left_panel(self):
        layout = QVBoxLayout(); available_group = QGroupBox("Available Media"); available_layout = QVBoxLayout(available_group); self.available_list = QListWidget(); self.available_list.setSelectionMode(QListWidget.ExtendedSelection); self.add_button = QPushButton("⬇️ Add to Shoot ⬇️"); available_layout.addWidget(self.available_list); available_layout.addWidget(self.add_button); layout.addWidget(available_group)
        shoot_group = QGroupBox("Items in Shoot (Sequence)"); shoot_layout = QVBoxLayout(shoot_group); list_hbox = QHBoxLayout(); self.shoot_list = QListWidget(); list_hbox.addWidget(self.shoot_list); arrows_vbox = QVBoxLayout(); self.move_up_button = QPushButton("⬆️"); self.move_down_button = QPushButton("⬇️"); arrows_vbox.addWidget(self.move_up_button); arrows_vbox.addWidget(self.move_down_button); arrows_vbox.addStretch(); list_hbox.addLayout(arrows_vbox); shoot_layout.addLayout(list_hbox); self.remove_button = QPushButton("⬆️ Remove from Shoot ⬆️"); shoot_layout.addWidget(self.remove_button); layout.addWidget(shoot_group); return layout
    
    def _create_center_panel(self):
        layout = QVBoxLayout(); preview_group = QGroupBox("Preview"); preview_layout = QVBoxLayout(preview_group); self.preview_stack = QStackedWidget(); self.image_preview_label = QLabel("Select an item to preview"); self.image_preview_label.setAlignment(Qt.AlignCenter); self.video_preview_player = PlayerWidget(); self.preview_stack.addWidget(self.image_preview_label); self.preview_stack.addWidget(self.video_preview_player); preview_layout.addWidget(self.preview_stack); layout.addWidget(preview_group)
        tagging_group = QGroupBox("Selected Item Tagging"); self.item_tagging_box = tagging_group; self.item_tagging_box.setEnabled(False); tag_layout = QGridLayout(tagging_group)
        self.main_tag_combo = self._create_combo("Main Tag:", self.shoots_tags.get('item_main_tags', {}).keys(), tag_layout, 0)
        self.action_group_combo = self._create_combo("Action Group:", self.shoots_tags.get('item_action_tags', {}).keys(), tag_layout, 1)
        self.specific_action_combo = self._create_combo("Specific Action:", [], tag_layout, 2); self.apply_tags_button = QPushButton("Apply Tags to Selected Item"); tag_layout.addWidget(self.apply_tags_button, 4, 0, 1, 2); layout.addWidget(tagging_group); return layout

    def _create_combo(self, label, items, layout, row):
        combo = QComboBox(); combo.addItems(["---"] + list(items)); layout.addWidget(QLabel(f"<b>{label}</b>"), row, 0); layout.addWidget(combo, row, 1); return combo
        
    def _preview_media(self, list_widget: QListWidget):
        item = list_widget.currentItem();
        if not item: self.video_preview_player.stop_video(); self.item_tagging_box.setEnabled(False); return
        path = item.data(Qt.UserRole)
        if self.current_shoot_type == "Photo Shoot": pixmap = QPixmap(path); self.image_preview_label.setPixmap(pixmap.scaled(self.image_preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else: self.video_preview_player.load_video(path)
        if list_widget is self.shoot_list:
            self.item_tagging_box.setEnabled(True); tags = self.shoot_data_buffer.get(path, {}).get('tags', {}); self.main_tag_combo.setCurrentText(tags.get('main_tag_text', "---")); self.action_group_combo.setCurrentText(tags.get('action_group', "---")); self._on_action_group_changed(self.action_group_combo.currentText()); self.specific_action_combo.setCurrentText(tags.get('specific_action', "---"))
        else: self.item_tagging_box.setEnabled(False)
    
    def activate(self):
        self.step_stack.setCurrentWidget(self.step1_widget); can_video_shoot = self.main_window.project.source_type == 'video' and bool(self.main_window.project.export_data.get('all_created_clips')); self.video_shoot_radio.setEnabled(can_video_shoot)
        if not can_video_shoot: self.photo_shoot_radio.setChecked(True); self.video_shoot_radio.setToolTip("Create clips in 'Vid Maker' first to enable this.")
    
    def display_sources(self, sources):
        self.available_list.clear(); self.shoot_list.clear(); self.shoot_data_buffer.clear()
        for source in sources:
            path = source if isinstance(source, str) else source.get('path', ''); name = os.path.basename(path)
            item = QListWidgetItem(name); item.setData(Qt.UserRole, path); self.available_list.addItem(item)
        self.step_stack.setCurrentWidget(self.step2_widget)
    
    def apply_ai_suggestions(self, suggestions):
        if suggestions.get('participants'): self.participants_combo.setCurrentText(suggestions['participants'])
        if suggestions.get('location_tag'):
            loc_tag = suggestions['location_tag'];
            for name, tag in self.shoots_tags.get('location_tags', {}).items():
                if tag == loc_tag: self.location_combo.setCurrentText(name); break
    
    def _on_start_shoot(self):
        if self.photo_shoot_radio.isChecked(): self.current_shoot_type = "Photo Shoot"; self.preview_stack.setCurrentWidget(self.image_preview_label)
        else: self.current_shoot_type = "Video Shoot"; self.preview_stack.setCurrentWidget(self.video_preview_player)
        self.sources_requested.emit(self.current_shoot_type)
    
    def _add_to_shoot(self):
        for item in self.available_list.selectedItems():
            path = item.data(Qt.UserRole);
            if path not in self.shoot_data_buffer:
                new_item = QListWidgetItem(f"✗ {os.path.basename(path)}"); new_item.setData(Qt.UserRole, path); self.shoot_list.addItem(new_item); self.shoot_data_buffer[path] = {'source_path': path, 'tags': {}}
        paths_in_shoot = [self.shoot_list.item(i).data(Qt.UserRole) for i in range(self.shoot_list.count())]
        if paths_in_shoot: self.ai_analysis_requested.emit(paths_in_shoot)
    
    def _remove_from_shoot(self):
        selected_items = self.shoot_list.selectedItems();
        if not selected_items: return
        for item in selected_items:
            path = item.data(Qt.UserRole); row = self.shoot_list.row(item); self.shoot_list.takeItem(row)
            if path in self.shoot_data_buffer: del self.shoot_data_buffer[path]
        paths_in_shoot = [self.shoot_list.item(i).data(Qt.UserRole) for i in range(self.shoot_list.count())]
        if paths_in_shoot: self.ai_analysis_requested.emit(paths_in_shoot)
    
    def _move_item(self, direction):
        row = self.shoot_list.currentRow()
        if row > -1 and 0 <= row + direction < self.shoot_list.count():
            item = self.shoot_list.takeItem(row); self.shoot_list.insertItem(row + direction, item); self.shoot_list.setCurrentRow(row + direction)
    
    def _on_action_group_changed(self, group_name):
        self.specific_action_combo.clear(); self.specific_action_combo.addItems(["---"]);
        if not group_name or group_name == "---": return
        actions_for_group = self.shoots_tags.get('item_action_tags', {}).get(group_name, {});
        if actions_for_group: self.specific_action_combo.addItems(list(actions_for_group.keys()))
    
    def _apply_item_tags(self):
        item = self.shoot_list.currentItem();
        if not item: return
        path = item.data(Qt.UserRole)
        tags_to_apply = {'main_tag_text': self.main_tag_combo.currentText(), 'action_group': self.action_group_combo.currentText(), 'specific_action': self.specific_action_combo.currentText()}
        self.shoot_data_buffer[path]['tags'] = tags_to_apply; item.setText(f"✓ {os.path.basename(path)}")
    
    def _on_save_shoot(self):
        shoot_name = self.name_input.text().strip(); display_name = self.display_name_input.text().strip()
        if not shoot_name or not display_name or self.shoot_subtype_combo.currentIndex() <= 0 or self.shoot_list.count() == 0: return QMessageBox.warning(self, "Incomplete Info", "Shoot Name, Display Name, Subtype, and at least one item are required.")
        shoot_key = sanitize_filename(shoot_name); all_tags = set()
        shoot_subtype_val = self.shoots_tags['shoot_subtypes'][self.shoot_subtype_combo.currentText()]; all_tags.add(shoot_subtype_val)
        if self.participants_combo.currentIndex() > 0: all_tags.add(self.shoots_tags['participant_tags'][self.participants_combo.currentText()])
        if self.location_combo.currentIndex() > 0: all_tags.add(self.shoots_tags['location_tags'][self.location_combo.currentText()])
        if self.theme_combo.currentIndex() > 0: all_tags.add(self.shoots_tags['theme_tags'][self.theme_combo.currentText()])
        config = {"name": shoot_key, "display_name": display_name, "shoot_subtype": shoot_subtype_val, "tags": sorted(list(filter(None, all_tags))), "cost": self.cost_spinbox.value(), "description": self.description_input.toPlainText().strip(), "is_shared": self.is_shared_checkbox.isChecked()}
        if config["is_shared"]:
            ids_text = self.participant_ids_input.text().strip()
            if ids_text: participant_ids = [pid.strip() for pid in ids_text.split(',') if pid.strip()]; config['participant_ids'] = participant_ids
        media_items = []
        for i in range(self.shoot_list.count()):
            item = self.shoot_list.item(i); path = item.data(Qt.UserRole); data = self.shoot_data_buffer.get(path)
            if not data or not data.get('tags') or data['tags'].get('main_tag_text', '---') == "---": return QMessageBox.warning(self, "Untagged Item", f"Item '{os.path.basename(path)}' has not been tagged with a Main Tag.")
            tags = data['tags']
            main_tag_val = self.shoots_tags['item_main_tags'].get(tags.get('main_tag_text'), "")
            action_group_dict = self.shoots_tags['item_action_tags'].get(tags.get('action_group'), {})
            action_val = action_group_dict.get(tags.get('specific_action'), "")
            
            # --- START MODIFIED FILENAME LOGIC (لتحقيق XX_MainTag-SubTag.ext) ---
            
            # 1. بناء الجزء الرئيسي (Sequence + Main Tag) مفصول بـ '_'
            main_parts = [f"{i+1:02d}"]
            if main_tag_val: main_parts.append(main_tag_val)
            main_block = "_".join(filter(None, main_parts))

            # 2. بناء الـ Sub Tags (Action Tag/Specific Action)
            # نفترض أن action_val هو الـ Sub Tag المتوفر حالياً (قد يحتوي على فاصلة إذا كان مركباً في نظام التاجات)
            sub_tag_str = action_val
            
            # 3. دمج الأجزاء باستخدام الشرطة '-'
            final_name_without_ext = main_block
            if sub_tag_str:
                final_name_without_ext = f"{main_block}-{sub_tag_str}"

            # 4. إضافة الامتداد وتطبيق التنقية
            ext = ".webp" if self.current_shoot_type == "Photo Shoot" else ".webm"; 
            final_filename = final_name_without_ext + ext
            
            # --- END MODIFIED FILENAME LOGIC ---
            
            media_items.append({'final_name': sanitize_filename(final_filename), 'source_path': path})
        final_data = {'shoot_type': self.current_shoot_type, 'shoot_key': shoot_key, 'config': config, 'media_items': media_items}
        self.save_shoot_requested.emit(final_data)