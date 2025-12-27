import os
import shutil
import re
# [DELETED] Remove this line to break the circular dependency
# from tools.logger import get_logger

# [NEW] Define a placeholder logger variable
logger = None 

def _get_logger():
    """Lazily loads the logger when first needed."""
    global logger
    if logger is None:
        from tools.logger import get_logger
        logger = get_logger("FileOps")
    return logger

def sanitize_filename(name: str) -> str:
    """Removes characters that are invalid in Windows filenames and replaces spaces."""
    sanitized = re.sub(r'[\\/*?:"<>|]', "", name)
    return sanitized.replace(" ", "_")

def ensure_folder(path: str):
    """Ensures that a directory exists. If it doesn't, it creates it."""
    _logger = _get_logger()
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except Exception as e:
        _logger.error(f"Failed to create directory {path}: {e}")

def list_files(folder: str, extensions: tuple = None) -> list:
    """Lists files in a directory with optional extension filtering."""
    _logger = _get_logger()
    if not os.path.isdir(folder):
        _logger.warning(f"Directory not found: {folder}")
        return []
    
    try:
        files_found = []
        for f in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, f)):
                if extensions is None or f.lower().endswith(extensions):
                    files_found.append(os.path.join(folder, f))
        return files_found
    except Exception as e:
        _logger.error(f"Failed to list files in {folder}: {e}")
        return []