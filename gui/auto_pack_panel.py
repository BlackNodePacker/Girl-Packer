from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QHBoxLayout,
    QFileDialog,
    QComboBox,
    QCheckBox,
    QMessageBox,
)
from PySide6.QtCore import Signal, QThread
from tools.logger import get_logger
from utils.pro_verifier import verify_license
from workflows.auto_pack_workflow import AutoPackWorkflow

logger = get_logger("AutoPackPanel")


class AutoPackPanel(QWidget):
    back_requested = Signal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.workflow_thread = None
        self.workflow_worker = None

        main_layout = QVBoxLayout(self)
        title = QLabel("🚀 Auto-Pack (Pro)")
        title.setObjectName("TitleLabel")
        main_layout.addWidget(title)

        # License / Pro activation
        prox_group = QGroupBox("Pro Activation")
        prox_layout = QHBoxLayout(prox_group)
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Paste license key (from Patreon/GitHub)")
        self.activate_button = QPushButton("Activate")
        prox_layout.addWidget(self.license_input)
        prox_layout.addWidget(self.activate_button)
        main_layout.addWidget(prox_group)

        # Source selection
        src_group = QGroupBox("Source & Options")
        src_layout = QVBoxLayout(src_group)
        folder_h = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.browse_button = QPushButton("Browse Folder")
        folder_h.addWidget(self.folder_input)
        folder_h.addWidget(self.browse_button)
        src_layout.addLayout(folder_h)

        # Pack type
        type_h = QHBoxLayout()
        type_h.addWidget(QLabel("Pack Type:"))
        self.pack_type = QComboBox()
        self.pack_type.addItems(["Min", "Mid", "Top"])
        type_h.addWidget(self.pack_type)
        src_layout.addLayout(type_h)

        # Components
        comp_group = QGroupBox("Components to extract")
        comp_layout = QVBoxLayout(comp_group)
        self.c_body = QCheckBox("Body parts")
        self.c_clothing = QCheckBox("Clothing")
        self.c_events = QCheckBox("Events")
        self.c_photos = QCheckBox("Photoshoots (frames)")
        self.c_videos = QCheckBox("Video shoots (split clips)")
        self.c_fullbody = QCheckBox("Fullbody images")
        for w in [self.c_body, self.c_clothing, self.c_events, self.c_photos, self.c_videos, self.c_fullbody]:
            comp_layout.addWidget(w)
        src_layout.addWidget(comp_group)

        main_layout.addWidget(src_group)

        # Run / Back
        bottom_h = QHBoxLayout()
        self.start_button = QPushButton("Start Auto-Pack")
        self.back_button = QPushButton("⬅️ Back")
        bottom_h.addWidget(self.back_button)
        bottom_h.addStretch()
        bottom_h.addWidget(self.start_button)
        main_layout.addLayout(bottom_h)

        # Connect
        self.back_button.clicked.connect(self.back_requested.emit)
        self.browse_button.clicked.connect(self._browse_folder)
        self.start_button.clicked.connect(self._start_autopack)
        self.activate_button.clicked.connect(self._activate_license)

    def _browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if path:
            self.folder_input.setText(path)

    def _activate_license(self):
        key = self.license_input.text().strip()
        if not key:
            QMessageBox.warning(self, "No Key", "Please paste your license key.")
            return
        # Attempt remote verification if configured, otherwise save locally as provisional
        verify_url = self.main_window.config.get("pro", {}).get("verify_url")
        valid = False
        if verify_url:
            QMessageBox.information(self, "Verifying", "Verifying license with server...")
            valid = verify_license(key, verify_url=verify_url)
        # Persist license and set project state immediately
        try:
            self.main_window.settings.setValue("pro_license", key)
        except Exception:
            pass

        if valid:
            try:
                self.main_window.settings.setValue("pro_active", True)
            except Exception:
                pass
            # Immediately update project state so dashboard and buttons reflect Pro
            try:
                self.main_window.project.pro_user = True
            except Exception:
                pass
            QMessageBox.information(self, "Activated", "Pro license verified and saved.")
        else:
            # fallback: save locally but mark as not verified
            try:
                self.main_window.settings.setValue("pro_active", False)
            except Exception:
                pass
            try:
                self.main_window.project.pro_user = False
            except Exception:
                pass
            QMessageBox.information(
                self,
                "Saved (Unverified)",
                "License saved locally but not verified. You can activate online later.",
            )

    def _start_autopack(self):
        src = self.folder_input.text().strip()
        if not src or not src:
            QMessageBox.warning(self, "No Source", "Please select a source folder.")
            return

        options = {
            "pack_type": self.pack_type.currentText(),
            "components": {
                "body": self.c_body.isChecked(),
                "clothing": self.c_clothing.isChecked(),
                "events": self.c_events.isChecked(),
                "photos": self.c_photos.isChecked(),
                "videos": self.c_videos.isChecked(),
                "fullbody": self.c_fullbody.isChecked(),
            },
            "source_folder": src,
        }

        self.workflow_thread = QThread()
        self.workflow_worker = AutoPackWorkflow(self.main_window, options)
        self.workflow_worker.moveToThread(self.workflow_thread)

        self.workflow_thread.started.connect(self.workflow_worker.run)
        self.workflow_worker.finished.connect(self._on_finished)
        self.workflow_worker.finished.connect(self.workflow_thread.quit)
        self.workflow_worker.finished.connect(self.workflow_worker.deleteLater)
        self.workflow_thread.finished.connect(self.workflow_thread.deleteLater)

        self.workflow_thread.start()
        QMessageBox.information(self, "Auto-Pack", "Auto-Pack workflow started. Check logs for progress.")

    def _on_finished(self, success, message):
        if success:
            QMessageBox.information(self, "Auto-Pack Complete", message)
            # After completion, refresh data review and move to Pack Review
            try:
                self.main_window.data_review_panel.activate()
            except Exception:
                pass
            self.main_window.workflow_manager.go_to("pack_review")
        else:
            QMessageBox.warning(self, "Auto-Pack Failed", message)
