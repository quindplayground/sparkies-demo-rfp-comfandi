"""Logging filters."""

from logging import Filter, LogRecord
from typing import Optional


class NoRecursiveFilter(Filter):
    """Logging filter to prevent recursive entries from Log4JProxyHandler."""

    def __init__(self, name: str = ""):
        """Initialize the NoRecursiveFilter.

        Args:
            name: The filter name. Defaults to "".
        """
        super().__init__(name)
        self.max_name_length = 1000

    def _is_valid_record(self, record: Optional[LogRecord]) -> bool:
        """Validate the given log record.

        Args:
            record: The log record to validate.

        Returns:
            True if the record is valid, False otherwise.
        """
        if not record or not isinstance(record, LogRecord):
            return False

        try:
            if not isinstance(record.name, str):
                return False
            if not isinstance(record.levelno, int):
                return False
            if not hasattr(record, "msg"):
                return False

            if len(record.name) > self.max_name_length:
                return False
        except Exception:
            return False

        return True

    def filter(self, record: LogRecord) -> bool:
        """Determine if the log record should be logged.

        Args:
            record: The log record to evaluate.

        Returns:
            True if the record is allowed, False otherwise.
        """
        if not self._is_valid_record(record):
            return False

        return "Log4JProxyHandler" not in record.name
