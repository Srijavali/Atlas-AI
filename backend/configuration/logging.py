import logging
import sys
from backend.configuration.settings import settings

def setup_logging() -> logging.Logger:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logger = logging.getLogger("atlas_ai")
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logging()
