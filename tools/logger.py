# GameMediaTool/tools/logger.py

import sys
from loguru import logger

# Configure the logger to have a specific format and colorization
# This configuration is applied only once when the module is imported.
logger.remove()  # Remove the default handler

# Add file handler
import os
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")
logger.add(
    log_file,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="10 MB",
    retention="1 week",
    enqueue=True,
)

# Add console handler if not bundled
if not getattr(sys, 'frozen', False):
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )


def get_logger(name: str):
    """
    Returns a logger instance with the specified name.
    Since loguru shares configuration, this is mainly for semantic naming in logs.
    """
    return logger.bind(name=name)
