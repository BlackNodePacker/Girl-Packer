import os
import cv2
import logging
import sys
import json 
import re
from datetime import datetime

# **********************************************
# * PySide6 Imports *
# **********************************************
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit, QLabel,
    QFormLayout, QTabWidget, QListWidget, QListWidgetItem, QPushButton, QComboBox,
    QSpinBox, QCheckBox, QTableWidget, QHeaderView,
    QTableWidgetItem, QInputDialog, QMessageBox,
    QGridLayout, QTextEdit, QSizePolicy, QScrollArea, QFrame
)
from PySide6.QtCore import (
    Signal as pyqtSignal, Qt, QSize
)
from PySide6.QtGui import QFont, QPixmap, QPalette, QColor
# **********************************************

# --- Standard Logging Setup ---
# استخدام logging.getLogger القياسي لتجنب أي تعارض في إعدادات الـ Handlers
logger = logging.getLogger("EventMakerPanel")
# ---------------------------

# Check for VLC and define PlayerWidget, or use a dummy for safety
try:
    import vlc
    
    # ******************************************************************************
    # * PlayerWidget (Integrated from user's provided code) *
    # ******************************************************************************
    logger_vlc = logging.getLogger("PlayerWidget") # استخدام logging.getLogger القياسي

    class PlayerWidget(QWidget):
        """Widget for displaying video content using VLC."""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.instance = None
            self.mediaplayer = None
            
            self.videoframe = QFrame()
            palette = self.videoframe.palette()
            palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Window, QColor(0, 0, 0))
            self.videoframe.setPalette(palette)
            self.videoframe.setAutoFillBackground(True)
            
            vbox = QVBoxLayout(self)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.addWidget(self.videoframe)
            self.setLayout(vbox)

        def _initialize_vlc(self):
            if self.instance is None:
                logger_vlc.info("Initializing new VLC instance...")
                vlc_options = [
                    '--avcodec-hw=none',
                    '--no-osd',
                    '--no-video-title-show',
                    '--ignore-config',
                    '--disable-screensaver',
                    '--quiet',
                ]
                self.instance = vlc.Instance(vlc_options)
            
            if self.instance is None:
                logger_vlc.critical("VLC Instance creation failed!")
                return

            if self.mediaplayer is None:
                self.mediaplayer = self.instance.media_player_new()
                if sys.platform.startswith("win"):
                    self.mediaplayer.set_hwnd(self.videoframe.winId())
                else: # For Linux/macOS
                    self.mediaplayer.set_xwindow(self.videoframe.winId())


        def load_video(self, path: str):
            """Loads and starts playing a video file."""
            self._initialize_vlc()
            if not self.mediaplayer:
                logger_vlc.error("Media player is not available. Cannot load video.")
                return
            media = self.instance.media_new(path)
            self.mediaplayer.set_media(media)
            self.play()
            logger_vlc.info(f"Loading and playing video: {os.path.basename(path)}")


        def release_player(self):
            """Stops and completely releases all VLC resources."""
            logger_vlc.info("Releasing all VLC resources...")
            if self.mediaplayer:
                if self.mediaplayer.is_playing():
                    self.mediaplayer.stop()
                self.mediaplayer.release()
                self.mediaplayer = None
            
            if self.instance:
                self.instance.release()
                self.instance = None

        def stop_video(self):
            if self.mediaplayer: 
                self.mediaplayer.stop()
        
        # Keep other essential methods for completeness, though not all are used here
        def play(self):
            if self.mediaplayer: self.mediaplayer.play()
        def pause(self):
            if self.mediaplayer: self.mediaplayer.pause()
        def is_playing(self) -> bool:
            return self.mediaplayer.is_playing() if self.mediaplayer else False
            
except ImportError:
    class PlayerWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            label = QLabel("VLC Player not available for video preview.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        def load_video(self, path: str):
            logging.getLogger("PlayerWidget").warning("VLC library (python-vlc) is not installed. Video preview disabled.")
        def release_player(self): pass
        def stop_video(self): pass
# ******************************************************************************
# * End of PlayerWidget *
# ******************************************************************************


class EventMakerPanel(QWidget):
    """
    Panel for creating and configuring Ren'Py events.
    Handles event requirements, impacts, and RPY script management across stages.
    """
    
    back_requested = pyqtSignal()

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager 
        
        # Internal Data
        self.current_script_data = {} 
        self.participant_impacts_data = {} 
        self.current_participant_id = None
        
        # --- NEW ASSET MANAGEMENT ---
        self.available_assets = {} 
        
        # 1. Container for dynamic preview (Image QLabel or Video Player)
        self.preview_container = QFrame()
        self.preview_container.setFrameShape(QFrame.Shape.StyledPanel)
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # 2. Video Player (Initialized here but hidden)
        self.video_player = PlayerWidget() 
        self.video_player.setVisible(False)
        self.preview_layout.addWidget(self.video_player)
        
        # 3. Image Preview (QLabel) - Used for images and initial state
        self.image_preview = QLabel("Select an asset from the list to preview.") 
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setScaledContents(True)
        self.image_preview.setStyleSheet("border: 1px solid gray;")
        self.preview_layout.addWidget(self.image_preview)
        
        self.media_list_widget = QListWidget() 
        # --- END NEW ASSET MANAGEMENT ---
        
        # --- UI Element Initialization ---
        self.tabs = QTabWidget()
        self._initialize_ui_elements()
        self._setup_ui()
        self._initialize_default_state()
        
        # ربط التبديل بين علامات التبويب لحفظ السكريبت الحالي وتحديث قائمة الميديا
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # New: Clean up VLC resources when the widget is destroyed
        self.destroyed.connect(self.video_player.release_player)


    def _on_tab_changed(self, index):
        """Saves the script content if the user is leaving the Script Editor tab and refreshes the media list if entering the Media Library tab."""
        # Index 1 هو الـ index الخاص بـ "Script Editor"
        if index != 1: 
            self._save_current_stage_script()
            logger.debug(f"Script saved automatically on tab change to index {index}")
            
        # Index 2 هو الـ index الخاص بـ "Media Library"
        if index == 2:
            self._populate_media_list() 
            logger.debug("Media list refreshed upon entering Media Library tab.")
        
        # New: Stop video player when leaving Media Library tab (index 2)
        if index != 2:
            self.video_player.stop_video()
            logger.debug("Video player stopped due to tab change.")


    def _initialize_ui_elements(self):
        # Main Info
        self.event_name_input = QLineEdit()
        self.event_display_name_input = QLineEdit()
        self.event_type_combo = QComboBox()
        self.event_reqs_desc_input = QLineEdit()
        self.girl_id_input = QLineEdit()
        # self.shoot_name_input removed as requested.
        
        # Participants
        self.participants_list = QListWidget()
        self.participant_type_combo = QComboBox()
        self.participant_id_input = QLineEdit()
        
        # Impacts
        self.impact_participant_combo = QComboBox()
        self.participant_stats_table = QGroupBox() 
        self.traits_to_add_list = QListWidget()
        self.traits_to_remove_list = QListWidget()
        
        # Requirements
        self.stat_requirements_table = QGroupBox() 
        self.required_traits_table = QGroupBox() 
        self.forbidden_traits_table = QGroupBox() 
        self.min_chance_spinbox = QSpinBox()
        self.max_chance_spinbox = QSpinBox()
        self.action_reqs_table = QGroupBox() 
        self.accept_influences_table = QGroupBox() 
        
        # Stages & Script
        self.stages_list = QListWidget()
        self.script_editor = QTextEdit()
        
        # Options
        self.one_time_event_check = QCheckBox("One Time Event")
        self.reset_outfit_check = QCheckBox("Reset Outfit when Finished")
        self.hide_in_menus_check = QCheckBox("Hide in Menus")
        self.ignore_frequency_check = QCheckBox("Ignore Frequency")
        self.allow_random_trigger_check = QCheckBox("Allow Random Trigger")
        self.event_cooldown_spinbox = QSpinBox()
        self.participant_cooldown_spinbox = QSpinBox()
        
        # Trait Comboboxes
        self.trait_add_combo = QComboBox()
        self.trait_remove_combo = QComboBox()

    # --- Utility Functions (Kept the same) ---
    def _get_list_widget_items(self, list_widget: QListWidget):
        return [list_widget.item(i).text() for i in range(list_widget.count())]

    def _get_table_data(self, table_widget: QTableWidget):
        data = []
        for row in range(table_widget.rowCount()):
            row_data = []
            for col in range(table_widget.columnCount()):
                item = table_widget.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data

    def _populate_table_from_list(self, table_widget: QTableWidget, data_list: list, row_mapper):
        table_widget.setRowCount(0)
        for row_index, item in enumerate(data_list):
            mapped_row = row_mapper(item)
            if mapped_row:
                table_widget.insertRow(row_index)
                for col_index, value in enumerate(mapped_row):
                    table_widget.setItem(row_index, col_index, QTableWidgetItem(value))
                    
    def _initialize_participant_impact(self, pid):
        if pid not in self.participant_impacts_data:
            self.participant_impacts_data[pid] = {
                'stats': {},
                'add_traits': [],
                'remove_traits': []
            }
            
    def _initialize_default_state(self):
        # Set default values for spinboxes
        self.min_chance_spinbox.setValue(0)
        self.max_chance_spinbox.setValue(100)
        self.event_cooldown_spinbox.setValue(7)
        self.participant_cooldown_spinbox.setValue(2)
        
        # Populate Comboboxes
        self.participant_type_combo.addItems(["girl", "player", "other"])
        self.event_type_combo.addItems(["home_visit", "post_exam", "dream", "home_visit_early", "school_day"])
        
        try:
             if hasattr(self.project_manager, 'get_all_traits'):
                 all_traits = self.project_manager.get_all_traits()
             else:
                 # لم نعد نستخدم logger_vlc.warning هنا لتجنب التعقيد، نستخدم logger
                 logger.warning(f"Project Manager object ({type(self.project_manager).__name__}) is missing 'get_all_traits' method.")
                 all_traits = []


             self.trait_add_combo.addItems(all_traits)
             self.trait_remove_combo.addItems(all_traits)
             
        except Exception as e:
             logger.warning(f"Could not load traits from project_manager: {type(e).__name__}: {e}")
        
        self._add_stage(initial=True, name="start")
        
        self.participant_id_input.setText("")
        self.participant_type_combo.setCurrentText("girl")
        self._add_participant(initial=True) 

        
    # ******************************************************************************
    # * UI Setup *
    # ******************************************************************************

    def _create_group_box_with_layout(self, title, layout):
        group = QGroupBox(title)
        group.setLayout(layout)
        return group
    
    def _setup_general_tab(self):
        main_layout = QVBoxLayout()
        
        # 1. Event Details Group
        info_form = QFormLayout()
        self.event_type_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        info_form.addRow("Internal Name:", self.event_name_input)
        info_form.addRow("Display Name:", self.event_display_name_input)
        info_form.addRow("Event Type:", self.event_type_combo)
        info_form.addRow("Reqs Description:", self.event_reqs_desc_input)
        info_form.addRow("Girl ID:", self.girl_id_input)
        # تمت إزالة حقل "Shoot Name" بناءً على طلب المستخدم
        
        details_group = self._create_group_box_with_layout("Event Details", info_form)
        main_layout.addWidget(details_group)

        # 2. Participants Section
        main_layout.addWidget(self._setup_participants_section())

        # 3. Options Group
        options_layout = QHBoxLayout()
        options_layout.addWidget(self.one_time_event_check)
        options_layout.addWidget(self.reset_outfit_check)
        options_layout.addWidget(self.hide_in_menus_check)
        options_layout.addWidget(self.ignore_frequency_check)
        options_layout.addWidget(self.allow_random_trigger_check)
        options_layout.addSpacing(20)
        options_layout.addWidget(QLabel("Event Cooldown:"))
        options_layout.addWidget(self.event_cooldown_spinbox)
        options_layout.addWidget(QLabel("Part. Cooldown:"))
        options_layout.addWidget(self.participant_cooldown_spinbox)
        options_layout.addStretch(1)
        
        options_group = self._create_group_box_with_layout("Event Options & Cooldowns", options_layout)
        main_layout.addWidget(options_group)
        
        main_layout.addStretch(1) # Push everything to the top
        container = QWidget()
        container.setLayout(main_layout)
        return container
        
    def _setup_participants_section(self):
        participants_layout = QVBoxLayout()
        
        add_p_layout = QHBoxLayout()
        add_p_layout.addWidget(QLabel("Type:"))
        add_p_layout.addWidget(self.participant_type_combo, 1)
        add_p_layout.addWidget(QLabel("Suffix:"))
        add_p_layout.addWidget(self.participant_id_input, 2)
        
        add_btn = QPushButton("Add Participant")
        add_btn.clicked.connect(self._add_participant)
        add_p_layout.addWidget(add_btn)
        participants_layout.addLayout(add_p_layout)
        
        participants_layout.addWidget(QLabel("Current Participants:"))
        participants_layout.addWidget(self.participants_list, 1) # List takes available space
        
        return self._create_group_box_with_layout("Participants", participants_layout)
    
    def _setup_req_impact_tab(self):
        main_layout = QHBoxLayout()

        # 1. Requirements Section (Left side)
        requirements_group = self._setup_requirements_section()
        main_layout.addWidget(requirements_group, 1)

        # 2. Impacts Section (Right side)
        impacts_group = self._setup_participant_impacts_section()
        main_layout.addWidget(impacts_group, 1)
        
        container = QWidget()
        container.setLayout(main_layout)
        return container

    def _setup_participant_impacts_section(self):
        impacts_layout = QVBoxLayout()

        # 1. Participant Selector 
        self.impact_participant_combo.addItem("--- No Participants ---")
        self.impact_participant_combo.currentTextChanged.connect(self._on_impact_participant_changed)
        
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Editing Impacts for:"))
        selector_layout.addWidget(self.impact_participant_combo, 1)
        impacts_layout.addLayout(selector_layout)

        # 2. Stats Table 
        stats_table_widget = QTableWidget(0, 3)
        stats_table_widget.setHorizontalHeaderLabels(["Stat", "Min XP", "Max XP"])
        stats_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # *** التعديل لتصحيح العرض ***
        stats_table_layout = QVBoxLayout()
        stats_table_layout.addWidget(stats_table_widget)
        self.participant_stats_table = self._create_group_box_with_layout("Stat Impacts (XP)", stats_table_layout)
        impacts_layout.addWidget(self.participant_stats_table, 1) 
        # *** نهاية التعديل ***


        # 3. Traits Lists
        traits_group = QGroupBox("Trait Impacts")
        traits_layout = QHBoxLayout()
        
        # Layout for Traits to ADD
        add_trait_layout = QVBoxLayout()
        add_trait_layout.addWidget(QLabel("Traits to ADD:"))
        self.traits_to_add_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        add_trait_layout.addWidget(self.traits_to_add_list, 1)
        
        add_trait_controls = QHBoxLayout()
        add_trait_controls.addWidget(self.trait_add_combo, 1)
        
        add_trait_btn = QPushButton("+")
        add_trait_btn.setFixedWidth(30)
        add_trait_btn.clicked.connect(lambda: self._add_trait_to_list(self.trait_add_combo, self.traits_to_add_list))
        
        # *** التعديل لتصحيح العرض ***
        add_trait_controls.addWidget(add_trait_btn)
        add_trait_layout.addLayout(add_trait_controls)
        # *** نهاية التعديل ***
        
        # Layout for Traits to REMOVE
        remove_trait_layout = QVBoxLayout()
        remove_trait_layout.addWidget(QLabel("Traits to REMOVE:"))
        self.traits_to_remove_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        remove_trait_layout.addWidget(self.traits_to_remove_list, 1)
        
        remove_trait_controls = QHBoxLayout()
        remove_trait_controls.addWidget(self.trait_remove_combo, 1)
        
        remove_trait_btn = QPushButton("+")
        remove_trait_btn.setFixedWidth(30)
        remove_trait_btn.clicked.connect(lambda: self._add_trait_to_list(self.trait_remove_combo, self.traits_to_remove_list))

        # *** التعديل لتصحيح العرض ***
        remove_trait_controls.addWidget(remove_trait_btn)
        remove_trait_layout.addLayout(remove_trait_controls)
        # *** نهاية التعديل ***

        traits_layout.addLayout(add_trait_layout, 1)
        traits_layout.addLayout(remove_trait_layout, 1)
        traits_group.setLayout(traits_layout)
        impacts_layout.addWidget(traits_group, 1) 
        
        return self._create_group_box_with_layout("Participant Impacts", impacts_layout)

    def _setup_requirements_section(self):
        reqs_layout = QVBoxLayout()
        
        # Stat Requirements Table
        stats_table_widget = QTableWidget(0, 4)
        stats_table_widget.setHorizontalHeaderLabels(["Stat", "Op", "Value", "Target"])
        stats_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stat_requirements_table = self._create_group_box_with_layout("Stat Requirements", QVBoxLayout())
        self.stat_requirements_table.findChild(QVBoxLayout).addWidget(stats_table_widget)
        reqs_layout.addWidget(self.stat_requirements_table, 2) 

        # Trait Requirements
        traits_group = QGroupBox("Trait Requirements")
        traits_layout = QHBoxLayout()

        req_traits_table_widget = QTableWidget(0, 2)
        req_traits_table_widget.setHorizontalHeaderLabels(["Trait", "Target"])
        req_traits_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.required_traits_table = self._create_group_box_with_layout("Required Traits", QVBoxLayout())
        self.required_traits_table.findChild(QVBoxLayout).addWidget(req_traits_table_widget)
        
        forbid_traits_table_widget = QTableWidget(0, 2)
        forbid_traits_table_widget.setHorizontalHeaderLabels(["Trait", "Target"])
        forbid_traits_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.forbidden_traits_table = self._create_group_box_with_layout("Forbidden Traits", QVBoxLayout())
        self.forbidden_traits_table.findChild(QVBoxLayout).addWidget(forbid_traits_table_widget)

        traits_layout.addWidget(self.required_traits_table, 1)
        traits_layout.addWidget(self.forbidden_traits_table, 1)
        traits_group.setLayout(traits_layout)
        reqs_layout.addWidget(traits_group, 2) 

        # Chance Calculation
        chance_group = QGroupBox("Chance to Happen Calculation (0-100%)")
        chance_layout = QVBoxLayout()
        
        min_max_layout = QHBoxLayout()
        min_max_layout.addWidget(QLabel("Min Chance:"))
        min_max_layout.addWidget(self.min_chance_spinbox, 1)
        min_max_layout.addWidget(QLabel("Max Chance:"))
        min_max_layout.addWidget(self.max_chance_spinbox, 1)
        chance_layout.addLayout(min_max_layout)
        
        action_reqs_table_widget = QTableWidget(0, 2)
        action_reqs_table_widget.setHorizontalHeaderLabels(["Action", "Count"])
        action_reqs_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.action_reqs_table = self._create_group_box_with_layout("Action Requirements", QVBoxLayout())
        self.action_reqs_table.findChild(QVBoxLayout).addWidget(action_reqs_table_widget)
        chance_layout.addWidget(self.action_reqs_table, 1)
        
        accept_influences_table_widget = QTableWidget(0, 2)
        accept_influences_table_widget.setHorizontalHeaderLabels(["Stat/Action", "Weight"])
        accept_influences_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.accept_influences_table = self._create_group_box_with_layout("Accept Influences", QVBoxLayout())
        self.accept_influences_table.findChild(QVBoxLayout).addWidget(accept_influences_table_widget)
        chance_layout.addWidget(self.accept_influences_table, 1)
        
        chance_group.setLayout(chance_layout)
        reqs_layout.addWidget(chance_group, 3) 
        
        return self._create_group_box_with_layout("Event Requirements & Chance", reqs_layout)

    def _setup_script_editor_tab(self):
        main_layout = QHBoxLayout()
        
        # Left Side: Stage Management (1/5 of the width)
        stage_management_layout = QVBoxLayout()
        stage_management_layout.addWidget(QLabel("Stages (Ren'Py Labels):"))
        self.stages_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        stage_management_layout.addWidget(self.stages_list, 1)
        
        stage_btn_layout = QHBoxLayout()
        add_stage_btn = QPushButton("Add Stage")
        add_stage_btn.clicked.connect(self._add_stage)
        remove_stage_btn = QPushButton("Remove Stage")
        remove_stage_btn.clicked.connect(self._remove_stage)
        
        stage_btn_layout.addWidget(add_stage_btn)
        stage_btn_layout.addWidget(remove_stage_btn)
        stage_management_layout.addLayout(stage_btn_layout)
        
        self.stages_list.currentRowChanged.connect(self._update_stage_selector)
        
        stage_group = self._create_group_box_with_layout("Stage Management", stage_management_layout)
        main_layout.addWidget(stage_group, 1) 

        # Middle: Script Editor (3/5 of the width)
        script_editor_layout = QVBoxLayout()
        script_editor_layout.addWidget(QLabel("Ren'Py Script Content (Indentation is handled automatically):"))
        
        font = QFont("Monospace")
        font.setPointSize(10)
        self.script_editor.setFont(font)
        
        script_editor_layout.addWidget(self.script_editor, 1) 
        
        editor_group = self._create_group_box_with_layout("Script Editor", script_editor_layout)
        main_layout.addWidget(editor_group, 3) 

        # Right Side: RPY Helper Tools (1/5 of the width)
        rpy_tools_group = self._setup_rpy_tools_section()
        main_layout.addWidget(rpy_tools_group, 1) 
        
        container = QWidget()
        container.setLayout(main_layout)
        return container

    def _setup_rpy_tools_section(self):
        tools_layout = QVBoxLayout()
        tools_layout.addWidget(QLabel("RPY Script Helpers:"))

        self.dialog_btn = QPushButton("1. Add Dialog/Line")
        self.show_image_btn = QPushButton("2. Add Show Image")
        self.show_video_btn = QPushButton("3. Add Show Video")
        self.menu_btn = QPushButton("4. Add Menu Block")
        self.pause_btn = QPushButton("5. Add Pause")
        self.pass_btn = QPushButton("6. Add Pass (in Menu)")
        self.end_early_btn = QPushButton("7. End Event Early")
        self.return_btn = QPushButton("8. Add Stage Return")

        tools_layout.addWidget(self.dialog_btn)
        tools_layout.addWidget(self.show_image_btn)
        tools_layout.addWidget(self.show_video_btn)
        tools_layout.addWidget(self.menu_btn)
        tools_layout.addWidget(self.pause_btn)
        tools_layout.addWidget(self.pass_btn)
        self.end_early_btn.clicked.connect(lambda: self._insert_text_to_editor('$ current_event.end_event_early(reset_availability=True)\nreturn\n'))
        self.return_btn.clicked.connect(lambda: self._insert_text_to_editor('return\n'))

        tools_layout.addWidget(self.end_early_btn)
        tools_layout.addWidget(self.return_btn)
        
        self.dialog_btn.clicked.connect(self._add_dialog)
        self.show_image_btn.clicked.connect(self._add_show_image)
        self.show_video_btn.clicked.connect(self._add_show_video)
        self.menu_btn.clicked.connect(self._add_menu_block)
        self.pause_btn.clicked.connect(lambda: self._insert_text_to_editor("pause\n"))
        self.pass_btn.clicked.connect(lambda: self._insert_text_to_editor("pass\n"))
        
        tools_layout.addStretch(1)

        return self._create_group_box_with_layout("RPY Tools", tools_layout)

    def _setup_media_library_tab(self):
        # [تعديل الواجهة] تم استبدال QLabel بـ self.preview_container الذي يحوي QLabel و PlayerWidget
        main_layout = QHBoxLayout()
        
        # Left Side: Preview
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel("Asset Preview:"))
        
        # Use the container widget (self.preview_container)
        self.preview_container.setMinimumSize(300, 200)
        self.preview_container.setMaximumHeight(350)
        
        preview_layout.addWidget(self.preview_container)
        
        # Add simple buttons for faster RPY insertion
        control_layout = QHBoxLayout()
        insert_image_btn = QPushButton("Insert Image RPY")
        insert_video_btn = QPushButton("Insert Video RPY")
        insert_image_btn.clicked.connect(lambda: self._on_quick_insert("image"))
        insert_video_btn.clicked.connect(lambda: self._on_quick_insert("video"))
        control_layout.addWidget(insert_image_btn)
        control_layout.addWidget(insert_video_btn)
        preview_layout.addLayout(control_layout)
        preview_layout.addStretch(1)

        preview_group = self._create_group_box_with_layout("Preview & Controls", preview_layout)
        main_layout.addWidget(preview_group, 1)

        # Right Side: Available Assets List
        list_layout = QVBoxLayout()
        list_layout.addWidget(QLabel("Available Assets (Double-Click to Insert):"))
        self.media_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        list_layout.addWidget(self.media_list_widget, 1)
        
        list_layout.addWidget(QLabel("Note: Assets are named (pic1, vid1) for easy scripting."))
        
        self.media_list_widget.doubleClicked.connect(self._on_media_double_click)
        self.media_list_widget.currentRowChanged.connect(self._on_asset_selection_changed)

        list_group = self._create_group_box_with_layout("Media Library (Scripting Names)", list_layout)
        main_layout.addWidget(list_group, 2) # Give the list more space

        container = QWidget()
        container.setLayout(main_layout)
        return container
    
    def _on_asset_selection_changed(self, index):
        """Updates the preview pane when an asset is selected."""
        selected_item = self.media_list_widget.item(index)
        
        # 1. Cleanup and Reset View to Image mode (default)
        self.video_player.stop_video()
        self.video_player.setVisible(False)
        self.image_preview.setVisible(True)
        self.image_preview.setPixmap(QPixmap()) # Clear any previous image
        
        if not selected_item:
            self.image_preview.setText("Select an asset from the list to preview.")
            return

        # Get asset info
        asset_name = selected_item.data(Qt.ItemDataRole.UserRole)
        asset_info = self.available_assets.get(asset_name)
        
        if not asset_info: 
            self.image_preview.setText(f"Asset info missing for {asset_name}.")
            return
        
        path = asset_info['path']
        asset_type = asset_info['type']
        
        # 2. Dynamic Preview Logic
        if asset_type == 'image':
            try:
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    self.image_preview.setPixmap(pixmap.scaled(self.image_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    self.image_preview.setText("") # Clear placeholder text if image loads
                else:
                    self.image_preview.setText(f"Cannot load image: {os.path.basename(path)}")
            except Exception as e:
                self.image_preview.setText(f"Preview Error: {type(e).__name__}")
                
        elif asset_type == 'video':
            # Switch to Video Player
            self.image_preview.setVisible(False)
            self.video_player.setVisible(True)
            try:
                self.video_player.load_video(path)
            except Exception as e:
                 logger.error(f"Failed to load video with PlayerWidget: {e}")
                 self.video_player.setVisible(False)
                 self.image_preview.setVisible(True)
                 self.image_preview.setText(f"VIDEO ERROR: Failed to load with VLC ({type(e).__name__}).")
        else:
            self.image_preview.setText(f"Unknown asset type: {asset_type}")


    def _on_quick_insert(self, asset_type):
        """Inserts the RPY code for the currently selected asset based on its type."""
        selected_items = self.media_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select an asset from the list first.")
            return
        
        asset_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        asset_info = self.available_assets.get(asset_name)

        if asset_info['type'] == 'image' and asset_type == 'image':
            self._add_show_image(asset_name)
        elif asset_info['type'] == 'video' and asset_type == 'video':
            self._add_show_video(asset_name)
        else:
            QMessageBox.warning(self, "Warning", f"Cannot insert {asset_type} RPY code for a {asset_info['type']} asset.")


    def _populate_media_list(self):
        self.media_list_widget.clear()
        self.available_assets = {}
        
        # Reset preview view and stop any playing video
        self.video_player.stop_video()
        self.video_player.setVisible(False)
        self.image_preview.setVisible(True)
        self.image_preview.setText("Select an asset from the list to preview.")

        try:
            file_paths = []
            if hasattr(self.project_manager, 'get_asset_file_paths'):
                 file_paths = self.project_manager.get_asset_file_paths()
            else:
                 raise AttributeError("Project Manager is missing the required media retrieval method: 'get_asset_file_paths'.")

            if not file_paths:
                 QListWidgetItem("No media files found in the current project assets.", self.media_list_widget)
                 return

            image_count = 1
            video_count = 1
            
            # Filter, Name, and Display
            for path in file_paths:
                file_name = os.path.basename(path)
                path_lower = path.lower()
                
                if path_lower.endswith(('.webp', '.png', '.jpg', '.jpeg')):
                    script_name = f"pic{image_count}"
                    asset_type = 'image'
                    image_count += 1
                elif path_lower.endswith(('.webm', '.mp4')):
                    script_name = f"vid{video_count}"
                    asset_type = 'video'
                    video_count += 1
                else:
                    continue 

                # Store the asset info internally
                self.available_assets[script_name] = {
                    'path': path, 
                    'type': asset_type,
                    'rpy_path_hint': os.path.join(os.path.basename(os.path.dirname(path)), file_name)
                }
                
                # Display in the list widget
                item_text = f"[{script_name}] {file_name}"
                item = QListWidgetItem(item_text, self.media_list_widget)
                item.setData(Qt.ItemDataRole.UserRole, script_name) 
        
        except Exception as e:
            logger.error(f"Failed to populate media list: {type(e).__name__}: {e}")
            self.media_list_widget.clear()
            QListWidgetItem(f"ERROR: Could not load media files. Check logs: {type(e).__name__}", self.media_list_widget)

    def _on_media_double_click(self, index):
        """Inserts the RPY code for the selected asset using its generated script name."""
        item = self.media_list_widget.item(index.row())
        script_name = item.data(Qt.ItemDataRole.UserRole)
        
        if not script_name: return
        
        asset_info = self.available_assets.get(script_name)
        if not asset_info: return

        if asset_info['type'] == 'image':
            self._add_show_image(script_name)
        elif asset_info['type'] == 'video':
            self._add_show_video(script_name)

    def _setup_event_configuration_tab(self):
        """
        Creates the main configuration tab with nested tabs for better layout.
        """
        main_layout = QVBoxLayout()
        
        # Top Controls: Back to Dashboard & Save
        top_controls_layout = QHBoxLayout()
        self.back_to_dashboard_btn = QPushButton("Back to Dashboard")
        self.back_to_dashboard_btn.clicked.connect(self.back_requested.emit)
        save_btn = QPushButton("Save Event (JSON & RPY)")
        save_btn.clicked.connect(self._on_save_event)
        
        top_controls_layout.addWidget(self.back_to_dashboard_btn)
        top_controls_layout.addStretch(1)
        top_controls_layout.addWidget(save_btn)
        main_layout.addLayout(top_controls_layout)

        # Nested Tabs
        nested_tabs = QTabWidget()
        nested_tabs.addTab(self._setup_general_tab(), "General & Participants")
        nested_tabs.addTab(self._setup_req_impact_tab(), "Requirements & Impacts")
        
        main_layout.addWidget(nested_tabs, 1) 

        container = QWidget()
        container.setLayout(main_layout)
        return container

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        self.tabs.addTab(self._setup_event_configuration_tab(), "Event Configuration") 
        self.tabs.addTab(self._setup_script_editor_tab(), "Script Editor")
        media_tab = self._setup_media_library_tab()
        self.tabs.addTab(media_tab, "Media Library")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        self.setWindowTitle("Event Maker Panel")
        
    # ******************************************************************************
    # * RPY SCRIPT GENERATION HELPERS *
    # ******************************************************************************

    def _insert_text_to_editor(self, text):
        """Inserts text at the current cursor position in the script editor."""
        cursor = self.script_editor.textCursor()
        cursor.insertText(text)
        self.script_editor.setTextCursor(cursor)
        self._save_current_stage_script() 

    # ------------------------------------------------------------------------------------------------
    # دالة _add_dialog: تم تعديلها في الخطوة السابقة وهي سليمة
    def _add_dialog(self):
        """Inserts a dialog line template."""
        
        # 1. Identify all non-special participants added by the user
        all_participants = self._get_list_widget_items(self.participants_list)
        # قم بإزالة 'girl' و 'player' من قائمة المشاركين المخصصين إذا كانت موجودة، لمنع التكرار
        custom_participants = [p for p in all_participants if p.lower() not in ["girl", "player"]]
        
        # 2. Hardcoded list of essential dialogue options for clarity
        char_list = [
            "Narrator (no name)",
            "Player (player.character)",
            "Girl (selected_girl.character)",
        ]
        
        # 3. Add other non-special participants (custom characters)
        char_list.extend(custom_participants)
             
        # Use QInputDialog to get the selection
        char_id, ok = QInputDialog.getItem(self, "Add Dialog", "Select Character ID:", char_list, 0, False)
        if not ok: return
        
        dialog, ok_d = QInputDialog.getText(self, "Add Dialog", f"Enter the dialogue for '{char_id}':")
        if not ok_d: return

        # Extract the base character ID (e.g., 'Player' from 'Player (player.character)')
        # This relies on the format 'Name (hint)', taking only the first word before the space.
        char_text = char_id.split(' ')[0].strip() 

        # Generate the RPY line
        if char_text == "Narrator":
             line = f'"{dialog}"\n'
        elif char_text.lower() == "girl":
             line = f'selected_girl.character "{dialog}"\n'
        elif char_text.lower() == "player":
             line = f'player.character "{dialog}"\n'
        else:
             # For custom participants (e.g., 'roommate')
             line = f'"{char_text}" "{dialog}"\n'
             
        self._insert_text_to_editor(line)
    # ------------------------------------------------------------------------------------------------

    def _add_show_image(self, script_name: str = None):
        """Inserts a 'show image' line using the generated script name."""
        if not script_name:
             script_name, ok = QInputDialog.getText(self, "Add Show Image", "Enter Image Script Name (e.g., 'pic1', 'my_custom_image'):", 
                                          QLineEdit.Normal, "")
             if not ok or not script_name.strip(): return
             
        line = f'$ current_event.show_image("{script_name}")\n'
        self._insert_text_to_editor(line)

    def _add_show_video(self, script_name: str = None):
        """Inserts a 'show video' line with a mandatory pause using the script name."""
        if not script_name:
             script_name, ok = QInputDialog.getText(self, "Add Show Video", "Enter Video Script Name (e.g., 'vid1', 'my_custom_video'):", 
                                         QLineEdit.Normal, "")
             if not ok or not script_name.strip(): return
             
        line = f'$ current_event.show_video("{script_name}")\npause\n'
        self._insert_text_to_editor(line)

    def _add_menu_block(self):
        """Inserts a menu block template."""
        menu_name, ok = QInputDialog.getText(self, "Menu Block", "Enter name for the menu label (optional, e.g., 'choice_1'):")
        if not ok: return
        
        template = f'menu {"{}_menu:".format(menu_name.strip()) if menu_name.strip() else ":"}\n'
        template += '    "Option 1":\n'
        template += '        # action code here, e.g., $ current_event.impact_stats("player", {"charisma": 1})\n'
        template += '        jump option_1_label\n'
        template += '    "Option 2":\n'
        template += '        pass # <- Edit this line\n\n'
        self._insert_text_to_editor(template)

    # ... (Participant Management functions are kept the same) ...
    def _add_participant(self, initial=False):
        """Adds a new participant to the list and initializes their impact data."""
        p_type = self.participant_type_combo.currentText()
        p_id_suffix = self.participant_id_input.text().strip().lower().replace(' ', '_')
        
        # Generate a unique ID
        if p_type == "player":
            pid = p_type
        elif p_type == "girl":
            pid = p_type
        elif p_id_suffix:
            pid = p_id_suffix 
        else:
            if not initial:
                QMessageBox.warning(self, "Invalid ID", "Please enter an ID suffix for this participant type.")
            return

        current_items = self._get_list_widget_items(self.participants_list)
        if pid in current_items:
            if not initial:
                QMessageBox.warning(self, "Duplicate Participant", f"Participant ID '{pid}' already exists.")
            return

        QListWidgetItem(pid, self.participants_list)
        self._initialize_participant_impact(pid)
        
        if self.impact_participant_combo.itemText(0) == "--- No Participants ---":
             self.impact_participant_combo.clear()

        if self.impact_participant_combo.findText(pid) == -1:
             self.impact_participant_combo.addItem(pid)
             
        self.participant_id_input.clear()
        logger.info(f"Participant added: {pid}")

    def _on_impact_participant_changed(self, pid):
        """Saves old impacts and loads new impacts when participant selection changes."""
        if not pid or "---" in pid:
            self._load_participant_impacts(None)
            self.current_participant_id = None
            return

        if self.current_participant_id and self.current_participant_id != pid:
            self._save_current_participant_impacts()

        self.current_participant_id = pid
        self._load_participant_impacts(pid)

    def _save_current_participant_impacts(self):
        """Gathers and saves the current impacts UI data into self.participant_impacts_data."""
        if not self.current_participant_id: return
        pid = self.current_participant_id
        
        # NOTE: We now explicitly look for the QTableWidget child within the GroupBox
        stats_table = self.participant_stats_table.findChild(QTableWidget) 
        if stats_table is None:
             logger.error(f"Could not find QTableWidget in participant_stats_table for {pid}.")
             stats_dict = {}
        else:
            stats_data = self._get_table_data(stats_table)
            stats_dict = {}
            for row in stats_data:
                if len(row) == 3 and row[0] and row[1].strip() and row[2].strip():
                    try:
                        stats_dict[row[0]] = (int(row[1]), int(row[2]))
                    except ValueError:
                        logger.warning(f"Skipping invalid stat impact range for {pid}: {row}")

        self.participant_impacts_data[pid]['stats'] = stats_dict

        self.participant_impacts_data[pid]['add_traits'] = self._get_list_widget_items(self.traits_to_add_list)
        self.participant_impacts_data[pid]['remove_traits'] = self._get_list_widget_items(self.traits_to_remove_list)
        logger.debug(f"Saved impacts for participant: {pid}")

    def _load_participant_impacts(self, pid):
        """Loads impacts data from self.participant_impacts_data into the UI widgets."""
        self.traits_to_add_list.clear()
        self.traits_to_remove_list.clear()

        # NOTE: We now explicitly look for the QTableWidget child within the GroupBox
        stats_table = self.participant_stats_table.findChild(QTableWidget)
        if stats_table is None:
             logger.error("Could not find QTableWidget to load participant impacts.")
             return
             
        stats_table.setRowCount(0)
        
        if not pid:
            return

        impact_data = self.participant_impacts_data.get(pid, {})
        
        all_stats = []
        if hasattr(self.project_manager, 'get_all_stats'):
            all_stats = self.project_manager.get_all_stats()
        
        for row_index, stat in enumerate(all_stats):
            stats_table.insertRow(row_index)
            min_val, max_val = impact_data['stats'].get(stat, (0, 0))
            
            stats_table.setItem(row_index, 0, QTableWidgetItem(stat))
            stats_table.setItem(row_index, 1, QTableWidgetItem(str(min_val)))
            stats_table.setItem(row_index, 2, QTableWidgetItem(str(max_val)))


        for trait in impact_data.get('add_traits', []):
            QListWidgetItem(trait, self.traits_to_add_list)
        for trait in impact_data.get('remove_traits', []):
            QListWidgetItem(trait, self.traits_to_remove_list)
        logger.debug(f"Loaded impacts for participant: {pid}")

    def _add_trait_to_list(self, combo: QComboBox, target_list: QListWidget):
        """Helper to add the selected trait tag to a target list widget."""
        selected_text = combo.currentText()
        if not selected_text or "---" in selected_text: return
        trait_tag = selected_text
        
        for i in range(target_list.count()):
            if target_list.item(i).text() == trait_tag:
                QMessageBox.warning(self, "Duplicate Trait", f"Trait '{trait_tag}' is already in the list.")
                return

        QListWidgetItem(trait_tag, target_list)
        self._save_current_participant_impacts()

    # ... (Stage / Script Management functions are kept the same) ...
    def _add_stage(self, initial=False, name=None):
        """Adds a new stage (Ren'Py label) to the list."""
        if initial and self.stages_list.count() > 0: return

        if not name:
            new_stage_name = f"stage_{self.stages_list.count() + 1}"
            stage_name_dialog, ok = QInputDialog.getText(self, "New Stage Name", "Enter the Ren'Py label name for the new stage:", QLineEdit.Normal, new_stage_name)
            if ok and stage_name_dialog.strip():
                name = stage_name_dialog.lower().replace(' ', '_').replace('-', '_')
            else:
                if not initial:
                    QMessageBox.warning(self, "Cancelled", "Stage creation cancelled or name was empty.")
                return
        
        if name in self.current_script_data:
            QMessageBox.critical(self, "Error", f"Stage '{name}' already exists.")
            return

        QListWidgetItem(name, self.stages_list)
        self.current_script_data[name] = ""
        self.stages_list.setCurrentRow(self.stages_list.count() - 1)
        logger.info(f"Added new stage: {name}")

    def _remove_stage(self):
        """Removes the selected stage from the list and its script data."""
        current_row = self.stages_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a stage to remove.")
            return
            
        stage_name = self.stages_list.item(current_row).text()
        if stage_name == "start":
            QMessageBox.critical(self, "Error", "The 'start' stage cannot be removed.")
            return
            
        del self.current_script_data[stage_name]
        self.stages_list.takeItem(current_row)
        logger.info(f"Removed stage: {stage_name}")

    def _update_stage_selector(self, current_row):
        """Saves the old stage script and loads the new stage script when selection changes."""
        old_stage = None
        if self.stages_list.count() > 0 and self.script_editor.isVisible():
            for i in range(self.stages_list.count()):
                 if self.stages_list.item(i).isSelected() and i != current_row:
                     old_stage = self.stages_list.item(i).text()
                     break

        if old_stage and old_stage in self.current_script_data:
            self._save_current_stage_script(stage_name=old_stage)

        if current_row >= 0:
            new_stage_name = self.stages_list.item(current_row).text()
            script_content = self.current_script_data.get(new_stage_name, "")
            self.script_editor.setText(script_content)
            logger.debug(f"Loaded script for stage: {new_stage_name}")

    def _save_current_stage_script(self, stage_name=None):
        """Saves the current content of the script editor to the internal data structure."""
        if self.stages_list.currentRow() < 0: return

        if not stage_name:
             current_stage_name = self.stages_list.currentItem().text()
        else:
             current_stage_name = stage_name
        
        self.current_script_data[current_stage_name] = self.script_editor.toPlainText()
        logger.debug(f"Script content saved for stage: {current_stage_name}")
        

    # ... (RPY Generation & Saving functions are kept the same) ...
    def _on_save_event(self):
        """Collects all data and calls the project manager to generate and save files."""
        # 1. Basic Data Collection
        event_name = self.event_name_input.text().strip()
        if not event_name:
            QMessageBox.critical(self, "Error", "Event Internal Name cannot be empty.")
            return

        normalized_event_name = event_name.lower().replace(' ', '_').replace('-', '_')
        girl_id = self.girl_id_input.text().strip()
        # تمت إزالة متغير shoot_name

        # --- 2. Impacts Data Collection (Ensure current impacts are saved) ---
        self._save_current_participant_impacts()
        final_impacts = self.participant_impacts_data 

        # --- 3. Requirements Data Collection ---
        stat_reqs_data = self._get_table_data(self.stat_requirements_table.findChild(QTableWidget))
        stat_requirements_list = []
        for item in stat_reqs_data:
            if len(item) == 4 and item[0] and item[2].strip() and item[3]:
                try:
                    stat_requirements_list.append({
                        "target": item[3],
                        "stat": item[0],
                        "comparator": item[1] if item[1] else ">=",
                        "value": int(item[2])
                    })
                except ValueError:
                    logger.warning(f"Skipping invalid stat requirement value: {item}")

        required_traits_data = self._get_table_data(self.required_traits_table.findChild(QTableWidget))
        forbidden_traits_data = self._get_table_data(self.forbidden_traits_table.findChild(QTableWidget))
        
        required_traits_list = []
        for item in required_traits_data:
             if len(item) == 2 and item[0] and item[1]:
                 required_traits_list.append({"target": item[1], "trait": item[0]})

        forbidden_traits_list = []
        for item in forbidden_traits_data:
             if len(item) == 2 and item[0] and item[1]:
                 forbidden_traits_list.append({"target": item[1], "trait": item[0]})

        action_reqs_table = self.action_reqs_table.findChild(QTableWidget)
        action_reqs_data = self._get_table_data(action_reqs_table)
        action_requirements_dict = {
            item[0]: int(item[1]) for item in action_reqs_data 
            if len(item) == 2 and item[0] and item[1].isdigit()
        }
        
        accept_influences_table = self.accept_influences_table.findChild(QTableWidget)
        accept_influences_data = self._get_table_data(accept_influences_table)
        accept_influences_dict = {
            item[0]: float(item[1]) for item in accept_influences_data
            if len(item) == 2 and item[0] and item[1]
        }
        
        stages_list_from_ui = self._get_list_widget_items(self.stages_list)

        # --- 4. Assemble Final JSON Data ---
        event_data_json = {
            "metadata": {
                "internal_name": normalized_event_name,
                "display_name": self.event_display_name_input.text(),
                "type": self.event_type_combo.currentText(),
                "requirements_description": self.event_reqs_desc_input.text(),
                "stat_requirements": stat_requirements_list,
                "required_traits": required_traits_list,
                "forbidden_traits": forbidden_traits_list,
                "girl_id": girl_id,
                # تمت إزالة "shoot_name": shoot_name,
                "min_chance": self.min_chance_spinbox.value(),
                "max_chance": self.max_chance_spinbox.value(),
                "action_requirements": action_requirements_dict,
                "accept_influences": accept_influences_dict,
                "one_time_event": self.one_time_event_check.isChecked(),
                "reset_outfit": self.reset_outfit_check.isChecked(),
                "hide_in_menus": self.hide_in_menus_check.isChecked(),
                "ignore_frequency": self.ignore_frequency_check.isChecked(),
                "allow_random_trigger": self.allow_random_trigger_check.isChecked(),
                "event_cooldown_days": self.event_cooldown_spinbox.value(),
                "participant_cooldown_days": self.participant_cooldown_spinbox.value(),
                "participants": self._get_list_widget_items(self.participants_list),
            },
            "impacts": final_impacts,
            "stages": stages_list_from_ui
        }
        
        # --- 5. RPY Script Generation ---\
        rpy_content = self._generate_rpy_script_content(normalized_event_name)
        
        # --- 6. Save Files ---
        if self._write_files_to_disk(normalized_event_name, event_data_json, rpy_content):
            QMessageBox.information(self, "Success", f"Event '{event_name}' saved successfully.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save event files. Check logs.")

    def _generate_rpy_script_content(self, normalized_event_name):
        """Generates the full Ren'Py script content from all stages."""
        logger.info(f"Generating RPY script content for {normalized_event_name}...")
        rpy_script = f"# Ren'Py Event Script Generated by EventMakerPanel\n"
        rpy_script += f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        rpy_script += f"# Event: {self.event_display_name_input.text()}\n"
        rpy_script += f"# Internal Name: {normalized_event_name}\n\n"

        self._save_current_stage_script()
        
        stage_names = self._get_list_widget_items(self.stages_list)
        
        # 1. Define image/video assets at the top of the RPY script
        rpy_script += "# --- Asset Definitions (Based on Media Library) ---\n"
        for script_name, info in self.available_assets.items():
            rpy_script += f'image {script_name} = "{info["rpy_path_hint"]}"\n'
        rpy_script += "\n"
        
        # 2. Add event label definitions
        for stage_name in stage_names:
            content = self.current_script_data.get(stage_name, "").strip()
            
            rpy_script += f"label {stage_name}_{normalized_event_name}:\n"
            
            if stage_name == stage_names[0] and "girl" in self._get_list_widget_items(self.participants_list):
                 rpy_script += f"    $ selected_girl = current_event.participants[0]\n\n"

            if content:
                indented_content = '\n'.join(['    ' + line for line in content.split('\n')])
                rpy_script += indented_content + '\n'
            else:
                rpy_script += "    # Start of stage script\n"
            
            content_lower = content.lower().strip()
            if not content_lower.endswith('return') and not content_lower.endswith('pass'):
                rpy_script += "    return\n\n"
            else:
                 rpy_script += '\n' 

        return rpy_script

    def _write_files_to_disk(self, event_name, event_data_json, rpy_content):
        """Calls the project manager to save the generated JSON and RPY files."""
        try:
            # تم تعديل اسم الدالة المتوقعة إلى 'save_event_definition' بناءً على الخطأ في السجل
            if hasattr(self.project_manager, 'save_event_definition'): 
                self.project_manager.save_event_definition(
                    event_name, 
                    event_data_json, 
                    {"script_content": rpy_content} 
                )
                return True
            else:
                # تم تحديث رسالة الخطأ لتعكس اسم الدالة الصحيح
                raise AttributeError("Project Manager is missing 'save_event_definition' method.")
        except Exception as e:
            logger.error(f"Error saving event files: {type(e).__name__}: {e}")
            return False