import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from ai.pipeline import Pipeline


class TestPipeline:
    @patch("ai.pipeline.YOLOModel")
    @patch("ai.pipeline.create_pytorch_model")
    @patch("ai.pipeline.torch.load")
    def test_init(self, mock_torch_load, mock_create_model, mock_yolo):
        mock_yolo.return_value = MagicMock()
        mock_model = MagicMock()
        mock_create_model.return_value = mock_model
        mock_model.load_state_dict.return_value = None

        tag_manager = MagicMock()
        pipeline = Pipeline(tag_manager)

        assert pipeline.tag_manager == tag_manager
        assert pipeline.yolo_model is not None
        assert pipeline.asset_classifier is not None
        assert pipeline.action_classifier is not None

    def test_classify_asset_no_model(self):
        tag_manager = MagicMock()
        pipeline = Pipeline(tag_manager)
        pipeline.asset_classifier = None

        result = pipeline.classify_asset(np.zeros((224, 224, 3), dtype=np.uint8))
        assert result == "unknown_asset"

    def test_suggest_action_no_model(self):
        tag_manager = MagicMock()
        pipeline = Pipeline(tag_manager)
        pipeline.action_classifier = None

        result = pipeline.suggest_action(np.zeros((224, 224, 3), dtype=np.uint8))
        assert result == "unknown_action"
