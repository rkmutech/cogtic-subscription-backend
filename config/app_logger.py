import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging() -> logging.Logger:
    """Write application logs to the console and a rotating project log file."""
    app_logger = logging.getLogger("cogtic")
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False

    if not app_logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
        log_directory = Path(__file__).resolve().parents[1] / "logs"
        log_directory.mkdir(parents=True, exist_ok=True)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        file_handler = RotatingFileHandler(
            log_directory / "app.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        app_logger.addHandler(console_handler)
        app_logger.addHandler(file_handler)

    return app_logger


logger = logging.getLogger("cogtic")
