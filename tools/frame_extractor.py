# GameMediaTool/tools/frame_extractor.py (Corrected - cleanup logic removed)

import os
import sys
import shutil
import subprocess
import cv2
import numpy as np
from pathlib import Path
from .logger import get_logger
from utils.file_ops import ensure_folder

logger = get_logger("FFmpegFrameExtractor")

FFMPEG_PATH = "ffmpeg.exe" if getattr(sys, 'frozen', False) else "F:/ffmpeg-8.0-essentials_build/bin/ffmpeg.exe"

def _run_ffmpeg_command(command):
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(command, check=True, startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"FFmpeg command failed: {' '.join(command)}. Error: {e}")
        return False

def _calculate_blurriness(image_path: str, threshold: float) -> bool:
    try:
        image = cv2.imread(image_path)
        if image is None: return False
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return variance >= threshold
    except Exception as e:
        logger.error(f"Failed to calculate blurriness for {image_path}: {e}")
        return False

def extract_frames(video_path: str, output_folder: str, progress_callback=None, blur_threshold=60.0, interval_seconds=2):
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}"); return []
    if not os.path.exists(FFMPEG_PATH):
        logger.error(f"FFmpeg not found at {FFMPEG_PATH}"); return []

    # The cleanup logic has been removed from this file.
    
    temp_extraction_folder = os.path.join(output_folder, f"temp_candidates_{Path(video_path).stem}")
    ensure_folder(temp_extraction_folder)
    
    video_name = Path(video_path).stem
    
    logger.info("Phase 1: Starting fast frame extraction with FFmpeg...")
    command = [
        FFMPEG_PATH,
        '-i', video_path,
        '-vf', f"fps=1/{interval_seconds}",
        '-q:v', '2',
        os.path.join(temp_extraction_folder, f'{video_name}_frame_%05d.jpg')
    ]
    
    if progress_callback: progress_callback(10)
    
    success = _run_ffmpeg_command(command)
    if not success:
        logger.error("FFmpeg frame extraction failed. Aborting.")
        return []
        
    logger.info("FFmpeg finished. Starting Phase 2: Quality filtering...")
    if progress_callback: progress_callback(50)

    candidate_files = sorted([os.path.join(temp_extraction_folder, f) for f in os.listdir(temp_extraction_folder)])
    final_frames = []
    total_candidates = len(candidate_files)

    for i, file_path in enumerate(candidate_files):
        if _calculate_blurriness(file_path, blur_threshold):
            final_path = os.path.join(output_folder, os.path.basename(file_path))
            try:
                os.rename(file_path, final_path)
                final_frames.append(final_path)
            except OSError as e:
                logger.error(f"Could not move sharp frame {file_path}: {e}")
        else:
            try:
                os.remove(file_path)
            except OSError as e:
                logger.error(f"Could not delete blurry frame {file_path}: {e}")
        
        if progress_callback and total_candidates > 0:
            progress_percent = 50 + int(((i + 1) / total_candidates) * 50)
            progress_callback(progress_percent)

    try:
        shutil.rmtree(temp_extraction_folder)
    except OSError:
        pass

    logger.info(f"Smart extraction complete. Kept {len(final_frames)} high-quality frames.")
    return final_frames