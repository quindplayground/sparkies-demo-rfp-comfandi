"""Main logger with Spark Log4J and OpenTelemetry integration."""

import logging
from logging import Handler
from typing import Literal, Sequence, Self
from pyspark.sql import SparkSession

from demo_comfandi_project.libs.resources.spark_resource import SparkResource
from demo_comfandi_project.libs.logging.defaults import LoggingDefaults
from demo_comfandi_project.libs.logging.filter import NoRecursiveFilter
from demo_comfandi_project.libs.logging.handler import Log4JProxyHandler
from demo_comfandi_project.libs.logging.formatter import OtelStyleJsonFormatter
from demo_comfandi_project.libs.context import Context


_LOG_LEVEL_TYPE = Literal["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]


class Logger:
    """Logger wrapper that integrates Python logging with Spark's Log4J system."""

    LOG_LEVEL_MAP: dict[_LOG_LEVEL_TYPE, int] = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "FATAL": logging.CRITICAL,
    }

    def __init__(
        self,
        spark: SparkSession,
        name: str | None = None,
        additional_handlers: Sequence[Handler] | None = None,
        service_name: str | None = None,
        service_version: str | None = None,
        schema_url: str | None = None,
        context: Context | None = None,
    ):
        """Initialize the Logger.

        Args:
            spark: Active Spark session for accessing JVM Log4J.
            name: Logger name (optional).
            additional_handlers: Additional handlers to add (optional).
            service_name: Service name for OpenTelemetry (optional).
            service_version: Service version for OpenTelemetry (optional).
            schema_url: Schema URL for OpenTelemetry (optional).
            context: Context provider for Opel data (optional).
        """
        self.spark = spark
        self.logger_name = name or LoggingDefaults.DEFAULT_LOGGER_NAME.value
        self._log_level: _LOG_LEVEL_TYPE = LoggingDefaults.DEFAULT_LOG_LEVEL.value

        self._setup_otel_formatter(
            service_name=service_name or LoggingDefaults.DEFAULT_SERVICE_NAME.value,
            service_version=service_version
            or LoggingDefaults.DEFAULT_SERVICE_VERSION.value,
            schema_url=schema_url or LoggingDefaults.DEFAULT_SCHEMA_URL.value,
            context=context,
        )

        self._setup_log4j_proxy_handler()

        if additional_handlers:
            for handler in additional_handlers:
                self.add_handler(handler)

        self.log_level(self._log_level)

    def _setup_otel_formatter(
        self,
        service_name: str | None = None,
        service_version: str | None = None,
        schema_url: str | None = None,
        context: Context | None = None,
    ) -> None:
        """Set up the OpenTelemetry JSON formatter.

        Args:
            service_name: Service name for OpenTelemetry (optional).
            service_version: Service version for OpenTelemetry (optional).
            schema_url: Schema URL for OpenTelemetry (optional).
            context: Context provider for Opel data (optional).
        """
        self.otel_formatter = OtelStyleJsonFormatter(
            service_name=service_name,
            service_version=service_version,
            schema_url=schema_url,
            context=context or Context(),
            add_spark_prefix=False,
        )

    def _setup_log4j_proxy_handler(self) -> None:
        """Set up the default Log4J proxy handler with filtering and OpenTelemetry formatting."""
        handler = Log4JProxyHandler(self.spark)
        handler.addFilter(NoRecursiveFilter())
        handler.setFormatter(self.otel_formatter)

        root_logger = logging.getLogger()
        root_logger.handlers = []
        root_logger.addHandler(handler)
        root_logger.addFilter(NoRecursiveFilter())

    def add_handler(self, handler: Handler) -> Self:
        """Add a custom logging handler with no-recursion filter and OpenTelemetry formatting.

        Args:
            handler: Logging handler to add.

        Returns:
            The Logger instance.
        """
        handler.addFilter(NoRecursiveFilter())
        handler.setFormatter(self.otel_formatter)
        logging.getLogger().addHandler(handler)
        return self

    def log_level(self, log_level: _LOG_LEVEL_TYPE | None = None) -> Self:
        """Set the logging level.

        Args:
            log_level: Logging level to set.

        Returns:
            The Logger instance.
        """
        log_level = log_level or LoggingDefaults.DEFAULT_LOG_LEVEL.value  # type: ignore

        self.spark.sparkContext.setLogLevel(log_level)
        logging.getLogger().setLevel(self.LOG_LEVEL_MAP[log_level])
        self._log_level = log_level
        return self

    def get_logger(self) -> logging.Logger:
        """Get the logger instance.

        Returns:
            The logger instance.
        """
        return logging.getLogger(self.logger_name)


def get_logger(
    name: str | None = None,
    log_level: _LOG_LEVEL_TYPE | None = None,
    capture_spark_logs: bool = True,
    service_name: str | None = None,
    service_version: str | None = None,
    schema_url: str | None = None,
    context: Context | None = None,
    force_reconfigure: bool = False,
) -> logging.Logger:
    """Factory function to create a Logger instance.

    Args:
        name: Logger name (optional).
        log_level: Logging level to set (optional).
        capture_spark_logs: Whether to capture Spark logs. Defaults to True.
        service_name: Service name for OpenTelemetry (optional).
        service_version: Service version for OpenTelemetry (optional).
        schema_url: Schema URL for OpenTelemetry (optional).
        context: Context provider for Opel data (optional).
        force_reconfigure: Whether to force reconfiguration of existing logger. Defaults to False.

    Returns:
        A configured Logger instance.
    """
    if capture_spark_logs:
        spark = SparkResource(new_session=True)
        logger = Logger(
            spark=spark,
            name=name,
            service_name=service_name,
            service_version=service_version,
            schema_url=schema_url,
            context=context,
        ).log_level(log_level)

        return logger.get_logger()

    root_logger = logging.getLogger()
    root_logger.handlers = []

    logger = logging.getLogger(name)

    if logger.handlers and not force_reconfigure:
        import warnings

        warnings.warn(
            f"Logger '{name}' already exists and will be reconfigured. "
            f"Use force_reconfigure=True to suppress this warning.",
            UserWarning,
            stacklevel=2,
        )

    logger.handlers = []

    otel_formatter = OtelStyleJsonFormatter(
        service_name=service_name or LoggingDefaults.DEFAULT_SERVICE_NAME.value,
        service_version=service_version
        or LoggingDefaults.DEFAULT_SERVICE_VERSION.value,
        schema_url=schema_url or LoggingDefaults.DEFAULT_SCHEMA_URL.value,
        context=context,
        add_spark_prefix=True,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(otel_formatter)
    logger.addHandler(handler)
    logger.setLevel(
        Logger.LOG_LEVEL_MAP[log_level]
        if log_level
        else LoggingDefaults.DEFAULT_LOG_LEVEL.value
    )

    logger.propagate = False

    return logger
