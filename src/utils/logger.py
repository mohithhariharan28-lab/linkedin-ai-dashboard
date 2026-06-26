import logging
import os
from pathlib import Path


def setup_logger(name: str = "linkedin_dashboard") -> logging.Logger:
    """Sets up a logger with both console and file handlers.

    Args:
        name: Name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Return existing logger if already configured to avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Formatter for logs
    log_format = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # File Handler (DEBUG level)
    # Determine the directory relative to this file
    project_root = Path(__file__).resolve().parent.parent.parent
    logs_dir = project_root / "logs"
    
    try:
        os.makedirs(logs_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            filename=logs_dir / "application.log",
            encoding="utf-8",
            mode="a"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not initialize file logging: {e}")

    return logger
