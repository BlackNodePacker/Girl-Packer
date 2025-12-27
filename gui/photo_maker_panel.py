# GameMediaTool/gui/photo_maker_panel.py (Complete and Corrected)

# [MODIFIED] Added QPushButton to the import list
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox, QPushButton
from PySide6.QtCore import Signal

from .components import ContactSheetPanel
from .components import ImageWorkshopPanel

from tools.logger import get_logger

logger = get_logger("PhotoMakerPanel_UI")


class PhotoMakerPanel(QWidget):
    """
    The UI-only panel for the Photo Maker workflow.
    It contains the ContactSheet and Workshop sub-panels and emits signals
    to a workflow controller, but contains no background logic itself.
    """

    back_requested = Signal()
    yolo_analysis_requested = Signal(list)
    final_processing_requested = Signal(dict)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.project = main_window.project

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.step_stack = QStackedWidget()
        main_layout.addWidget(self.step_stack)

        self.contact_sheet_step = ContactSheetPanel(self.main_window)
        self.image_workshop_step = ImageWorkshopPanel(self.main_window)

        self.step_stack.addWidget(self.contact_sheet_step)
        self.step_stack.addWidget(self.image_workshop_step)

        self.back_button = QPushButton("⬅️ Back to Dashboard")
        main_layout.addWidget(self.back_button)

        self._connect_internal_signals()

    def _connect_internal_signals(self):
        """Connects signals between the internal steps and this panel's main signals."""
        self.contact_sheet_step.frames_confirmed.connect(self.yolo_analysis_requested)
        self.image_workshop_step.back_requested.connect(self.go_to_contact_sheet)
        self.image_workshop_step.processing_requested.connect(self.final_processing_requested)
        self.back_button.clicked.connect(self.back_requested.emit)

    def activate_and_load_frames(self, source_frames: list):
        """
        Called by MainWindow to start this UI workflow.
        It loads the initial set of frames/images into the contact sheet.
        """
        if not source_frames:
            QMessageBox.critical(
                self, "Error", "Photo Maker was started with no source frames or images."
            )
            self.back_requested.emit()
            return

        logger.info(f"Photo Maker UI activated with {len(source_frames)} source frames.")
        self.contact_sheet_step.load_frames(source_frames)
        self.go_to_contact_sheet()

    def go_to_contact_sheet(self):
        """Switches the view to the contact sheet panel."""
        self.step_stack.setCurrentWidget(self.contact_sheet_step)

    def go_to_workshop(self, yolo_results, selected_paths, tasks):
        """Switches to the workshop panel and loads it with AI data."""
        self.image_workshop_step.load_data(selected_paths, yolo_results, tasks)
        self.step_stack.setCurrentWidget(self.image_workshop_step)

    def on_final_processing_finished(self, final_processed_images: list):
        """Receives the final results from the controller and shows a success message."""
        logger.info(f"UI received {len(final_processed_images)} processed images.")

        project_data = self.main_window.project.export_data
        if "approved_images" not in project_data:
            project_data["approved_images"] = []
        project_data["approved_images"].extend(final_processed_images)

        QMessageBox.information(
            self,
            "Success",
            f"Successfully created {len(final_processed_images)} final image assets!",
        )
        self.back_requested.emit()
