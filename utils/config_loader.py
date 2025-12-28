# GameMediaTool/utils/config_loader.py

import yaml
import sys
import os
from tools.logger import get_logger

logger = get_logger("ConfigLoader")


def load_config(config_path: str = "config.yaml") -> dict:
    """
    Loads a configuration dictionary from a YAML file.

    Args:
        config_path (str): The path to the YAML configuration file.

    Returns:
        dict: The configuration dictionary, or an empty dict if an error occurs.
    """
    if getattr(sys, 'frozen', False):
        config_path = os.path.join(sys._MEIPASS, config_path)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info(f"Configuration loaded successfully from {config_path}")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found at: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {config_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading config: {e}")
        return {}
