import pytest
import os
import tempfile
from utils.file_ops import sanitize_filename, ensure_folder, list_files


class TestFileOps:
    def test_sanitize_filename(self):
        assert sanitize_filename("test file.jpg") == "test_file.jpg"
        assert sanitize_filename("test<file>") == "testfile"
        assert sanitize_filename("normal") == "normal"

    def test_ensure_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new_folder")
            ensure_folder(new_dir)
            assert os.path.exists(new_dir)

    def test_list_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.jpg")
            with open(test_file, "w") as f:
                f.write("test")

            test_txt = os.path.join(tmpdir, "test.txt")
            with open(test_txt, "w") as f:
                f.write("text")

            files = list_files(tmpdir, (".jpg",))
            assert test_file in files
            assert test_txt not in files
