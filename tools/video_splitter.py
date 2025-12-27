# GameMediaTool/tools/video_splitter.py (Simplified to be a command generator)

import os
import sys
import subprocess
from pathlib import Path
from .logger import get_logger

logger = get_logger("VideoSplitter")

# --- Dynamic FFmpeg/FFprobe Path Logic ---
if getattr(sys, "frozen", False):
    FFMPEG_PATH = "ffmpeg.exe"
    FFPROBE_PATH = "ffprobe.exe"
else:
    FFMPEG_DIR = "F:/ffmpeg-8.0-essentials_build/bin"
    FFMPEG_PATH = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
    FFPROBE_PATH = os.path.join(FFMPEG_DIR, "ffprobe.exe")


def _run_command(command):
    """
    [MODIFIED] Helper function to run a command robustly using Popen to prevent deadlocks.
    This is the most reliable way to handle subprocesses from a GUI thread.
    """
    try:
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        # Use Popen for non-blocking execution and communicate() to safely get output and wait.
        # This is the canonical way to avoid pipe deadlocks.
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            startupinfo=startupinfo,
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_message = f"Command failed with exit code {process.returncode}: {' '.join(command)}\nStderr: {stderr}"
            logger.error(error_message)
            return False, stdout, stderr

        return True, stdout, stderr

    except Exception as e:
        logger.error(
            f"An unexpected error occurred running Popen command: {' '.join(command)}. Error: {e}",
            exc_info=True,
        )
        return False, "", str(e)


def get_video_duration(video_path):
    """Gets video duration in seconds using ffprobe."""
    if not os.path.exists(video_path):
        return 0
    command = [
        FFPROBE_PATH,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    try:
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(
            command, check=True, capture_output=True, text=True, startupinfo=startupinfo
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Could not parse duration from ffprobe. Error: {e}")
        return 0


def get_ffmpeg_split_commands(video_path, output_folder, clips):
    """
    [NEW] Generates a list of ffmpeg command arrays to be executed later.
    Returns a list of tuples, where each tuple is (command_list, expected_output_path).
    """
    if not os.path.exists(FFMPEG_PATH):
        logger.error(f"FFmpeg not found at: {FFMPEG_PATH}.")
        return []
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return []

    # Validate video file can be read
    try:
        duration = get_video_duration(video_path)
        if duration <= 0:
            logger.error(f"Invalid video file or unable to read duration: {video_path}")
            return []
        logger.info(f"Video duration: {duration} seconds")
    except Exception as e:
        logger.error(f"Error validating video file {video_path}: {e}")
        return []
    os.makedirs(output_folder, exist_ok=True)
    video_path_obj = Path(video_path)
    base_name = video_path_obj.stem
    extension = video_path_obj.suffix
    command_list = []

    for i, clip_info in enumerate(clips):
        start_ms = clip_info["start"]
        end_ms = clip_info["end"]
        start_time = start_ms / 1000.0
        end_time = end_ms / 1000.0
        if end_time <= start_time:
            continue

        output_path = os.path.join(output_folder, f"{base_name}_clip_{i:03d}{extension}")
        command = [
            FFMPEG_PATH,
            "-i",
            str(video_path),
            "-ss",
            str(start_time),
            "-to",
            str(end_time),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "1",
            str(output_path),
            "-y",
        ]
        command_list.append((command, output_path))

    return command_list


def generate_clip_timestamps(video_path, params):
    duration_s = get_video_duration(video_path)
    if duration_s == 0:
        logger.error("Could not determine video duration.")
        return [], 0
    timestamps, mode, value = [], params["mode"], params["value"]
    if mode == "duration":
        for start_s in range(0, int(duration_s), value):
            end_s = min(start_s + value, duration_s)
            timestamps.append({"start": start_s * 1000, "end": end_s * 1000})
    elif mode == "number":
        if value == 0:
            return [], 0
        segment_duration_s = duration_s / value
        for i in range(value):
            start_s, end_s = i * segment_duration_s, (i + 1) * segment_duration_s
            timestamps.append({"start": int(start_s * 1000), "end": int(end_s * 1000)})
    return timestamps, int(duration_s * 1000)


def split_video(video_path, output_folder, clips, progress_callback=None):
    # This function remains unchanged
    os.makedirs(output_folder, exist_ok=True)
    created_files = []
    if not os.path.exists(FFMPEG_PATH):
        logger.error(f"FFmpeg not found at: {FFMPEG_PATH}. Cannot split videos.")
        return []
    logger.info(f"Starting ultra-fast FFmpeg splitting for {len(clips)} clips...")
    video_path_obj = Path(video_path)
    base_name = video_path_obj.stem
    extension = video_path_obj.suffix
    total_clips = len(clips)
    for i, clip_info in enumerate(clips):
        start_ms = clip_info["start"]
        end_ms = clip_info["end"]
        start_time = start_ms / 1000.0
        end_time = end_ms / 1000.0
        if end_time <= start_time:
            continue
        output_path = os.path.join(output_folder, f"{base_name}_clip_{i:03d}{extension}")
        command = [
            FFMPEG_PATH,
            "-i",
            str(video_path),
            "-ss",
            str(start_time),
            "-to",
            str(end_time),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "1",
            str(output_path),
            "-y",
        ]
        success, _, stderr = _run_command(command)
        if success:
            created_files.append(output_path)
        else:
            logger.error(f"Failed to create clip {i+1}. FFmpeg likely failed. Stderr: {stderr}")
        if progress_callback and total_clips > 0:
            progress_percent = int(((i + 1) / total_clips) * 100)
            progress_callback(progress_percent)
    return created_files
