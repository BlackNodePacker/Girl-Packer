# GameMediaTool/gui/main_window.py (Corrected typo in export thread cleanup)

import os
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QMessageBox,
    QProgressDialog,
    QDialog,
    QFileDialog,
)
from PySide6.QtCore import QSettings, QThread, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication

from .dashboard_panel import DashboardPanel
from .ai_training_panel import AITrainingPanel
from .data_review_panel import DataReviewPanel
from .vids_maker_panel import VidsMakerPanel
from .photo_maker_panel import PhotoMakerPanel
from .shoot_maker_panel import ShootMakerPanel
from .character_setup_panel import CharacterSetupPanel
from .event_maker_panel import EventMakerPanel  # [NEW] Import the new panel
from .auto_pack_panel import AutoPackPanel
from .pack_review_panel import PackReviewPanel
from .settings_panel2 import SettingsPanel
from .report_bug_dialog import ReportBugDialog
from .components import ExportWorker, FrameExtractionDialog
from tools.logger import get_logger
from tools import video_splitter
from utils.config_loader import load_config
from utils.tag_manager import TagManager
from ai.pipeline import Pipeline
from project_data import Project
from workflows.workflow_manager import WorkflowManager
from workflows.photo_maker_workflow import PhotoMakerWorkflow
from workflows.vid_maker_workflow import VidMakerWorkflow
from workflows.shoot_maker_workflow import ShootMakerWorkflow
from utils.pro_verifier import verify_license

logger = get_logger("MainWindow")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initializing MainWindow")
        self.config = load_config()
        logger.debug(f"Config loaded: {self.config}")
        self.settings = QSettings("GameMediaTool", "GirlPacker")
        self.project = Project()
        # Initialize pro_user from settings; attempt remote verification if configured
        try:
            stored_license = self.settings.value("pro_license", "")
            pro_active_setting = self.settings.value("pro_active", False)
            # Default to boolean for stored flag
            pro_active_flag = bool(pro_active_setting) if pro_active_setting is not None else False
            verify_url = self.config.get("pro", {}).get("verify_url") if isinstance(self.config, dict) else None
            if stored_license and verify_url:
                try:
                    valid = verify_license(stored_license, verify_url=verify_url)
                    self.project.pro_user = bool(valid)
                    self.settings.setValue("pro_active", bool(valid))
                except Exception:
                    self.project.pro_user = bool(pro_active_flag)
            else:
                # Use stored flag if no remote verification configured
                self.project.pro_user = bool(pro_active_flag)
        except Exception:
            self.project.pro_user = False
        logger.info("Project instance created")
        self.tag_manager = TagManager()
        logger.info("TagManager initialized")
        self.pipeline = Pipeline(self.tag_manager)
        logger.info("AI Pipeline initialized")

        self.photo_maker_workflow = PhotoMakerWorkflow(self)
        self.vid_maker_workflow = VidMakerWorkflow(self)
        self.shoot_maker_workflow = ShootMakerWorkflow(self)

        self._setup_ui_panels()
        self.workflow_manager = WorkflowManager(self, self.view_stack)
        self._connect_signals()
        # Apply saved theme
        try:
            saved_theme = self.settings.value("theme", "light")
            self.apply_theme(saved_theme)
        except Exception:
            pass

        self._report_dialog = None

    # **********************************************
    # * NEW METHODS FOR EVENTMAKERPANEL INTERFACE *
    # **********************************************

    # [FIXED INDENTATION]
    def get_asset_file_paths(self):
        """
        Called by EventMakerPanel to list available media files.
        FIX: Now calls the corrected method in self.project.
        """
        logger.debug("Retrieving asset file paths")
        paths = self.project.get_asset_file_paths()
        logger.info(f"Found {len(paths)} asset file paths")
        return paths

    # [FIXED INDENTATION]
    def get_all_traits(self):
        """
        Returns a list of all available traits from the TagManager.
        Used by EventMakerPanel to populate trait comboboxes.
        """
        logger.debug("Retrieving all traits")
        traits = self.tag_manager.get_all_traits()
        logger.info(f"Retrieved {len(traits)} trait categories")
        return traits

    # [FIXED INDENTATION]
    def save_event_files(self, event_name, event_data_json, rpy_content):
        """
        Saves the event configuration JSON and the Ren'Py script to the project directory.
        Used by EventMakerPanel when the user clicks 'Save Event'.
        """
        logger.info(f"Saving event files for event: {event_name}")
        # نستخدم TagManager لحفظ الـ JSON
        self.tag_manager.save_event_definition(event_name, event_data_json)
        logger.debug("Event JSON saved via TagManager")
        # نستخدم Project لحفظ ملف Ren'Py Script
        self.project.save_event_files(event_name, event_data_json, rpy_content)
        logger.info("Event RPY script saved successfully")
        # Note: self.project.save_event_files must be implemented in the Project class

    # **********************************************
    # * END OF NEW METHODS *
    # **********************************************

    def _setup_ui_panels(self):
        self.setWindowTitle("Girl Packer v2.6 - Feature Complete")
        self.setGeometry(100, 100, 1500, 950)
        self.setMinimumSize(1280, 800)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.setCentralWidget(self.main_widget)

        self.view_stack = QStackedWidget()
        self.main_layout.addWidget(self.view_stack)

        self.setup_panel = CharacterSetupPanel(self)
        self.dashboard_panel = DashboardPanel(self)
        self.ai_training_panel = AITrainingPanel(self)
        self.data_review_panel = DataReviewPanel(self)
        self.settings_panel = SettingsPanel(self)
        self.auto_pack_panel = AutoPackPanel(self)
        self.pack_review_panel = PackReviewPanel(self)
        self.vids_maker_panel = VidsMakerPanel(self)
        self.photo_maker_panel = PhotoMakerPanel(self)
        self.shoot_maker_panel = ShootMakerPanel(self)
        # [MODIFIED] Pass 'self' (MainWindow) as the project_manager interface
        self.event_maker_panel = EventMakerPanel(self)

        # [MODIFIED] Add the new panel to the list of widgets for the stack
        panels_to_add = [
            self.setup_panel,
            self.dashboard_panel,
            self.ai_training_panel,
            self.settings_panel,
            self.auto_pack_panel,
            self.pack_review_panel,
            self.data_review_panel,
            self.vids_maker_panel,
            self.photo_maker_panel,
            self.shoot_maker_panel,
            self.event_maker_panel,
        ]
        for panel in panels_to_add:
            self.view_stack.addWidget(panel)

        self.view_stack.setCurrentWidget(self.setup_panel)

    def _connect_signals(self):
        self.setup_panel.project_started.connect(self.go_to_dashboard)

        self.dashboard_panel.generate_vids_requested.connect(self.start_vid_maker_workflow)
        self.dashboard_panel.photo_maker_requested.connect(self.start_photo_maker_workflow)
        self.dashboard_panel.shoot_maker_requested.connect(self.start_shoot_maker_workflow)
        self.dashboard_panel.event_maker_requested.connect(
            self.start_event_maker_workflow
        )  # [NEW] Connect the dashboard signal
        self.dashboard_panel.auto_pack_requested.connect(self.start_auto_pack_workflow)

        self.dashboard_panel.export_pack_requested.connect(self._start_final_export)
        self.dashboard_panel.ai_center_requested.connect(
            lambda: self.workflow_manager.go_to("ai_center")
        )
        self.dashboard_panel.path_change_requested.connect(self._change_output_path)

        self.photo_maker_panel.yolo_analysis_requested.connect(self.start_yolo_analysis)
        self.photo_maker_panel.final_processing_requested.connect(
            self.photo_maker_workflow.run_final_processing
        )
        self.photo_maker_workflow.extraction_finished.connect(self._on_extraction_finished)
        self.photo_maker_workflow.yolo_analysis_finished.connect(self._on_yolo_finished)
        self.photo_maker_workflow.final_processing_finished.connect(
            self.photo_maker_panel.on_final_processing_finished
        )
        self.photo_maker_panel.back_requested.connect(self.go_to_dashboard)

        self.vids_maker_panel.splitting_requested.connect(self.start_video_splitting)
        self.vid_maker_workflow.splitting_finished.connect(self._on_splitting_finished)
        self.vids_maker_panel.export_complete.connect(self._update_dashboard_state)
        self.vids_maker_panel.back_requested.connect(self.go_to_dashboard)

        self.shoot_maker_panel.sources_requested.connect(
            self.shoot_maker_workflow.load_available_sources
        )
        self.shoot_maker_panel.ai_analysis_requested.connect(
            self.shoot_maker_workflow.run_ai_analysis_for_suggestions
        )
        self.shoot_maker_panel.save_shoot_requested.connect(self._on_save_shoot_requested)
        self.shoot_maker_workflow.available_sources_loaded.connect(
            self.shoot_maker_panel.display_sources
        )
        self.shoot_maker_workflow.ai_suggestions_ready.connect(
            self.shoot_maker_panel.apply_ai_suggestions
        )
        self.shoot_maker_panel.back_requested.connect(self.go_to_dashboard)

        self.event_maker_panel.back_requested.connect(
            self.go_to_dashboard
        )  # [NEW] Connect the back button for the new panel

        self.ai_training_panel.back_to_dashboard.connect(self.go_to_dashboard)
        self.ai_training_panel.review_data_requested.connect(
            lambda: self.workflow_manager.go_to("data_review")
        )

    def start_auto_pack_workflow(self):
        self.workflow_manager.go_to("auto_pack")
        # Panel handles its own activation

    def go_to_dashboard(self):
        if self.project.source_type == "video" and self.project.video_duration == 0:
            try:  # Add try-except block for robustness
                self.project.video_duration = video_splitter.get_video_duration(
                    self.project.source_video_path
                )
            except Exception as e:
                logger.error(f"Failed to get video duration on going to dashboard: {e}")
                self.project.video_duration = 0  # Ensure it has a value even on error
        self.view_stack.setCurrentWidget(self.dashboard_panel)
        self._update_dashboard_state()

    def _update_dashboard_state(self):
        project = self.project
        dashboard = self.dashboard_panel

        dashboard.disable_all_buttons()

        if project.character_name:
            source_is_video = project.source_type == "video"

            dashboard.vids_button.setEnabled(source_is_video)
            dashboard.photo_maker_button.setEnabled(True)
            dashboard.shoot_maker_button.setEnabled(True)
            dashboard.event_maker_button.setEnabled(True)  # [NEW] Enable the event maker button
            dashboard.ai_button.setEnabled(True)

            if project.is_ready_for_export():
                dashboard.export_button.setEnabled(True)

    # [NEW] Add the workflow start method for the event maker
    def start_event_maker_workflow(self):
        self.workflow_manager.go_to("event_maker")
        self.event_maker_panel.activate()

    # --- All other methods remain unchanged, included for completeness ---
    def _change_output_path(self):
        new_path = QFileDialog.getExistingDirectory(
            self, "Select Final Output Directory", self.project.final_output_path
        )
        if new_path:
            self.project.final_output_path = new_path
            self.settings.setValue("final_output_path", new_path)
            self.dashboard_panel.output_path_label.setText(new_path)

    def open_url(self, url: str):
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")

    def show_report_dialog(self):
        if not self._report_dialog:
            self._report_dialog = ReportBugDialog(self)
        self._report_dialog.exec()

    def apply_theme(self, theme_name: str):
        """Load QSS from `gui/themes/{theme_name}.qss` and apply to QApplication."""
        try:
            base = os.path.join(os.getcwd(), "gui", "themes")
            qss_path = os.path.join(base, f"{theme_name}.qss")
            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as f:
                    qss = f.read()
                QApplication.instance().setStyleSheet(qss)
                self.settings.setValue("theme", theme_name)
                logger.info(f"Applied theme: {theme_name}")
            else:
                logger.warning(f"Theme file not found: {qss_path}")
        except Exception as e:
            logger.error(f"Failed to apply theme {theme_name}: {e}")

    def _start_final_export(self):
        reply = QMessageBox.question(
            self,
            "Final Export",
            "Start final export?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return
        self.progress_dialog = QProgressDialog("Exporting Girl Pack...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        self.export_thread = QThread()  # Create the thread instance
        self.export_worker = ExportWorker(self.project, self.pipeline)
        self.export_worker.moveToThread(self.export_thread)

        self.export_thread.started.connect(self.export_worker.run)
        self.progress_dialog.canceled.connect(
            self.export_worker.stop
        )  # Connect cancel to worker's stop
        self.export_worker.finished.connect(
            self._on_export_finished
        )  # Worker finished -> UI update

        # Cleanup connections
        self.export_worker.finished.connect(
            self.export_thread.quit
        )  # Worker finished -> Quit thread
        self.export_worker.finished.connect(
            self.export_worker.deleteLater
        )  # Worker finished -> Delete worker
        # [THE FIX] Connect the THREAD's finished signal, not the worker's again
        self.export_thread.finished.connect(
            self.export_thread.deleteLater
        )  # Thread finished -> Delete thread

        self.export_thread.start()  # Start the thread

    def _on_export_finished(self, result_path):
        logger.debug("--- _on_export_finished slot has been called ---")
        self.progress_dialog.close()

        logger.debug(f"Received result_path: {result_path}")
        logger.debug(f"Type of result_path: {type(result_path)}")

        path_exists = False
        if result_path and isinstance(result_path, str):
            normalized_path = os.path.normpath(result_path)
            logger.debug(f"Normalized path for checking: {normalized_path}")
            path_exists = os.path.exists(normalized_path)

        logger.debug(f"Does the path exist? {path_exists}")

        if result_path and path_exists:
            logger.debug("Condition PASSED. Showing success message box.")
            msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                "Success!",
                f"Pack for '{self.project.character_name}' created!",
            )
            open_folder_button = msg_box.addButton(
                "Open Output Folder", QMessageBox.ButtonRole.ActionRole
            )
            msg_box.addButton(QMessageBox.StandardButton.Ok)
            msg_box.exec()

            if msg_box.clickedButton() == open_folder_button:
                QDesktopServices.openUrl(QUrl.fromLocalFile(result_path))
        else:
            logger.error(
                "Condition FAILED. Bypassing success message box. The result_path was either empty or did not exist."
            )
            QMessageBox.critical(
                self,
                "Export Information",
                f"The export process completed, but the output path could not be verified automatically.\n\n"
                f"Please check your output directory manually.\n\n"
                f"Path checked: {result_path}",
            )

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def start_photo_maker_workflow(self):
        stype = self.project.source_type
        settings = None
        if self.project.export_data.get("all_created_clips"):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Choose Source")
            msg_box.setText("Found split clips. Which source to use for frame extraction?")
            full_video_button = msg_box.addButton("Full Video", QMessageBox.ButtonRole.ActionRole)
            clips_button = msg_box.addButton("Split Clips", QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg_box.exec()
            clicked = msg_box.clickedButton()
            if clicked == full_video_button:
                stype = "video"
            elif clicked == clips_button:
                stype = "clips"
            else:
                return

        if stype != "folder":
            dialog = FrameExtractionDialog(
                self,
                self.config.get("image", {}).get("interval_seconds", 2),
                self.config.get("image", {}).get("blur_threshold", 60.0),
            )
            if not dialog.exec() == QDialog.DialogCode.Accepted:
                return
            settings = dialog.get_settings()
            self.progress_dialog = QProgressDialog("Extracting Frames...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.photo_maker_workflow.progress_updated.connect(self.progress_dialog.setValue)
            if hasattr(self.photo_maker_workflow, "stop_current_task"):
                self.progress_dialog.canceled.connect(self.photo_maker_workflow.stop_current_task)
            self.progress_dialog.show()
            self.photo_maker_workflow.start_workflow(stype, settings)
        else:
            self.photo_maker_workflow.start_workflow(stype)
        self.workflow_manager.go_to("photo_maker")

    def _on_extraction_finished(self, source_frames):
        if hasattr(self, "progress_dialog") and self.progress_dialog.isVisible():
            self.progress_dialog.close()
        self.photo_maker_panel.activate_and_load_frames(source_frames)

    def start_yolo_analysis(self, selected_paths):
        self.progress_dialog = QProgressDialog("AI is analyzing frames...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.photo_maker_workflow.progress_updated.connect(self.progress_dialog.setValue)
        if hasattr(self.photo_maker_workflow, "stop_current_task"):
            self.progress_dialog.canceled.connect(self.photo_maker_workflow.stop_current_task)
        self.progress_dialog.show()
        self.photo_maker_workflow.run_yolo_analysis(selected_paths)

    def _on_yolo_finished(self, yolo_results, selected_paths, tasks):
        if hasattr(self, "progress_dialog") and self.progress_dialog.isVisible():
            self.progress_dialog.close()
        self.photo_maker_panel.go_to_workshop(yolo_results, selected_paths, tasks)

    def start_vid_maker_workflow(self):
        self.workflow_manager.go_to("vid_maker")
        self.vids_maker_panel.activate()

    def start_video_splitting(self, clips_timestamps):
        self.vids_maker_panel.clipper_step.stop_video()

        self.progress_dialog = QProgressDialog(
            "Splitting & Analyzing Clips...", "Cancel", 0, 100, self
        )
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.vid_maker_workflow.progress_updated.connect(self.progress_dialog.setValue)

        if hasattr(self.vid_maker_workflow, "stop_current_task"):
            self.progress_dialog.canceled.connect(self.vid_maker_workflow.stop_current_task)

        self.progress_dialog.show()

        self.vid_maker_workflow.run_video_splitting(clips_timestamps)

    def _on_splitting_finished(self, clips_data_with_ai):
        if hasattr(self, "progress_dialog") and self.progress_dialog.isVisible():
            self.progress_dialog.close()
        if clips_data_with_ai:
            all_paths = list(clips_data_with_ai.keys())
            self.project.export_data["all_created_clips"] = all_paths
            logger.info(f"Saved {len(all_paths)} created clip paths to project.")
        try:
            self.vid_maker_workflow.progress_updated.disconnect(self.progress_dialog.setValue)
        except RuntimeError:
            pass
        self.vids_maker_panel.on_splitting_finished(clips_data_with_ai)

    def start_shoot_maker_workflow(self):
        self.workflow_manager.go_to("shoot_maker")
        self.shoot_maker_panel.activate()

    def _on_save_shoot_requested(self, shoot_data):
        self.shoot_maker_workflow.save_shoot_to_project(shoot_data)
        QMessageBox.information(
            self, "Shoot Saved", f"Shoot '{shoot_data['config']['display_name']}' has been saved."
        )
        self.go_to_dashboard()  # <-- تم التصحيح هنا

    def show_processing_screen(self):
        """
        Shows a progress dialog for final processing operations.
        Called when image workshop starts final processing.
        """
        logger.info("Showing processing screen for final processing")
        self.progress_dialog = QProgressDialog("Processing final images...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        # Connect to workflow progress if available
        if hasattr(self.photo_maker_workflow, 'progress_updated'):
            self.photo_maker_workflow.progress_updated.connect(self.progress_dialog.setValue)
        if hasattr(self.photo_maker_workflow, 'stop_current_task'):
            self.progress_dialog.canceled.connect(self.photo_maker_workflow.stop_current_task)
        # Connect to close dialog when finished
        self.photo_maker_workflow.final_processing_finished.connect(self._close_processing_dialog)

    def _close_processing_dialog(self, *args):
        """
        Closes the processing progress dialog when final processing finishes.
        """
        if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():
            self.progress_dialog.close()
            logger.info("Processing dialog closed")
