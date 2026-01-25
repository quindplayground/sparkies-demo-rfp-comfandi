import logging
import sys
from typing import Optional


def setup_logger(name: str = "setup_project", level: int = logging.INFO,
                 dry_run: bool = False) -> logging.Logger:
    """Configures and returns a logger for setup scripts.

    Args:
        name: Logger name.
        level: Logging level. Defaults to INFO.
        dry_run: If True, adds [DRY RUN] prefix to messages.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if dry_run:
        formatter = logging.Formatter('[DRY RUN] %(message)s')
    else:
        formatter = logging.Formatter('%(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
