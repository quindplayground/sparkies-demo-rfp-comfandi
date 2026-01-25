import pytest
from unittest.mock import Mock, create_autospec
from logging import LogRecord
import logging

from pyspark.sql import SparkSession

# Cargar handler por ruta para evitar ejecutar demo_comfandi_project.libs.logging.__init__
import importlib.util
from pathlib import Path

_handler_path = (
    Path(__file__).parents[3] / "demo_comfandi_project" / "libs" / "logging" / "handler.py"
)
spec = importlib.util.spec_from_file_location("ppd_logging_handler", str(_handler_path))
ppd_logging_handler = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
assert spec is not None and spec.loader is not None
spec.loader.exec_module(ppd_logging_handler)  # type: ignore[assignment]
Log4JProxyHandler = ppd_logging_handler.Log4JProxyHandler


@pytest.fixture
def mock_spark():
    """Create a mock SparkSession with JVM logger."""
    mock_spark = create_autospec(SparkSession, instance=True)
    mock_logger = Mock()
    mock_log4j = Mock()
    mock_log4j.Logger.getLogger.return_value = mock_logger

    mock_jvm = Mock()
    mock_org = Mock()
    mock_apache = Mock()
    mock_org.apache = mock_apache
    mock_apache.log4j = mock_log4j
    mock_jvm.org = mock_org

    mock_spark._jvm = mock_jvm
    return mock_spark


@pytest.fixture
def handler(mock_spark):
    """Create a Log4JProxyHandler instance."""
    return Log4JProxyHandler(mock_spark)


def test_handler_initialization(mock_spark):
    """Test that handler initializes correctly."""
    handler = Log4JProxyHandler(mock_spark)
    assert handler.logger == mock_spark._jvm.org.apache.log4j
    assert handler.max_msg_length == 10000


def test_handler_initialization_invalid_spark():
    """Test that handler raises error with invalid spark session."""
    with pytest.raises(
        ValueError, match="spark_session must be an instance of SparkSession"
    ):
        Log4JProxyHandler("not a spark session")


def test_handler_initialization_custom_max_length(mock_spark):
    """Test that handler accepts custom max message length."""
    handler = Log4JProxyHandler(mock_spark, max_msg_length=100)
    assert handler.max_msg_length == 100


def test_sanitize_message_truncation(handler):
    """Test that long messages are truncated."""
    long_message = "x" * 20000
    sanitized = handler._sanitize_message(long_message)
    assert len(sanitized) <= handler.max_msg_length
    assert sanitized.endswith("... (truncated)")


def test_sanitize_message_sensitive_data(handler):
    """Test that sensitive data is redacted."""
    sensitive_messages = [
        "password=secret123",
        "secret=mysecret",
        "token=abc123",
        "api_key=xyz789",
        "email=test@example.com",
        "card=1234-5678-9012-3456",
    ]
    for msg in sensitive_messages:
        sanitized = handler._sanitize_message(msg)
        assert "[REDACTED]" in sanitized
        assert msg not in sanitized


def test_sanitize_message_special_chars(handler):
    """Test that special characters are escaped."""
    message = "test\nmessage\rwith\tspecial chars"
    sanitized = handler._sanitize_message(message)
    assert "\n" not in sanitized
    assert "\r" not in sanitized
    assert "\t" not in sanitized


def test_get_safe_logger_invalid_name(handler, mock_spark):
    """Test that invalid logger names are handled safely."""
    unsafe_names = [None, 123, "unsafe/name", "unsafe;name", "unsafe$name"]
    for name in unsafe_names:
        safe_logger = handler._get_safe_logger(name)
        assert (
            safe_logger
            == mock_spark._jvm.org.apache.log4j.Logger.getLogger.return_value
        )
        if name is None or not isinstance(name, str):
            mock_spark._jvm.org.apache.log4j.Logger.getLogger.assert_called_with(
                "default"
            )
        else:
            called_name = mock_spark._jvm.org.apache.log4j.Logger.getLogger.call_args[
                0
            ][0]
            assert all(
                c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
                for c in called_name
            )


def test_handler_skips_py4j_records(handler):
    """Test that handler skips records from py4j."""
    record = LogRecord(
        name="py4j.something",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    handler.emit(record)
    assert not handler.logger.Logger.getLogger.called


def test_handler_handles_exception_gracefully(handler, mock_spark):
    """Test that handler handles exceptions gracefully."""
    mock_spark._jvm.org.apache.log4j.Logger.getLogger.side_effect = Exception(
        "Test error"
    )

    record = LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )

    handler.emit(record)


def test_handler_emits_critical(handler, mock_spark):
    """Test that handler emits CRITICAL level correctly."""
    record = LogRecord(
        name="test.logger",
        level=logging.CRITICAL,
        pathname="test.py",
        lineno=1,
        msg="critical message",
        args=(),
        exc_info=None,
    )
    handler.emit(record)

    mock_logger = mock_spark._jvm.org.apache.log4j.Logger.getLogger.return_value
    mock_logger.fatal.assert_called_once()
    # Check that the message contains the original message
    call_args = mock_logger.fatal.call_args[0][0]
    assert "critical message" in call_args


def test_handler_emits_error(handler, mock_spark):
    """Test that handler emits ERROR level correctly."""
    record = LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="error message",
        args=(),
        exc_info=None,
    )
    handler.emit(record)

    mock_logger = mock_spark._jvm.org.apache.log4j.Logger.getLogger.return_value
    mock_logger.error.assert_called_once()
    # Check that the message contains the original message
    call_args = mock_logger.error.call_args[0][0]
    assert "error message" in call_args


def test_handler_emits_warning(handler, mock_spark):
    """Test that handler emits WARNING level correctly."""
    record = LogRecord(
        name="test.logger",
        level=logging.WARNING,
        pathname="test.py",
        lineno=1,
        msg="warning message",
        args=(),
        exc_info=None,
    )
    handler.emit(record)

    mock_logger = mock_spark._jvm.org.apache.log4j.Logger.getLogger.return_value
    mock_logger.warn.assert_called_once()
    # Check that the message contains the original message
    call_args = mock_logger.warn.call_args[0][0]
    assert "warning message" in call_args


def test_handler_emits_info(handler, mock_spark):
    """Test that handler emits INFO level correctly."""
    record = LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="info message",
        args=(),
        exc_info=None,
    )
    handler.emit(record)

    mock_logger = mock_spark._jvm.org.apache.log4j.Logger.getLogger.return_value
    mock_logger.info.assert_called_once()
    # Check that the message contains the original message
    call_args = mock_logger.info.call_args[0][0]
    assert "info message" in call_args


def test_handler_emits_debug(handler, mock_spark):
    """Test that handler emits DEBUG level correctly."""
    record = LogRecord(
        name="test.logger",
        level=logging.DEBUG,
        pathname="test.py",
        lineno=1,
        msg="debug message",
        args=(),
        exc_info=None,
    )
    handler.emit(record)

    mock_logger = mock_spark._jvm.org.apache.log4j.Logger.getLogger.return_value
    mock_logger.debug.assert_called_once()
    # Check that the message contains the original message
    call_args = mock_logger.debug.call_args[0][0]
    assert "debug message" in call_args


def test_handler_uses_formatter_when_available(handler, mock_spark):
    """Test that handler uses formatter when available."""

    # Create a mock formatter
    mock_formatter = Mock()
    mock_formatter.format.return_value = "formatted message"
    handler.setFormatter(mock_formatter)

    record = LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="original message",
        args=(),
        exc_info=None,
    )

    handler.emit(record)

    # Verify formatter was called
    mock_formatter.format.assert_called_once_with(record)

    # Verify the formatted message was used
    mock_logger = mock_spark._jvm.org.apache.log4j.Logger.getLogger.return_value
    mock_logger.info.assert_called_once()
    call_args = mock_logger.info.call_args[0][0]
    assert "formatted message" in call_args


def test_handler_uses_getMessage_when_no_formatter(handler, mock_spark):
    """Test that handler uses getMessage when no formatter is available."""
    # Ensure no formatter is set
    handler.setFormatter(None)

    record = LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="original message",
        args=(),
        exc_info=None,
    )

    handler.emit(record)

    # Verify the original message was used
    mock_logger = mock_spark._jvm.org.apache.log4j.Logger.getLogger.return_value
    mock_logger.info.assert_called_once()
    call_args = mock_logger.info.call_args[0][0]
    assert "original message" in call_args
