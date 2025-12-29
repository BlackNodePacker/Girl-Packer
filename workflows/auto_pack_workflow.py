import os
import shutil
from PySide6.QtCore import QObject, Signal
from tools.logger import get_logger
from tools.pack_analyzer import PackAnalyzer

logger = get_logger("AutoPackWorkflow")


class AutoPackWorkflow(QObject):
    """A simplified Auto-Pack worker that performs extraction of requested components.

    This implementation is intentionally lightweight: it organizes selected components
    from a source folder into a temporary pack structure, runs `PackAnalyzer`, and
    writes results into `temp/autopack_{name}`. It emits `finished` when done.
    """

    finished = Signal(bool, str)

    def __init__(self, main_window, options):
        super().__init__()
        import os
        import shutil
        from PySide6.QtCore import QObject, Signal
        from tools.logger import get_logger
        from tools.pack_analyzer import PackAnalyzer

        logger = get_logger("AutoPackWorkflow")


        class AutoPackWorkflow(QObject):
            """A simplified Auto-Pack worker that performs extraction of requested components.

            This implementation is intentionally lightweight: it organizes selected components
            from a source folder into a temporary pack structure, runs `PackAnalyzer`, and
            writes results into `temp/autopack_{name}`. It emits `finished` when done.
            """

            finished = Signal(bool, str)

            def __init__(self, main_window, options):
                super().__init__()
                self.main_window = main_window
                self.options = options

            def run(self):
                try:
                    src = self.options.get("source_folder")
                    pack_type = self.options.get("pack_type")
                    comps = self.options.get("components", {})

                    if not os.path.isdir(src):
                        self.finished.emit(False, "Source folder not found")
                        return

                    name = os.path.basename(os.path.normpath(src))
                    target_root = os.path.join("temp", f"autopack_{name}")
                    shutil.rmtree(target_root, ignore_errors=True)
                    os.makedirs(target_root, exist_ok=True)

                    # Copy selected components — heuristics: look for folders in source matching names
                    for comp_key, enabled in comps.items():
                        if not enabled:
                            continue
                        # try to find matching folders
                        candidate = os.path.join(src, comp_key)
                        out_dir = os.path.join(target_root, comp_key)
                        if os.path.isdir(candidate):
                            shutil.copytree(candidate, out_dir)
                        else:
                            # collect files by extension heuristics
                            os.makedirs(out_dir, exist_ok=True)
                            for root, _, files in os.walk(src):
                                for f in files:
                                    if comp_key == "videos" and f.lower().endswith((".mp4", ".webm")):
                                        shutil.copy2(os.path.join(root, f), out_dir)
                                    if comp_key in ("photos", "fullbody", "body", "clothing", "events") and f.lower().endswith((".png", ".jpg", ".webp")):
                                        shutil.copy2(os.path.join(root, f), out_dir)

                    # Analyze created pack
                    analyzer = PackAnalyzer(target_root)
                    report = analyzer.analyze()
                    # Save report
                    try:
                        with open(os.path.join(target_root, "pack_report.json"), "w", encoding="utf-8") as fh:
                            import json

                            json.dump(report, fh, indent=2)
                    except Exception as e:
                        logger.warning(f"Failed to write report file: {e}")

                    # Register the pack as current project for review/export convenience
                    try:
                        self.main_window.project.character_name = name
                        self.main_window.project.final_output_path = os.path.abspath(target_root)
                    except Exception:
                        pass

                    logger.info("Auto-Pack workflow finished successfully")
                    self.finished.emit(True, "Auto-Pack completed successfully.")
                except Exception as e:
                    logger.error(f"AutoPackWorkflow failed: {e}", exc_info=True)
                    self.finished.emit(False, f"Auto-Pack failed: {e}")
