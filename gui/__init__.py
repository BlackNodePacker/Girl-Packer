# GameMediaTool/gui/__init__.py (Updated and Simplified)

# This file gathers the main top-level UI panels/views of the application.

from .main_window import MainWindow
from .dashboard_panel import DashboardPanel
from .ai_training_panel import AITrainingPanel
from .data_review_panel import DataReviewPanel
from .character_setup_panel import CharacterSetupPanel # <-- ADDED

# --- Workflow Container Panels ---
from .vids_maker_panel import VidsMakerPanel
from .photo_maker_panel import PhotoMakerPanel
from .shoot_maker_panel import ShootMakerPanel