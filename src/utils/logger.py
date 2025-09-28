"""
Logging utilities for Orchesity IDE OSS
"""

import logging
import sys
from pathlib import Path
from ..config import settings


def setup_logger():
    """Setup basic logging configuration"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger("orchesity_ide")
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Set logging level for external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)

    return logger


def get_logger(name: str = "orchesity_ide") -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(f"{name}")
