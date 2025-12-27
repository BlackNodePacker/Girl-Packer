import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from tools.logger import get_logger

logger = get_logger("Main")

if __name__ == "__main__":
    logger.info("Starting Girl Packer application")
    # 1. Start Application
    app = QApplication(sys.argv)
    logger.info("QApplication initialized")

    # Load the stylesheet robustly
    script_dir = Path(__file__).resolve().parent
    # Assume the stylesheet is at the root of the project structure for Nuitka to find it easily
    stylesheet_path = script_dir / "gui" / "style.qss"

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
            # Fallback for Nuitka build: load from execution folder
            # Nuitka script uses 'gui/style.qss' -> 'style.qss' in build root
            nuitka_fallback_path = script_dir / "style.qss"
            if nuitka_fallback_path.exists():
                with open(nuitka_fallback_path, "r", encoding="utf-8") as f:
                    style_content = f.read()
                logger.info(f"Stylesheet loaded from Nuitka fallback {nuitka_fallback_path}")
            else:
                logger.warning(f"Stylesheet not found at '{stylesheet_path}' or '{nuitka_fallback_path}'. Using default.")

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
