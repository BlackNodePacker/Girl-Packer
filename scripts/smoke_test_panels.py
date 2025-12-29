import sys, traceback
from PySide6.QtWidgets import QApplication

# Ensure project root is on sys.path so package imports (gui, ai, etc.) work
sys.path.insert(0, r"F:\My Tools\Girl Packer")

app = QApplication([])
panels = [
    ("gui.auto_pack_panel", "AutoPackPanel"),
    ("gui.pack_review_panel", "PackReviewPanel"),
    ("gui.settings_panel2", "SettingsPanel"),
    ("gui.report_bug_dialog", "ReportBugDialog"),
]

class DummyMainWindow:
    def __init__(self):
        self.project = type("P", (), {"character_name": "test", "final_output_path": ""})()
        self.config = {}
        self.tag_manager = None

results = {}
for modname, clsname in panels:
    key = f"{modname}.{clsname}"
    try:
        mod = __import__(modname, fromlist=[clsname])
        cls = getattr(mod, clsname)
        try:
            inst = cls()
        except TypeError:
            # try passing a minimal dummy main_window
            inst = cls(DummyMainWindow())
        results[key] = "OK"
    except Exception:
        results[key] = traceback.format_exc()

for k, v in results.items():
    print('---', k, '---')
    print(v)

print('\nSmoke test complete')
