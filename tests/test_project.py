import pytest
import os
import tempfile
from project_data import Project


class TestProject:
    def test_init(self):
        project = Project()
        assert project.source_type is None
        assert project.source_video_path is None
        assert project.source_image_paths == []
        assert project.character_name == ""
        assert project.final_output_path == ""

    def test_scan_directory_for_media(self):
        project = Project()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_img = os.path.join(tmpdir, "test.jpg")
            with open(test_img, "w") as f:
                f.write("fake image")

            test_txt = os.path.join(tmpdir, "test.txt")
            with open(test_txt, "w") as f:
                f.write("text")

            media = project._scan_directory_for_media_absolute(tmpdir)
            assert test_img in media
            assert test_txt not in media

    def test_get_asset_file_paths(self):
        project = Project()
        with tempfile.TemporaryDirectory() as tmpdir:
            project.final_output_path = tmpdir
            temp_dir = os.path.join(tmpdir, "temp")
            os.makedirs(temp_dir)
            test_asset = os.path.join(temp_dir, "asset.jpg")
            with open(test_asset, "w") as f:
                f.write("asset")

            paths = project.get_asset_file_paths()
            assert test_asset in paths
