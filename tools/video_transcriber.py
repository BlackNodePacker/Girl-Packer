# tools/video_transcriber.py

import os
import subprocess
import tempfile
from tools.logger import get_logger
from utils.file_ops import ensure_folder

logger = get_logger("VideoTranscriber")

# Check for faster-whisper availability
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Transcription disabled.")

# FFmpeg path
FFMPEG_PATH = "ffmpeg.exe"  # Adjust if needed

def extract_audio_from_video(video_path: str, audio_path: str) -> bool:
    """Extract audio from video using FFmpeg."""
    command = [
        FFMPEG_PATH,
        "-i", video_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # PCM 16-bit
        "-ar", "16000",  # 16kHz sample rate for Whisper
        "-ac", "1",  # Mono
        "-y",  # Overwrite
        audio_path
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Extracted audio from {video_path} to {audio_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to extract audio from {video_path}: {e}")
        return False

def transcribe_audio(audio_path: str, model_size: str = "base") -> str:
    """Transcribe audio using faster-whisper."""
    if not FASTER_WHISPER_AVAILABLE:
        logger.error("faster-whisper not available.")
        return ""

    try:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")  # Adjust for GPU if available
        segments, info = model.transcribe(audio_path, beam_size=5)
        logger.info(f"Detected language: {info.language} with probability {info.language_probability}")

        transcription = ""
        for segment in segments:
            transcription += f"{segment.text}\n"

        logger.info(f"Transcribed {len(segments)} segments")
        return transcription.strip()
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return ""

def transcribe_video(video_path: str, model_size: str = "base") -> str:
    """Full pipeline: extract audio and transcribe."""
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return ""

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        audio_path = temp_audio.name

    try:
        if not extract_audio_from_video(video_path, audio_path):
            return ""

        transcription = transcribe_audio(audio_path, model_size)
        return transcription
    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)

def format_transcription_to_rpy(transcription: str, character_name: str = "character") -> str:
    """Simple formatting of transcription to RPY dialogue lines."""
    # Split into sentences or lines
    lines = [line.strip() for line in transcription.split('\n') if line.strip()]
    rpy_script = ""
    for line in lines:
        # Assume each line is dialogue from the character
        rpy_script += f'{character_name} "{line}"\n'
    return rpy_script.strip()