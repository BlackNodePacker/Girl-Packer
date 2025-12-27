import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

if __name__ == "__main__":
    # 1. Start Application
    app = QApplication(sys.argv)

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
        else:
            # Fallback for Nuitka build: load from execution folder
            # Nuitka script uses 'gui/style.qss' -> 'style.qss' in build root
            nuitka_fallback_path = script_dir / "style.qss"
            if nuitka_fallback_path.exists():
                with open(nuitka_fallback_path, "r", encoding="utf-8") as f:
                    style_content = f.read()
            else:
                print(
                    f"WARNING: Stylesheet not found at '{stylesheet_path}' or '{nuitka_fallback_path}'. Using default."
                )

        if style_content:
            app.setStyleSheet(style_content)
            print("Stylesheet loaded successfully.")

    except Exception as e:
        print(f"An error occurred while loading stylesheet: {e}")

    # 2. Run MainWindow
    window = MainWindow()
    window.show()

    # 3. Exit (Using exec() for Pyside6 compatibility)
    sys.exit(app.exec())
