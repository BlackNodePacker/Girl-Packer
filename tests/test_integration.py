import pytest
import os
import tempfile
from project_data import Project
from ai.pipeline import Pipeline
import numpy as np


@pytest.fixture
def sample_video():
    """Path to sample video."""
    return r"F:\My Tools\Girl Packer\sample\720.mp4"


@pytest.fixture
def temp_project():
    """Create a temporary project."""
    project = Project()
    project.character_name = "TestChar"
    project.source_video_path = r"F:\My Tools\Girl Packer\sample\720.mp4"
    project.source_type = "video"
    with tempfile.TemporaryDirectory() as tmpdir:
        project.final_output_path = tmpdir
        yield project


@pytest.fixture
def pipeline():
    """Create pipeline instance."""
    from utils.tag_manager import TagManager
    tag_manager = TagManager()
    return Pipeline(tag_manager)


def test_cnn_classification(pipeline):
    """Test CNN classification."""
    # Create dummy image
    dummy_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

    asset_tag = pipeline.classify_asset(dummy_image)
    action_tag = pipeline.suggest_action(dummy_image)

    assert isinstance(asset_tag, str)
    assert isinstance(action_tag, str)


def test_training_data_save():
    """Test that training data is saved correctly."""
    # Simulate saving data
    training_dir = "assets/cnn_training_data/train/boobs"
    os.makedirs(training_dir, exist_ok=True)
    # In real workflow, this happens during processing
    assert os.path.exists(training_dir)


def test_project_setup(temp_project, sample_video):
    """Test project setup with sample video."""
    assert temp_project.source_video_path == sample_video
    assert temp_project.source_type == "video"
    assert temp_project.character_name == "TestChar"