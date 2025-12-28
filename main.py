import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from tools.logger import get_logger

logger = get_logger("Main")

if __name__ == "__main__":
    logger.info("Starting Girl Packer application")
    # Handle frozen executable paths
    if getattr(sys, 'frozen', False):
        # Running in a bundle
        exe_dir = Path(sys.executable).parent
        os.chdir(exe_dir)
        logger.info(f"Changed working directory to {exe_dir}")
    # 1. Start Application
    app = QApplication(sys.argv)
    logger.info("QApplication initialized")

    # Load the stylesheet robustly
    script_dir = Path(__file__).resolve().parent
    if getattr(sys, 'frozen', False):
        # Running in a bundle (PyInstaller or Nuitka)
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = script_dir
    # Assume the stylesheet is at the root of the project structure for Nuitka to find it easily
    stylesheet_path = base_dir / "gui" / "style.qss"

    try:
        # NOTE: Nuitka includes data files in the root of the build folder.
        # When running the built executable, the path 'gui/style.qss' may fail.
        # Try loading relative to script dir first, then as direct file.

        # Try loading from the path relative to the script directory first
        style_content = ""
        if stylesheet_path.exists():
            with open(stylesheet_path, "r", encoding="utf-8") as f:
                style_content = f.read()
            logger.info(f"Stylesheet loaded from {stylesheet_path}")
        else:
            logger.warning(f"Stylesheet not found at '{stylesheet_path}'. Using default.")

        if style_content:
            app.setStyleSheet(style_content)
            logger.info("Stylesheet applied to application")

    except Exception as e:
        logger.error(f"An error occurred while loading stylesheet: {e}")

    # 2. Run MainWindow
    logger.info("Initializing MainWindow")
    window = MainWindow()
    window.show()
    logger.info("MainWindow shown")

    # 3. Exit (Using exec() for Pyside6 compatibility)
    logger.info("Entering application event loop")
    sys.exit(app.exec())
