import logging


def configure_logging() -> logging.Logger:
    """Configure consistent console logging and return the application logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return logging.getLogger("cogtic")


logger = logging.getLogger("cogtic")
