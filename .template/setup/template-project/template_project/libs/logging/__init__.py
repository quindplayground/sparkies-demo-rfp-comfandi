"""Logging module with OpenTelemetry integration."""

from template_project.libs.logging.logger import get_logger, Logger
from template_project.libs.logging.defaults import LoggingDefaults

__all__ = ["get_logger", "Logger", "LoggingDefaults"]
