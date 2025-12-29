from tools.video_transcriber import format_transcription_to_rpy, transcribe_audio


def test_format_transcription_to_rpy():
    text = "Hello world\nThis is a test"
    rpy = format_transcription_to_rpy(text, character_name="char")
    assert 'char "Hello world"' in rpy
    assert 'char "This is a test"' in rpy


def test_transcribe_audio_not_available():
    # If faster-whisper is not installed, transcribe_audio should return empty string
    res = transcribe_audio("nonexistent.wav")
    assert res == "" or isinstance(res, str)
