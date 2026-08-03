"""Logging setup shared by every entry point."""

import logging
import os

DEFAULT_FORMAT = '%(asctime)s %(levelname)s [%(name)s] %(message)s'


def configure_logging(level: str = None) -> None:
    """Configure root logging once, honouring the LOG_LEVEL environment variable."""
    resolved = (level or os.getenv('LOG_LEVEL', 'INFO')).upper()
    if resolved not in logging._nameToLevel:
        resolved = 'INFO'

    logging.basicConfig(level=resolved, format=DEFAULT_FORMAT)

    # APScheduler logs job crashes at ERROR; without this they are invisible.
    logging.getLogger('apscheduler').setLevel(logging.INFO)
