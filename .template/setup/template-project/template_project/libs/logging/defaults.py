"""Default configurations for logging."""

import enum
import os
from template_project import __version__


class LoggingDefaults(enum.Enum):
    """Enumeration of default logging configurations."""

    DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "WARN")
    DEFAULT_LOGGER_NAME = "template_project"
    DEFAULT_SERVICE_NAME = "nutresa-data-platform-template-project"
    DEFAULT_SERVICE_VERSION = __version__
    DEFAULT_SCHEMA_URL = "https://opentelemetry.io/schemas/1.0.0"
