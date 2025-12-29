from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QGroupBox, QHBoxLayout, QMessageBox
from PySide6.QtCore import Signal, QUrl
from PySide6.QtGui import QDesktopServices
import os
from tools.logger import get_logger

logger = get_logger("SettingsPanel")


class SettingsPanel(QWidget):
    back_requested = Signal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout(self)
        title = QLabel("⚙️ Settings")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        theme_group = QGroupBox("Theme")
        th_layout = QHBoxLayout(theme_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "classic", "muted_steel", "muted_forest"])
        th_layout.addWidget(QLabel("Select Theme:"))
        th_layout.addWidget(self.theme_combo)
        layout.addWidget(theme_group)

        pro_group = QGroupBox("Pro Activation")
        p_layout = QHBoxLayout(pro_group)
        self.pro_status = QLabel("Pro: Unknown")
        self.open_license_button = QPushButton("Enter License")
        p_layout.addWidget(self.pro_status)
        p_layout.addWidget(self.open_license_button)
        layout.addWidget(pro_group)

        back_btn = QPushButton("⬅️ Back")
        layout.addWidget(back_btn)

        # Load saved theme
        try:
            current = self.main_window.settings.value("theme", "light")
            idx = self.theme_combo.findText(current)
            if idx >= 0:
                self.theme_combo.setCurrentIndex(idx)
        except Exception:
            pass

        back_btn.clicked.connect(self.back_requested.emit)
        self.open_license_button.clicked.connect(self._enter_license)
        self.theme_combo.currentTextChanged.connect(self._on_theme_change)

        # Theme Manager extras
        theme_manage_group = QGroupBox("Theme Manager")
        tmg_layout = QHBoxLayout(theme_manage_group)
        self.refresh_themes_btn = QPushButton("Refresh Themes")
        self.open_themes_folder_btn = QPushButton("Open Themes Folder")
        tmg_layout.addWidget(self.refresh_themes_btn)
        tmg_layout.addWidget(self.open_themes_folder_btn)
        layout.addWidget(theme_manage_group)

        self.refresh_themes_btn.clicked.connect(self._refresh_themes)
        self.open_themes_folder_btn.clicked.connect(self._open_themes_folder)

    def _refresh_themes(self):
        try:
            base = os.path.join(os.getcwd(), "gui", "themes")
            if os.path.exists(base):
                files = [f for f in os.listdir(base) if f.endswith(".qss")]
                names = [os.path.splitext(f)[0] for f in files]
                self.theme_combo.clear()
                self.theme_combo.addItems(names)
        except Exception as e:
            logger.error(f"Failed to refresh themes: {e}")

    def _open_themes_folder(self):
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(os.getcwd(), "gui", "themes")))
        except Exception:
            QMessageBox.warning(self, "Open Folder", "Could not open themes folder.")

    def _enter_license(self):
        # open auto pack activation dialog for convenience
        self.main_window.workflow_manager.go_to("auto_pack")
        QMessageBox.information(self, "License", "Use the Auto-Pack panel to enter and activate your license key.")

    def _on_theme_change(self, theme_name: str):
        try:
            self.main_window.apply_theme(theme_name)
            self.main_window.settings.setValue("theme", theme_name)
        except Exception as e:
            logger.error(f"Failed to change theme: {e}")
