# GameMediaTool/gui/dashboard_panel.py (MODIFIED to add Event Maker button and enable all buttons on project load)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QLabel,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
import os


class DashboardPanel(QWidget):
    # Consolidated signals
    generate_vids_requested = Signal()
    photo_maker_requested = Signal()
    shoot_maker_requested = Signal()
    event_maker_requested = Signal()  # [NEW] Signal for the new button
    ai_center_requested = Signal()
    export_pack_requested = Signal()
    path_change_requested = Signal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        main_layout = QVBoxLayout(self)

        # --- Status Group (at the top) ---
        status_group = QGroupBox("Project Status")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel("No active project. Please use the setup screen to start.")
        status_layout.addWidget(self.status_label)
        main_layout.addWidget(status_group)

        # --- Main Workflows Group (in the center) ---
        center_layout = QHBoxLayout()
        workflows_group = QGroupBox("Main Workflows")
        workflows_layout = QGridLayout(workflows_group)

        self.vids_button = QPushButton("🎬 Vid Maker (Create Clips)")
        self.photo_maker_button = QPushButton("🖼️ Photo Maker (Extract Frames)")
        self.shoot_maker_button = QPushButton("📖 Shoot Maker (Create Shoots)")
        self.event_maker_button = QPushButton(
            "✨ Event Maker (Create Events)"
        )  # [NEW] The new button
        self.ai_button = QPushButton("🧠 AI Training Center")

        workflows_layout.addWidget(self.vids_button, 0, 0)
        workflows_layout.addWidget(self.photo_maker_button, 0, 1)
        workflows_layout.addWidget(self.shoot_maker_button, 1, 0)
        workflows_layout.addWidget(self.event_maker_button, 1, 1)  # [NEW] Added to the grid
        workflows_layout.addWidget(self.ai_button, 2, 0, 1, 2)

        center_layout.addStretch()
        center_layout.addWidget(workflows_group)
        center_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()

        # --- Export Section (moved to the bottom) ---
        export_section_group = QGroupBox("Final Export")
        export_section_layout = QVBoxLayout(export_section_group)

        export_path_layout = QHBoxLayout()
        export_path_layout.addWidget(QLabel("Output Path:"))
        self.output_path_label = QLineEdit()
        self.output_path_label.setReadOnly(True)
        export_path_layout.addWidget(self.output_path_label)
        self.browse_button = QPushButton("Browse...")
        export_path_layout.addWidget(self.browse_button)
        export_section_layout.addLayout(export_path_layout)

        self.export_button = QPushButton("📦 Assemble & Export Final Pack")
        self.export_button.setObjectName("ConfirmButton")
        export_section_layout.addWidget(self.export_button)

        main_layout.addWidget(export_section_group)

        # --- Support Section ---
        support_group = QGroupBox("Support the Project")
        support_layout = QVBoxLayout(support_group)
        self.coffee_button = QPushButton("☕ Buy Me a Coffee")
        self.coffee_button.setToolTip("Support the developer on GitHub Sponsors or Patreon")
        support_layout.addWidget(self.coffee_button)
        main_layout.addWidget(support_group)

        # --- Connect Signals ---
        self.vids_button.clicked.connect(self.generate_vids_requested)
        self.photo_maker_button.clicked.connect(self.photo_maker_requested)
        self.shoot_maker_button.clicked.connect(self.shoot_maker_requested)
        self.event_maker_button.clicked.connect(
            self.event_maker_requested
        )  # [NEW] Connect the signal
        self.ai_button.clicked.connect(self.ai_center_requested)
        self.export_button.clicked.connect(self.export_pack_requested)
        self.browse_button.clicked.connect(self.path_change_requested)
        self.coffee_button.clicked.connect(self.open_support_link)

        # [MODIFIED] Add the new button to the list to be managed
        self.all_buttons = [
            self.vids_button,
            self.photo_maker_button,
            self.shoot_maker_button,
            self.event_maker_button,
            self.ai_button,
            self.export_button,
        ]
        self.disable_all_buttons()

    def update_status(self, project):
        """
        Updates the status label and enables/disables buttons based on the project status.
        """
        if project and project.character_name:
            source_text = (
                os.path.basename(project.source_video_path)
                if project.source_video_path
                else "Image Folder"
            )
            self.status_label.setText(
                f"<b>Project:</b> {project.character_name} ({project.character_type}) | <b>Source:</b> {source_text}"
            )
            self.output_path_label.setText(project.final_output_path)
            # --- [NEW] Enable buttons when a project is loaded ---
            # Note: MainWindow's _update_dashboard_state manages specific video/non-video button states.
            for button in self.all_buttons:
                button.setEnabled(True)
            # --------------------------------------------------
        else:
            self.status_label.setText("No active project.")
            self.output_path_label.clear()
            self.disable_all_buttons()

    def disable_all_buttons(self):
        for button in self.all_buttons:
            button.setEnabled(False)

    def open_support_link(self):
        """Open the support link in the default browser."""
        url = QUrl("https://www.patreon.com/15309479/join")  # Or Patreon link
        QDesktopServices.openUrl(url)
