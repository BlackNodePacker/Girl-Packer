import cv2
import os
import hashlib
from PySide6.QtGui import QImage  # We need QImage for easy thumbnail handling in Qt environment
from tools.logger import get_logger
from .ai_utils import ensure_dir  # Import the utility to ensure directories exist

logger = get_logger("VideoUtils")


def load_video(video_path: str):
    """
    Loads a video file using OpenCV.
    Returns a cv2.VideoCapture object or None if the file cannot be opened.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video file: {video_path}")
        return None

    return cap


def split_video(video_path: str, output_folder: str, segment_length: int = 10):
    """
    Splits a video file into smaller segments.
    This is a simplified function for testing the pipeline.
    """
    logger.info(f"Splitting video {video_path} into {segment_length}s segments.")
    cap = load_video(video_path)
    if cap is None:
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames_per_segment = int(fps * segment_length)

    segments = []

    for i in range(0, total_frames, frames_per_segment):
        segment_path = os.path.join(output_folder, f"segment_{i:05d}.avi")
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(segment_path, fourcc, fps, (int(cap.get(3)), int(cap.get(4))))

        cap.set(cv2.CAP_PROP_POS_FRAMES, i)

        for j in range(frames_per_segment):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        out.release()
        segments.append(segment_path)

    cap.release()
    logger.info(f"Video splitting completed. {len(segments)} segments created.")
    return segments


# --- [NEW] Caching and Thumbnail Function ---


def _get_cache_path(video_path: str, cache_dir: str):
    """Generates a stable cache file path based on video path and modification time."""
    # Use file path and last modification time to create a unique hash (prevents using old thumbnail if video changes)
    mod_time = os.path.getmtime(video_path)
    unique_key = f"{video_path}_{mod_time}"
    file_hash = hashlib.sha256(unique_key.encode("utf-8")).hexdigest()
    return os.path.join(cache_dir, f"{file_hash}.png")


def create_thumbnail_from_video(video_path: str, target_size: int = 128):
    """
    Creates or loads a thumbnail from a video file with Caching logic.
    Returns a QImage object or None.
    """
    CACHE_DIR = ensure_dir(os.path.join(os.getcwd(), "cache", "media_thumbs"))
    cache_path = _get_cache_path(video_path, CACHE_DIR)

    # 1. Check Cache
    if os.path.exists(cache_path):
        try:
            image = QImage(cache_path)
            if not image.isNull():
                logger.debug(f"Loaded thumbnail from cache for: {os.path.basename(video_path)}")
                return image
            else:
                logger.warning(
                    f"Cache file was corrupt, regenerating: {os.path.basename(video_path)}"
                )
                os.remove(cache_path)  # Remove corrupt file
        except Exception as e:
            logger.error(f"Error loading cache thumbnail: {e}")

    # 2. Generate Thumbnail (Slow Process)
    cap = load_video(video_path)
    if cap is None:
        return None

    # Try to grab a frame from the middle of the video (safer than frame 0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        logger.warning(f"Could not read frame for thumbnail from: {video_path}")
        return None

    # Convert OpenCV BGR frame to QImage
    height, width, channel = frame.shape
    bytes_per_line = 3 * width

    # Resize frame for efficiency before converting
    scale_factor = target_size / max(height, width)
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    frame_resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

    # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)

    # Create QImage
    q_image = QImage(
        frame_rgb.data, new_width, new_height, 3 * new_width, QImage.Format.Format_RGB888
    )

    # 3. Save to Cache
    q_image.save(cache_path, "PNG")
    logger.info(f"Generated and cached thumbnail for: {os.path.basename(video_path)}")

    return q_image
