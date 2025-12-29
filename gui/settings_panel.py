
from PySide6.QtCore import Signal
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
        self.theme_combo.addItems(["light", "dark", "classic"])
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

        back_btn.clicked.connect(self.back_requested.emit)
        self.open_license_button.clicked.connect(self._enter_license)

    def _enter_license(self):
        # open auto pack activation dialog for convenience
        dlg = self.main_window.auto_pack_panel
        self.main_window.workflow_manager.go_to("auto_pack")
        QMessageBox.information(self, "License", "Use the Auto-Pack panel to enter and activate your license key.")

```