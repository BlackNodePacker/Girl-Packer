# tests/test_event_maker.py

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch
from gui.event_maker_panel import EventMakerPanel
from tools.video_transcriber import transcribe_video, format_transcription_to_rpy


class TestEventMakerPanel:
    @pytest.fixture
    def mock_project_manager(self):
        """Mock project manager with required methods."""
        pm = Mock()
        pm.get_asset_file_paths.return_value = [
            "test_image.png",
            "test_video.mp4"
        ]
        pm.get_all_traits.return_value = ["trait1", "trait2"]
        return pm

    @pytest.fixture
    def event_panel(self, mock_project_manager):
        """Create EventMakerPanel instance with mocked dependencies."""
        with patch('gui.event_maker_panel.QWidget'):
            panel = EventMakerPanel(mock_project_manager)
            # Mock UI elements
            panel.event_name_input = Mock()
            panel.event_name_input.text.return_value = "test_event"
            panel.event_display_name_input = Mock()
            panel.event_display_name_input.text.return_value = "Test Event"
            panel.event_type_combo = Mock()
            panel.event_type_combo.currentText.return_value = "home_visit"
            panel.event_reqs_desc_input = Mock()
            panel.event_reqs_desc_input.text.return_value = "Test requirements"
            panel.girl_id_input = Mock()
            panel.girl_id_input.text.return_value = "test_girl"
            panel.min_chance_spinbox = Mock()
            panel.min_chance_spinbox.value.return_value = 10
            panel.max_chance_spinbox = Mock()
            panel.max_chance_spinbox.value.return_value = 20
            panel.one_time_event_check = Mock()
            panel.one_time_event_check.isChecked.return_value = False
            panel.reset_outfit_check = Mock()
            panel.reset_outfit_check.isChecked.return_value = True
            panel.hide_in_menus_check = Mock()
            panel.hide_in_menus_check.isChecked.return_value = False
            panel.ignore_frequency_check = Mock()
            panel.ignore_frequency_check.isChecked.return_value = False
            panel.allow_random_trigger_check = Mock()
            panel.allow_random_trigger_check.isChecked.return_value = True
            panel.event_cooldown_spinbox = Mock()
            panel.event_cooldown_spinbox.value.return_value = 7
            panel.participant_cooldown_spinbox = Mock()
            panel.participant_cooldown_spinbox.value.return_value = 3
            panel.participants_list = Mock()
            panel.participants_list.findChild.return_value = Mock()
            panel.participants_list.findChild.return_value.items.return_value = ["test_girl"]
            panel.stages_list = Mock()
            panel.stages_list.findChild.return_value = Mock()
            panel.stages_list.findChild.return_value.items.return_value = ["stage1"]
            panel.current_script_data = {"stage1": 'player.character "Hello"'}
            return panel

    def test_generate_rpy_script_content(self, event_panel):
        """Test RPY script generation."""
        rpy = event_panel._generate_rpy_script_content("test_event")
        assert "label stage1_test_event:" in rpy
        assert 'player.character "Hello"' in rpy
        assert "return" in rpy

    def test_on_save_event_validation(self, event_panel):
        """Test save event with empty name."""
        event_panel.event_name_input.text.return_value = ""
        with patch('gui.event_maker_panel.QMessageBox') as mock_msg:
            event_panel._on_save_event()
            mock_msg.critical.assert_called_once()

    @patch('gui.event_maker_panel.EventMakerPanel._write_files_to_disk')
    def test_on_save_event_success(self, mock_write, event_panel):
        """Test successful save event."""
        with patch('gui.event_maker_panel.QMessageBox') as mock_msg:
            event_panel._on_save_event()
            mock_write.assert_called_once()
            mock_msg.information.assert_called_once()

    def test_write_files_to_disk_success(self, event_panel):
        """Test writing files to disk."""
        event_panel.project_manager.save_event_files = Mock(return_value=True)
        result = event_panel._write_files_to_disk("test", {}, "rpy content")
        assert result is True

    def test_write_files_to_disk_failure(self, event_panel):
        """Test writing files failure."""
        event_panel.project_manager.save_event_files = Mock(side_effect=Exception("Test error"))
        result = event_panel._write_files_to_disk("test", {}, "rpy content")
        assert result is False

    def test_populate_media_list(self, event_panel):
        """Test populating media list."""
        event_panel.media_list_widget = Mock()
        event_panel.video_player = Mock()
        event_panel.image_preview = Mock()
        event_panel.available_assets = {}
        event_panel._populate_media_list()
        assert len(event_panel.available_assets) == 2  # image and video

    def test_on_transcribe_video_no_selection(self, event_panel):
        """Test transcribe with no selection."""
        event_panel.media_list_widget.currentItem.return_value = None
        with patch('gui.event_maker_panel.QMessageBox') as mock_msg:
            event_panel._on_transcribe_video()
            mock_msg.warning.assert_called_once()

    @patch('tools.video_transcriber.transcribe_video')
    def test_on_transcribe_video_success(self, mock_transcribe, event_panel):
        """Test successful transcription."""
        mock_transcribe.return_value = "Hello world"
        event_panel.media_list_widget.currentItem.return_value = Mock()
        event_panel.media_list_widget.currentItem.return_value.data.return_value = "vid1"
        event_panel.available_assets = {"vid1": {"path": "test.mp4", "type": "video"}}
        event_panel.stages_list.currentItem.return_value = Mock()
        event_panel.stages_list.currentItem.return_value.text.return_value = "stage1"
        event_panel.script_editor = Mock()
        with patch('gui.event_maker_panel.QMessageBox') as mock_msg:
            event_panel._on_transcribe_video()
            assert "character \"Hello world\"" in event_panel.current_script_data["stage1"]
            mock_msg.information.assert_called_once()


class TestVideoTranscriber:
    def test_format_transcription_to_rpy(self):
        """Test formatting transcription to RPY."""
        transcription = "Hello\nHow are you?"
        rpy = format_transcription_to_rpy(transcription, "player")
        expected = 'player "Hello"\nplayer "How are you?"'
        assert rpy == expected

    @patch('tools.video_transcriber.extract_audio_from_video')
    @patch('tools.video_transcriber.transcribe_audio')
    def test_transcribe_video_success(self, mock_transcribe, mock_extract):
        """Test full video transcription."""
        mock_extract.return_value = True
        mock_transcribe.return_value = "Test transcription"
        with patch('os.path.exists', return_value=True):
            result = transcribe_video("test.mp4")
            assert result == "Test transcription"

    @patch('tools.video_transcriber.extract_audio_from_video')
    def test_transcribe_video_extract_fail(self, mock_extract):
        """Test transcription when audio extraction fails."""
        mock_extract.return_value = False
        result = transcribe_video("test.mp4")
        assert result == ""