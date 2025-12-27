import json

# [DELETED] Remove the original top-level import: from tools.logger import get_logger

# Define a placeholder and a lazy loading function
logger = None


def _get_logger():
    """Lazily loads the logger when first needed."""
    global logger
    if logger is None:
        from tools.logger import get_logger

        logger = get_logger("JsonAggregator")
    return logger


def save_json(data: dict, path: str):
    _logger = _get_logger()  # Load logger here
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        _logger.error(f"Error saving JSON to {path}: {e}")


def load_json(path: str) -> dict:
    _logger = _get_logger()  # Load logger here
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        _logger.error(f"JSON file not found: {path}")
        return {}
    except json.JSONDecodeError:
        _logger.error(f"Error decoding JSON from file: {path}")
        return {}
    except Exception as e:
        _logger.error(f"Error loading JSON from {path}: {e}")
        return {}
