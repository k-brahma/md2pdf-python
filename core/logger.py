"""Application-wide logging configuration."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pdf_converter.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def configure_logger():
    """Return the shared logger, configured once per process."""
    app_logger = logging.getLogger("md2pdf")
    app_logger.setLevel(logging.DEBUG)
    app_logger.propagate = False

    if app_logger.handlers:
        return app_logger

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    app_logger.debug("Logger initialized: %s", LOG_FILE)
    return app_logger


logger = configure_logger()
