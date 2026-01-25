"""Logging handlers."""

import logging
import re
from logging import Handler, LogRecord
from typing import Optional

from pyspark.sql import SparkSession


class Log4JProxyHandler(Handler):
    """Logging handler that proxies log messages to Spark's Log4J system with sanitization."""

    SENSITIVE_PATTERNS = [
        r'password=\S+',
        r'secret=\S+',
        r'token=\S+',
        r'api[_-]?key=\S+',
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
    ]

    TRUNCATE_SUFFIX = "... (truncated)"

    def __init__(self, spark_session: SparkSession, max_msg_length: int = 10000):
        """Initialize the Log4JProxyHandler.

        Args:
            spark_session: The Spark session used to access the JVM logger.
            max_msg_length: Maximum length for log messages. Defaults to 10000.

        Raises:
            ValueError: If spark_session is not a SparkSession instance.
        """
        super().__init__()
        if not isinstance(spark_session, SparkSession):
            raise ValueError("spark_session must be an instance of SparkSession")

        self.logger = spark_session._jvm.org.apache.log4j  # type: ignore
        self.max_msg_length = max_msg_length

    def _sanitize_message(self, message: str) -> str:
        """Sanitize a log message by redacting sensitive patterns and truncating if necessary.

        Args:
            message: The log message.

        Returns:
            The sanitized log message.
        """
        if not isinstance(message, str):
            message = str(message)

        if len(message) > self.max_msg_length:
            available_length = self.max_msg_length - len(self.TRUNCATE_SUFFIX)
            message = message[:available_length] + self.TRUNCATE_SUFFIX

        for pattern in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, '[REDACTED]', message)

        message = message.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        return message

    def _get_safe_logger(self, name: Optional[str]) -> object:
        """Get a safe logger instance by sanitizing the logger name.

        Args:
            name: The logger name.

        Returns:
            A Log4J logger instance.
        """
        if not name or not isinstance(name, str):
            name = "default"
        safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
        return self.logger.Logger.getLogger(safe_name)  # type: ignore

    def emit(self, record: LogRecord):
        """Emit a log record to the corresponding Log4J logger after sanitizing the message.

        Args:
            record: The log record to emit.
        """
        try:
            if "py4j" in record.name:
                return

            if self.formatter:
                message = self._sanitize_message(self.formatter.format(record))
            else:
                message = self._sanitize_message(record.getMessage())

            log = self._get_safe_logger(record.name)

            if record.levelno >= logging.CRITICAL:
                log.fatal(message)  # type: ignore
            elif record.levelno >= logging.ERROR:
                log.error(message)  # type: ignore
            elif record.levelno >= logging.WARNING:
                log.warn(message)  # type: ignore
            elif record.levelno >= logging.INFO:
                log.info(message)  # type: ignore
            elif record.levelno >= logging.DEBUG:
                log.debug(message)  # type: ignore
        except Exception as _:
            self.handleError(record)
