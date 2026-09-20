import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """
    Configures centralized application logging with ISO timestamps, module names, and configurable log levels.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Reduce noisy logs from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger("ai_incident_commander")
    logger.info(
        f"Logging initialized for '{settings.APP_NAME}' [{settings.APP_ENV}] at level '{settings.LOG_LEVEL}'"
    )


logger = logging.getLogger("ai_incident_commander")
