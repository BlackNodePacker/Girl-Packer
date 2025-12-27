# GameMediaTool/workflows/workflow_manager.py (Final and Confirmed)

from PySide6.QtWidgets import QStackedWidget, QMessageBox
from tools.logger import get_logger

logger = get_logger("WorkflowManager")

class WorkflowManager:
    """
    Manages the navigation between different top-level UI panels (workflows).
    """
    def __init__(self, main_window, view_stack: QStackedWidget):
        super().__init__()
        self.main_window = main_window
        self.view_stack = view_stack
        self.project = main_window.project

        self.panels = {
            'dashboard': main_window.dashboard_panel,
            'ai_center': main_window.ai_training_panel, # موجودة بالفعل
            'data_review': main_window.data_review_panel,
            'vid_maker': main_window.vids_maker_panel,
            'photo_maker': main_window.photo_maker_panel,
            'shoot_maker': main_window.shoot_maker_panel,
            'event_maker': main_window.event_maker_panel, # <-- تم إضافتها
        }
        logger.info("WorkflowManager initialized with final panel references.")

    def go_to(self, panel_key: str):
        """The central navigation function."""
        if panel_key not in self.panels:
            logger.error(f"Attempted to navigate to a non-existent panel: {panel_key}")
            return

        target_panel = self.panels[panel_key]
        logger.info(f"Navigating to '{panel_key}' panel.")
        
        # The activation logic is now handled by MainWindow before calling go_to,
        # but we keep this for panels that don't need complex pre-loading.
        if hasattr(target_panel, 'activate') and panel_key not in ['vid_maker', 'photo_maker', 'shoot_maker', 'event_maker']: # <-- تم تحديث القائمة المستبعدة
             try:
                target_panel.activate()
             except Exception as e:
                 logger.error(f"Error activating panel '{panel_key}': {e}", exc_info=True)
                 QMessageBox.critical(self.main_window, "Activation Error", f"Could not start the '{panel_key}' workflow.")
                 return

        self.view_stack.setCurrentWidget(target_panel)
        if panel_key == 'dashboard':
            self.main_window._update_dashboard_state()

    def go_to_dashboard(self):
        """A convenience method to always return to the dashboard."""
        self.go_to('dashboard')