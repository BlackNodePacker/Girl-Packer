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
    QMessageBox,
)
from PySide6.QtGui import QIcon, QPixmap
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
    auto_pack_requested = Signal()
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
        self.auto_pack_button = QPushButton("🚀 Auto-Pack (Pro)")
        self.ai_button = QPushButton("🧠 AI Training Center")

        workflows_layout.addWidget(self.vids_button, 0, 0)
        workflows_layout.addWidget(self.photo_maker_button, 0, 1)
        workflows_layout.addWidget(self.shoot_maker_button, 1, 0)
        workflows_layout.addWidget(self.event_maker_button, 1, 1)  # [NEW] Added to the grid
        workflows_layout.addWidget(self.auto_pack_button, 2, 0)
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
        support_group = QGroupBox("Support & Tools")
        support_layout = QVBoxLayout(support_group)

        # Donation buttons (Patreon + GitHub Sponsors)
        donate_h = QHBoxLayout()
        self.patreon_button = QPushButton("Patreon")
        self.patreon_button.setFlat(True)
        self.github_button = QPushButton("GitHub Sponsors")
        self.github_button.setFlat(True)
        # Try to load icon assets from known locations
        try:
            base_icons = [
                os.path.join(os.getcwd(), "icons"),
                os.path.join(os.getcwd(), "assets", "icons"),
                os.path.join(os.getcwd(), "gui", "icons"),
            ]
            for base in base_icons:
                patreon_path = os.path.join(base, "patreon.png")
                gh_path = os.path.join(base, "github.png")
                if os.path.exists(patreon_path):
                    self.patreon_button.setIcon(QIcon(QPixmap(patreon_path)))
                if os.path.exists(gh_path):
                    self.github_button.setIcon(QIcon(QPixmap(gh_path)))
                # if we found at least one, break
                if os.path.exists(patreon_path) or os.path.exists(gh_path):
                    break
        except Exception:
            pass
        donate_h.addWidget(self.patreon_button)
        donate_h.addWidget(self.github_button)
        support_layout.addLayout(donate_h)

        # Report Bug button
        self.report_bug_button = QPushButton("🐞 Report Bug")
        support_layout.addWidget(self.report_bug_button)

        # Settings shortcut
        self.settings_button = QPushButton("⚙️ Settings")
        support_layout.addWidget(self.settings_button)

        main_layout.addWidget(support_group)

        # --- Connect Signals ---
        self.vids_button.clicked.connect(self.generate_vids_requested)
        self.photo_maker_button.clicked.connect(self.photo_maker_requested)
        self.shoot_maker_button.clicked.connect(self.shoot_maker_requested)
        self.event_maker_button.clicked.connect(
            self.event_maker_requested
        )  # [NEW] Connect the signal
        # Auto-pack should be gated: open upgrade info when not a pro user
        self.auto_pack_button.clicked.connect(self._on_auto_pack_clicked)
        self.ai_button.clicked.connect(self.ai_center_requested)
        self.export_button.clicked.connect(self.export_pack_requested)
        self.browse_button.clicked.connect(self.path_change_requested)
        self.patreon_button.clicked.connect(self.open_patreon_link)
        self.github_button.clicked.connect(self.open_github_sponsors_link)
        self.report_bug_button.clicked.connect(self._open_report_bug)
        self.settings_button.clicked.connect(self._open_settings)

        # [MODIFIED] Add the new button to the list to be managed
        self.all_buttons = [
            self.vids_button,
            self.photo_maker_button,
            self.shoot_maker_button,
            self.event_maker_button,
            self.auto_pack_button,
            self.ai_button,
            self.export_button,
        ]
        self.disable_all_buttons()

    def _open_settings(self):
        # Signal to MainWindow is not defined here; use direct navigation if available
        try:
            self.main_window.workflow_manager.go_to("settings")
        except Exception:
            pass

    def _on_auto_pack_clicked(self):
        """Emit the request only for pro users, otherwise prompt upgrade."""
        proj = getattr(self.main_window, "project", None)
        is_pro = False
        if proj and hasattr(proj, "pro_user"):
            try:
                is_pro = bool(getattr(proj, "pro_user"))
            except Exception:
                is_pro = False

        if is_pro:
            try:
                self.auto_pack_requested.emit()
            except Exception:
                # Fallback: navigate to the panel
                try:
                    self.main_window.workflow_manager.go_to("auto_pack")
                except Exception:
                    pass
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Auto-Pack (Pro)")
            msg.setText(
                "Auto-Pack is a Pro feature.\n\nUpgrade to access Auto-Pack automation and batch exports."
            )
            upgrade_button = msg.addButton("Learn More", QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Ok)
            msg.exec()
            if msg.clickedButton() == upgrade_button:
                try:
                    self.main_window.open_url(self.main_window.config.get("pro_info_url", "https://patreon.com"))
                except Exception:
                    pass

    def open_patreon_link(self):
        try:
            self.main_window.open_url(
                "https://patreon.com/Black_nod835?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink"
            )
        except Exception:
            pass

    def open_github_sponsors_link(self):
        try:
            # Link directly to the release as requested
            self.main_window.open_url(
                "https://github.com/BlackNodePacker/Girl-Packer/releases/tag/v1.0.0-pre"
            )
        except Exception:
            pass

    def _open_report_bug(self):
        try:
            self.main_window.show_report_dialog()
        except Exception:
            pass

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
            # Gate Auto-Pack to pro users
            is_pro = bool(getattr(self.main_window.project, "pro_user", False))
            self.auto_pack_button.setEnabled(bool(is_pro))
            if not is_pro:
                self.auto_pack_button.setToolTip("Pro feature — upgrade to enable Auto-Pack")
            else:
                self.auto_pack_button.setToolTip("Run Auto-Pack automation")
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
