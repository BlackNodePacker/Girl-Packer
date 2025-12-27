# GameMediaTool/utils/ai_utils.py
import os

def ensure_dir(path: str):
    """
    Ensures that a directory exists.
    """
    os.makedirs(path, exist_ok=True)
    return path

def get_absolute_path(base_dir, relative_path):
    """
    Returns the absolute path from a base directory and a relative path.
    """
    return os.path.abspath(os.path.join(base_dir, relative_path))