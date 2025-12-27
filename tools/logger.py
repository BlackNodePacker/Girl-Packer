# GameMediaTool/tools/logger.py

import sys
from loguru import logger

# Configure the logger to have a specific format and colorization
# This configuration is applied only once when the module is imported.
logger.remove()  # Remove the default handler
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
