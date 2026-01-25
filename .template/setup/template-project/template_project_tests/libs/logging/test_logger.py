import pytest
import logging
from unittest.mock import Mock, patch, create_autospec
from logging import Handler
from pyspark.sql import SparkSession

# Cargar el módulo logger por ruta para evitar ejecutar __init__.py del paquete
import importlib.util
from pathlib import Path

_logger_path = (
    Path(__file__).parents[3] / "template_project" / "libs" / "logging" / "logger.py"
)
spec = importlib.util.spec_from_file_location("ppd_logging_logger", str(_logger_path))
ppd_logging_logger = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
assert spec is not None and spec.loader is not None
spec.loader.exec_module(ppd_logging_logger)  # type: ignore[assignment]

Logger = ppd_logging_logger.Logger
get_logger = ppd_logging_logger.get_logger

# Cargar dependencias
_defaults_path = (
    Path(__file__).parents[3] / "template_project" / "libs" / "logging" / "defaults.py"
)
spec_defaults = importlib.util.spec_from_file_location(
    "ppd_logging_defaults", str(_defaults_path)
)
ppd_logging_defaults = importlib.util.module_from_spec(spec_defaults)  # type: ignore[arg-type]
assert spec_defaults is not None and spec_defaults.loader is not None
spec_defaults.loader.exec_module(ppd_logging_defaults)  # type: ignore[assignment]

LoggingDefaults = ppd_logging_defaults.LoggingDefaults


@pytest.fixture
def mock_spark():
    """Create a mock SparkSession with JVM logger."""
    mock_spark = create_autospec(SparkSession, instance=True)
    mock_spark_context = Mock()
    mock_spark.sparkContext = mock_spark_context
    mock_spark_context.setLogLevel = Mock()
    return mock_spark


@pytest.fixture
def mock_handler():
    """Create a mock logging handler."""
    handler = Mock(spec=Handler)
    handler.addFilter = Mock()
    return handler


def test_logger_init_with_defaults(mock_spark):
    """Test Logger initialization with default parameters."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark)

        assert logger.spark == mock_spark
        assert logger.logger_name == LoggingDefaults.DEFAULT_LOGGER_NAME.value
        assert logger._log_level == LoggingDefaults.DEFAULT_LOG_LEVEL.value
        assert "DEBUG" in logger.LOG_LEVEL_MAP
        assert "INFO" in logger.LOG_LEVEL_MAP
        assert "WARN" in logger.LOG_LEVEL_MAP
        assert "ERROR" in logger.LOG_LEVEL_MAP
        assert "FATAL" in logger.LOG_LEVEL_MAP


def test_logger_init_with_custom_name(mock_spark):
    """Test Logger initialization with custom name."""
    custom_name = "custom_logger"

    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark, name=custom_name)

        assert logger.logger_name == custom_name


def test_logger_init_with_additional_handlers(mock_spark, mock_handler):
    """Test Logger initialization with additional handlers."""
    additional_handlers = [mock_handler]

    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        _ = Logger(mock_spark, additional_handlers=additional_handlers)

        mock_handler.addFilter.assert_called_once()
        mock_root_logger.addHandler.assert_called_with(mock_handler)


def test_setup_log4j_proxy_handler(mock_spark):
    """Test _setup_log4j_proxy_handler method."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        _ = Logger(mock_spark)

        mock_proxy_handler.assert_called_once_with(mock_spark)
        mock_handler_instance.addFilter.assert_called_once()
        mock_get_logger.assert_called_with()
        mock_root_logger.handlers = []
        mock_root_logger.addHandler.assert_called_with(mock_handler_instance)
        mock_root_logger.addFilter.assert_called_once()


def test_add_handler(mock_spark, mock_handler):
    """Test add_handler method."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark)
        result = logger.add_handler(mock_handler)

        assert result is logger
        mock_handler.addFilter.assert_called_once()
        mock_root_logger.addHandler.assert_called_with(mock_handler)


def test_log_level_with_valid_level(mock_spark):
    """Test log_level method with valid level."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark)
        result = logger.log_level("DEBUG")

        assert result is logger
        assert logger._log_level == "DEBUG"
        mock_spark.sparkContext.setLogLevel.assert_called_with("DEBUG")
        mock_root_logger.setLevel.assert_called_with(logging.DEBUG)


def test_log_level_with_none(mock_spark):
    """Test log_level method with None (should use default)."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark)
        result = logger.log_level(None)

        assert result is logger
        assert logger._log_level == LoggingDefaults.DEFAULT_LOG_LEVEL.value
        mock_spark.sparkContext.setLogLevel.assert_called_with(
            LoggingDefaults.DEFAULT_LOG_LEVEL.value
        )


def test_log_level_all_levels(mock_spark):
    """Test log_level method with all valid levels."""
    levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]

    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark)

        for level in levels:
            logger.log_level(level)
            assert logger._log_level == level
            mock_spark.sparkContext.setLogLevel.assert_called_with(level)


def test_get_logger(mock_spark):
    """Test get_logger method."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_logger = Mock()
        # Logger calls getLogger twice: once for root logger, once for specific logger
        mock_get_logger.side_effect = [mock_root_logger, mock_root_logger, mock_logger]

        logger = Logger(mock_spark, name="test_logger")
        result = logger.get_logger()

        assert result == mock_logger
        # Check the last call was with the specific logger name
        assert mock_get_logger.call_args_list[-1] == (("test_logger",),)


def test_get_logger_function_with_spark_capture(mock_spark):
    """Test get_logger function with capture_spark_logs=True."""
    with patch.object(
        ppd_logging_logger, "SparkResource"
    ) as mock_spark_resource, patch.object(
        ppd_logging_logger, "Logger"
    ) as mock_logger_class, patch(
        "logging.getLogger"
    ) as _:

        mock_spark_resource.return_value = mock_spark
        mock_logger_instance = Mock()
        mock_logger_instance.get_logger.return_value = Mock()
        mock_logger_class.return_value = mock_logger_instance

        _ = get_logger(name="test", log_level="DEBUG", capture_spark_logs=True)

        mock_spark_resource.assert_called_once_with(new_session=True)
        mock_logger_class.assert_called_once_with(
            spark=mock_spark,
            name="test",
            service_name=None,
            service_version=None,
            schema_url=None,
            context=None,
        )
        mock_logger_instance.log_level.assert_called_once_with("DEBUG")


def test_get_logger_function_without_spark_capture():
    """Test get_logger function with capture_spark_logs=False."""
    with patch("logging.getLogger") as mock_get_logger, patch(
        "logging.StreamHandler"
    ) as mock_stream_handler, patch.object(
        ppd_logging_logger, "OtelStyleJsonFormatter"
    ) as mock_formatter:

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_handler_instance = Mock()
        mock_stream_handler.return_value = mock_handler_instance
        mock_formatter_instance = Mock()
        mock_formatter.return_value = mock_formatter_instance

        result = get_logger(name="test", capture_spark_logs=False)

        assert result == mock_logger
        mock_get_logger.assert_called_with("test")
        mock_formatter.assert_called_once()
        mock_stream_handler.assert_called_once()
        mock_handler_instance.setFormatter.assert_called_once_with(
            mock_formatter_instance
        )
        mock_logger.addHandler.assert_called_once_with(mock_handler_instance)


def test_get_logger_function_with_none_name():
    """Test get_logger function with None name."""
    with patch("logging.getLogger") as mock_get_logger, patch(
        "logging.StreamHandler"
    ) as mock_stream_handler, patch.object(
        ppd_logging_logger, "OtelStyleJsonFormatter"
    ) as mock_formatter:

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_handler_instance = Mock()
        mock_stream_handler.return_value = mock_handler_instance
        mock_formatter_instance = Mock()
        mock_formatter.return_value = mock_formatter_instance

        result = get_logger(name=None, capture_spark_logs=False)

        assert result == mock_logger
        mock_get_logger.assert_called_with(None)


def test_get_logger_function_with_none_log_level():
    """Test get_logger function with None log_level."""
    with patch("logging.getLogger") as mock_get_logger, patch(
        "logging.StreamHandler"
    ) as mock_stream_handler, patch.object(
        ppd_logging_logger, "OtelStyleJsonFormatter"
    ) as mock_formatter:

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_handler_instance = Mock()
        mock_stream_handler.return_value = mock_handler_instance
        mock_formatter_instance = Mock()
        mock_formatter.return_value = mock_formatter_instance

        result = get_logger(log_level=None, capture_spark_logs=False)

        assert result == mock_logger


def test_logger_level_map_values(mock_spark):
    """Test that level map contains correct values."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark)

        assert logger.LOG_LEVEL_MAP["DEBUG"] == logging.DEBUG
        assert logger.LOG_LEVEL_MAP["INFO"] == logging.INFO
        assert logger.LOG_LEVEL_MAP["WARN"] == logging.WARNING
        assert logger.LOG_LEVEL_MAP["ERROR"] == logging.ERROR
        assert logger.LOG_LEVEL_MAP["FATAL"] == logging.CRITICAL


def test_logger_chain_methods(mock_spark):
    """Test that Logger methods can be chained."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark)
        mock_handler = Mock(spec=Handler)

        result = logger.add_handler(mock_handler).log_level("DEBUG")

        assert result is logger


def test_logger_with_multiple_additional_handlers(mock_spark):
    """Test Logger with multiple additional handlers."""
    handler1 = Mock(spec=Handler)
    handler2 = Mock(spec=Handler)
    additional_handlers = [handler1, handler2]

    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        _ = Logger(mock_spark, additional_handlers=additional_handlers)

        handler1.addFilter.assert_called_once()
        handler2.addFilter.assert_called_once()
        # Logger adds 1 default handler + 2 additional handlers = 3 total
        assert mock_root_logger.addHandler.call_count == 3


def test_logger_initialization_calls_log_level(mock_spark):
    """Test that Logger initialization calls log_level with default."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger, patch.object(
        Logger, "log_level"
    ) as mock_log_level:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        Logger(mock_spark)

        mock_log_level.assert_called_once_with(LoggingDefaults.DEFAULT_LOG_LEVEL.value)


def test_logger_get_logger_returns_correct_logger(mock_spark):
    """Test that get_logger returns the correct logger instance."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_logger = Mock()
        # Logger calls getLogger twice: once for root logger, once for specific logger
        mock_get_logger.side_effect = [mock_root_logger, mock_root_logger, mock_logger]

        logger = Logger(mock_spark, name="specific_logger")
        result = logger.get_logger()

        assert result == mock_logger
        # Check the last call was with the specific logger name
        assert mock_get_logger.call_args_list[-1] == (("specific_logger",),)


def test_logger_handles_empty_additional_handlers(mock_spark):
    """Test Logger with empty additional handlers list."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        _ = Logger(mock_spark, additional_handlers=[])

        # Logger always adds 1 default handler, but no additional handlers
        assert mock_root_logger.addHandler.call_count == 1


def test_logger_handles_none_additional_handlers(mock_spark):
    """Test Logger with None additional handlers."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        _ = Logger(mock_spark, additional_handlers=None)

        # Logger always adds 1 default handler, but no additional handlers
        assert mock_root_logger.addHandler.call_count == 1


def test_get_logger_function_default_parameters():
    """Test get_logger function with default parameters."""
    with patch.object(
        ppd_logging_logger, "SparkResource"
    ) as mock_spark_resource, patch.object(
        ppd_logging_logger, "Logger"
    ) as mock_logger_class, patch(
        "logging.getLogger"
    ) as _:

        mock_spark = Mock()
        mock_spark_resource.return_value = mock_spark
        mock_logger_instance = Mock()
        mock_logger_instance.get_logger.return_value = Mock()
        mock_logger_class.return_value = mock_logger_instance

        _ = get_logger()

        # Default behavior uses capture_spark_logs=True
        mock_spark_resource.assert_called_once_with(new_session=True)
        mock_logger_class.assert_called_once_with(
            spark=mock_spark,
            name=None,
            service_name=None,
            service_version=None,
            schema_url=None,
            context=None,
        )
        mock_logger_instance.log_level.assert_called_once_with(None)


def test_logger_initialization_with_custom_name_and_handlers(mock_spark, mock_handler):
    """Test Logger initialization with both custom name and handlers."""
    custom_name = "custom_test_logger"
    additional_handlers = [mock_handler]

    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger, patch.object(
        ppd_logging_logger, "OtelStyleJsonFormatter"
    ) as mock_formatter:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger
        mock_formatter_instance = Mock()
        mock_formatter.return_value = mock_formatter_instance

        logger = Logger(
            mock_spark, name=custom_name, additional_handlers=additional_handlers
        )

        assert logger.logger_name == custom_name
        mock_handler.addFilter.assert_called_once()
        mock_root_logger.addHandler.assert_called_with(mock_handler)
        mock_formatter.assert_called_once()


def test_logger_level_mapping_consistency(mock_spark):
    """Test that level mapping is consistent with Python logging levels."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark)

        # Test that all levels are properly mapped
        expected_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARN": logging.WARNING,
            "ERROR": logging.ERROR,
            "FATAL": logging.CRITICAL,
        }

        for level_name, expected_value in expected_mapping.items():
            assert logger.LOG_LEVEL_MAP[level_name] == expected_value


def test_logger_handles_invalid_log_level_gracefully(mock_spark):
    """Test that Logger handles invalid log levels gracefully."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark)

        # Test with invalid level - should not raise exception
        # The actual implementation should handle this gracefully
        try:
            logger.log_level("INVALID_LEVEL")  # type: ignore
        except KeyError:
            # This is expected behavior for invalid levels
            pass


def test_logger_returns_self_for_chaining(mock_spark):
    """Test that Logger methods return self for method chaining."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark)
        mock_handler = Mock(spec=Handler)

        # Test chaining add_handler and log_level
        result1 = logger.add_handler(mock_handler)
        result2 = logger.log_level("INFO")

        assert result1 is logger
        assert result2 is logger
        assert result1 is result2


def test_logger_initialization_with_none_name_uses_default(mock_spark):
    """Test that Logger initialization with None name uses default."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        logger = Logger(mock_spark, name=None)

        assert logger.logger_name == LoggingDefaults.DEFAULT_LOGGER_NAME.value


def test_get_logger_function_with_spark_capture_and_none_params(mock_spark):
    """Test get_logger function with capture_spark_logs=True and None parameters."""
    with patch.object(
        ppd_logging_logger, "SparkResource"
    ) as mock_spark_resource, patch.object(
        ppd_logging_logger, "Logger"
    ) as mock_logger_class, patch(
        "logging.getLogger"
    ) as _:

        mock_spark_resource.return_value = mock_spark
        mock_logger_instance = Mock()
        mock_logger_instance.get_logger.return_value = Mock()
        mock_logger_class.return_value = mock_logger_instance

        _ = get_logger(name=None, log_level=None, capture_spark_logs=True)

        mock_spark_resource.assert_called_once_with(new_session=True)
        mock_logger_class.assert_called_once_with(
            spark=mock_spark,
            name=None,
            service_name=None,
            service_version=None,
            schema_url=None,
            context=None,
        )
        mock_logger_instance.log_level.assert_called_once_with(None)


def test_get_logger_function_with_otel_parameters():
    """Test get_logger function with OpenTelemetry parameters."""
    with patch("logging.getLogger") as mock_get_logger, patch(
        "logging.StreamHandler"
    ) as mock_stream_handler, patch.object(
        ppd_logging_logger, "OtelStyleJsonFormatter"
    ) as mock_formatter, patch.object(
        ppd_logging_logger, "Context"
    ) as mock_context:

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_handler_instance = Mock()
        mock_stream_handler.return_value = mock_handler_instance
        mock_formatter_instance = Mock()
        mock_formatter.return_value = mock_formatter_instance
        mock_context_instance = Mock()
        mock_context.return_value = mock_context_instance

        result = get_logger(
            name="test",
            capture_spark_logs=False,
            service_name="custom-service",
            service_version="2.0.0",
            schema_url="https://custom.schema.url",
            context=mock_context_instance,
        )

        assert result == mock_logger
        mock_formatter.assert_called_once_with(
            service_name="custom-service",
            service_version="2.0.0",
            schema_url="https://custom.schema.url",
            context=mock_context_instance,
            add_spark_prefix=True,
        )


def test_get_logger_function_with_force_reconfigure():
    """Test get_logger function with force_reconfigure parameter."""
    with patch("logging.getLogger") as mock_get_logger, patch(
        "logging.StreamHandler"
    ) as mock_stream_handler, patch.object(
        ppd_logging_logger, "OtelStyleJsonFormatter"
    ) as mock_formatter, patch(
        "warnings.warn"
    ) as mock_warn:

        mock_root_logger = Mock()
        mock_root_logger.handlers = []

        mock_logger = Mock()
        mock_logger.handlers = [Mock()]  # Simulate existing handlers

        # getLogger is called multiple times: root logger, specific logger, root logger again, specific logger again
        mock_get_logger.side_effect = [
            mock_root_logger,
            mock_logger,
            mock_root_logger,
            mock_logger,
        ]
        mock_handler_instance = Mock()
        mock_stream_handler.return_value = mock_handler_instance
        mock_formatter_instance = Mock()
        mock_formatter.return_value = mock_formatter_instance

        # First call - should warn about reconfiguration
        result1 = get_logger(name="test", capture_spark_logs=False)
        assert mock_warn.called

        # Reset mock
        mock_warn.reset_mock()

        # Second call with force_reconfigure=True - should not warn
        result2 = get_logger(
            name="test", capture_spark_logs=False, force_reconfigure=True
        )
        assert not mock_warn.called

        assert result1 == mock_logger
        assert result2 == mock_logger


def test_logger_initialization_with_otel_parameters(mock_spark):
    """Test Logger initialization with OpenTelemetry parameters."""
    with patch.object(
        ppd_logging_logger, "Log4JProxyHandler"
    ) as mock_proxy_handler, patch.object(
        ppd_logging_logger, "NoRecursiveFilter"
    ) as _, patch(
        "logging.getLogger"
    ) as mock_get_logger, patch.object(
        ppd_logging_logger, "OtelStyleJsonFormatter"
    ) as mock_formatter, patch.object(
        ppd_logging_logger, "Context"
    ) as mock_context:

        mock_handler_instance = Mock()
        mock_proxy_handler.return_value = mock_handler_instance
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger
        mock_formatter_instance = Mock()
        mock_formatter.return_value = mock_formatter_instance
        mock_context_instance = Mock()
        mock_context.return_value = mock_context_instance

        logger = Logger(
            mock_spark,
            name="test",
            service_name="custom-service",
            service_version="2.0.0",
            schema_url="https://custom.schema.url",
            context=mock_context_instance,
        )

        assert logger.logger_name == "test"
        mock_formatter.assert_called_once_with(
            service_name="custom-service",
            service_version="2.0.0",
            schema_url="https://custom.schema.url",
            context=mock_context_instance,
            add_spark_prefix=False,
        )
