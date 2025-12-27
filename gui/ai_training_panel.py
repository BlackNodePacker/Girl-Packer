# GameMediaTool/gui/ai_training_panel.py (File 52 - Fully Functional)

import os
# [MIGRATION] Switched to PySide6
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QMessageBox, QProgressDialog
from PySide6.QtCore import Signal, QThread, Qt, QObject

from ai.trainer import TrainerManager
from tools.logger import get_logger

from ai.trainer import TrainerManager
from tools.logger import get_logger

logger = get_logger("AITrainingPanel")

class TrainingWorker(QObject):
    """A worker to run the training process in a separate thread."""
    finished = Signal(bool, str) # Emits success status and a message

    def __init__(self, training_mode, config=None):
        super().__init__()
        self.training_mode = training_mode
        self.config = config
        self.trainer = TrainerManager(config)

    def run(self):
        logger.info(f"TrainingWorker started for mode: {self.training_mode}")
        try:
            if self.training_mode == 'all':
                success = self.trainer.train_all_models()
                if success:
                    self.finished.emit(True, "All models trained successfully!")
                else:
                    self.finished.emit(False, "Training was skipped or failed. Check logs for details (e.g., missing train/val folders).")
            # Add other modes here if needed later (e.g., 'yolo', 'cnn_action')
            else:
                self.finished.emit(False, f"Unknown training mode: {self.training_mode}")

        except Exception as e:
            logger.error(f"An error occurred during training: {e}", exc_info=True)
            self.finished.emit(False, f"A critical error occurred: {e}")

class AITrainingPanel(QWidget):
    back_to_dashboard = Signal()
    review_data_requested = Signal() # This remains for navigation

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window 
        self.training_thread = None
        self.training_worker = None

        main_layout = QVBoxLayout(self)
        
        title = QLabel("🧠 AI Training Center")
        title.setObjectName("TitleLabel")
        main_layout.addWidget(title)

        steps_group = QGroupBox("Training Workflow")
        steps_layout = QVBoxLayout(steps_group)
        
        # We will simplify this to a single, powerful button
        self.train_all_button = QPushButton("🚀 Train/Update All Models")
        self.train_all_button.setToolTip(
            "Starts the incremental training process for all AI models (e.g., CNNs).\n"
            "This will use any new data you have prepared in the 'assets/cnn_training_data' folder.\n"
            "Ensure you have 'train' and 'val' sub-folders organized correctly before running."
        )
        self.train_all_button.setObjectName("ConfirmButton")

        self.review_data_button = QPushButton("🔬 Review & Correct AI-Generated Data")

        steps_layout.addWidget(self.train_all_button)
        steps_layout.addWidget(self.review_data_button)
        main_layout.addWidget(steps_group)
        
        main_layout.addStretch()
        
        back_button = QPushButton("⬅️ Back to Dashboard")
        main_layout.addWidget(back_button)

        # Connect signals
        back_button.clicked.connect(self.back_to_dashboard.emit)
        self.train_all_button.clicked.connect(self.start_training)
        self.review_data_button.clicked.connect(self.review_data_requested.emit)

    def start_training(self):
        reply = QMessageBox.question(self, "Confirm Training",
                                     "This will start the AI training process using data in the designated training folders. This may take a while and consume significant system resources.\n\nAre you sure you want to proceed?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.No:
            return

        self.progress_dialog = QProgressDialog("Training AI models... Please wait.", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setWindowTitle("AI Training in Progress")
        self.progress_dialog.show()
        
        self.training_thread = QThread()
        self.training_worker = TrainingWorker(training_mode='all', config=self.main_window.config)
        self.training_worker.moveToThread(self.training_thread)

        self.training_thread.started.connect(self.training_worker.run)
        self.training_worker.finished.connect(self.on_training_finished)
        
        # Cleanup connections
        self.training_worker.finished.connect(self.training_thread.quit)
        self.training_worker.finished.connect(self.training_worker.deleteLater)
        self.training_thread.finished.connect(self.training_thread.deleteLater)

        self.training_thread.start()

    def on_training_finished(self, success, message):
        self.progress_dialog.close()
        if success:
            QMessageBox.information(self, "Training Complete", message)
        else:
            QMessageBox.warning(self, "Training Finished with Issues", message)