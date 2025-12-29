import tempfile
import os
from project_data import Project

def test_save_event_files_creates_files(tmp_path):
    p = Project()
    p.final_output_path = str(tmp_path)
    event_name = "test_event"
    event_data = {"title": "Test", "steps": []}
    rpy_content = 'label test:\n    "Hello"\n'
    success = p.save_event_files(event_name, event_data, rpy_content)
    assert success is True
    event_folder = os.path.join(p.final_output_path, "game", "events", event_name)
    assert os.path.exists(event_folder)
    assert any(f.endswith('.json') for f in os.listdir(event_folder))
    assert any(f.endswith('.rpy') for f in os.listdir(event_folder))
    # ensure export_data updated
    assert event_name in p.export_data.get('events', {})
