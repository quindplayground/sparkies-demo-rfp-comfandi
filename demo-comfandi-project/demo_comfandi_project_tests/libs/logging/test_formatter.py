import pytest
import json
import logging
from pathlib import Path
import importlib.util

# Cargar el módulo formatter por ruta para evitar ejecutar __init__.py del paquete
_formatter_path = (
    Path(__file__).parents[3] / "demo_comfandi_project" / "libs" / "logging" / "formatter.py"
)
spec = importlib.util.spec_from_file_location(
    "ppd_logging_formatter", str(_formatter_path)
)
ppd_logging_formatter = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
assert spec is not None and spec.loader is not None
spec.loader.exec_module(ppd_logging_formatter)  # type: ignore[assignment]

OtelStyleJsonFormatter = ppd_logging_formatter.OtelStyleJsonFormatter
OTEL_LEVEL_MAP = ppd_logging_formatter.OTEL_LEVEL_MAP
LOG_RECORD_FLAGS = ppd_logging_formatter.LOG_RECORD_FLAGS

# Cargar Context
_context_path = Path(__file__).parents[3] / "demo_comfandi_project" / "libs" / "context.py"
spec_context = importlib.util.spec_from_file_location("ppd_context", str(_context_path))
ppd_context = importlib.util.module_from_spec(spec_context)  # type: ignore[arg-type]
assert spec_context is not None and spec_context.loader is not None
spec_context.loader.exec_module(ppd_context)  # type: ignore[assignment]

Context = ppd_context.Context

# Cargar defaults
_defaults_path = (
    Path(__file__).parents[3] / "demo_comfandi_project" / "libs" / "logging" / "defaults.py"
)
spec_defaults = importlib.util.spec_from_file_location(
    "ppd_logging_defaults", str(_defaults_path)
)
ppd_logging_defaults = importlib.util.module_from_spec(spec_defaults)  # type: ignore[arg-type]
assert spec_defaults is not None and spec_defaults.loader is not None
spec_defaults.loader.exec_module(ppd_logging_defaults)  # type: ignore[assignment]

LoggingDefaults = ppd_logging_defaults.LoggingDefaults


@pytest.fixture
def context():
    """Create a Context instance for testing."""
    context = Context()
    context.clear()
    return context


@pytest.fixture
def formatter(context):
    """Create an OtelStyleJsonFormatter instance."""
    return OtelStyleJsonFormatter(context=context)


@pytest.fixture
def formatter_with_spark_prefix(context):
    """Create an OtelStyleJsonFormatter instance with Spark prefix enabled."""
    return OtelStyleJsonFormatter(context=context, add_spark_prefix=True)


@pytest.fixture
def formatter_without_spark_prefix(context):
    """Create an OtelStyleJsonFormatter instance with Spark prefix disabled."""
    return OtelStyleJsonFormatter(context=context, add_spark_prefix=False)


@pytest.fixture
def sample_record():
    """Create a sample LogRecord for testing."""
    return logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="/path/to/test.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None,
    )


@pytest.fixture
def error_record():
    """Create a LogRecord with exception info."""
    try:
        raise ValueError("Test error")
    except ValueError:
        import sys

        return logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/path/to/test.py",
            lineno=50,
            msg="Error occurred",
            args=(),
            exc_info=sys.exc_info(),
        )


def test_formatter_initialization_defaults():
    """Test formatter initialization with default parameters."""
    formatter = OtelStyleJsonFormatter()

    assert formatter.default_attributes == {}
    assert hasattr(formatter.context, "get")  # Check it's a Context-like object
    assert formatter.service_name == LoggingDefaults.DEFAULT_SERVICE_NAME.value
    assert formatter.service_version == LoggingDefaults.DEFAULT_SERVICE_VERSION.value
    assert formatter.schema_url == LoggingDefaults.DEFAULT_SCHEMA_URL.value
    assert formatter.add_spark_prefix is True


def test_formatter_initialization_custom_params():
    """Test formatter initialization with custom parameters."""
    context = Context()
    formatter = OtelStyleJsonFormatter(
        default_attributes={"custom": "value"},
        context=context,
        service_name="custom-service",
        service_version="2.0.0",
        schema_url="https://custom.schema.url",
        add_spark_prefix=False,
    )

    assert formatter.default_attributes == {"custom": "value"}
    assert formatter.context is context
    assert formatter.service_name == "custom-service"
    assert formatter.service_version == "2.0.0"
    assert formatter.schema_url == "https://custom.schema.url"
    assert formatter.add_spark_prefix is False


def test_format_basic_record(formatter, sample_record):
    """Test formatting a basic log record."""
    result = formatter.format(sample_record)

    # Parse the JSON part (after the Spark prefix if present)
    if formatter.add_spark_prefix:
        json_part = result.split(": ", 1)[1]
    else:
        json_part = result

    log_data = json.loads(json_part)

    # Check basic structure
    assert "timestamp" in log_data
    assert "observed_timestamp" in log_data
    assert "severity_text" in log_data
    assert "severity_number" in log_data
    assert "body" in log_data
    assert "attributes" in log_data
    assert "resource" in log_data
    assert "instrumentation_scope" in log_data

    # Check values
    assert log_data["severity_text"] == "INFO"
    assert log_data["severity_number"] == OTEL_LEVEL_MAP[logging.INFO]
    assert log_data["body"] == "Test message"
    # code.function may not be present if funcName is not set
    assert log_data["attributes"]["code.filepath"] == "/path/to/test.py"
    assert log_data["attributes"]["code.lineno"] == 42


def test_format_with_spark_prefix(formatter_with_spark_prefix, sample_record):
    """Test formatting with Spark prefix enabled."""
    result = formatter_with_spark_prefix.format(sample_record)

    # Should have Spark prefix
    assert ": " in result
    parts = result.split(": ", 1)
    assert len(parts) == 2

    # Parse JSON part
    json_part = parts[1]
    log_data = json.loads(json_part)

    # Check that it's valid JSON
    assert log_data["severity_text"] == "INFO"


def test_format_without_spark_prefix(formatter_without_spark_prefix, sample_record):
    """Test formatting without Spark prefix."""
    result = formatter_without_spark_prefix.format(sample_record)

    # Should not have Spark prefix
    assert not result.startswith("10/09/25")

    # Should be pure JSON
    log_data = json.loads(result)
    assert log_data["severity_text"] == "INFO"


def test_format_with_context_data(formatter, sample_record, context):
    """Test formatting with Context data."""
    # Set up context data
    context.set("opel/trace_id", "1234567890abcdef")
    context.set("opel/span_id", "abcdef1234567890")
    context.set("opel/trace_flags", 1)
    context.set(
        "opel/resource",
        {"deployment.environment": "test", "service.instance.id": "test-instance"},
    )
    context.set("opel/instrumentation_attributes", {"custom.team": "data-engineering"})

    result = formatter.format(sample_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Check trace data
    assert log_data["trace_id"] == "1234567890abcdef"
    assert log_data["span_id"] == "abcdef1234567890"
    assert log_data["trace_flags"] == 1

    # Check resource attributes
    resource_attrs = log_data["resource"]["attributes"]
    assert resource_attrs["deployment.environment"] == "test"
    assert resource_attrs["service.instance.id"] == "test-instance"

    # Check instrumentation attributes
    inst_attrs = log_data["instrumentation_scope"]["attributes"]
    assert inst_attrs["custom.team"] == "data-engineering"


def test_format_with_exception(formatter, error_record):
    """Test formatting a record with exception info."""
    result = formatter.format(error_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Check exception attributes
    assert "exception.type" in log_data["attributes"]
    assert "exception.message" in log_data["attributes"]
    assert "exception.stacktrace" in log_data["attributes"]

    assert log_data["attributes"]["exception.type"] == "ValueError"
    assert "Test error" in log_data["attributes"]["exception.message"]


def test_format_with_extra_attributes(formatter, sample_record):
    """Test formatting with extra attributes."""
    sample_record.extra_attributes = {
        "custom_field": "custom_value",
        "numeric_field": 42,
        "boolean_field": True,
    }

    result = formatter.format(sample_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Check extra attributes
    assert log_data["attributes"]["custom_field"] == "custom_value"
    assert log_data["attributes"]["numeric_field"] == 42
    assert log_data["attributes"]["boolean_field"] is True


def test_format_with_default_attributes(formatter, sample_record):
    """Test formatting with default attributes."""
    formatter.default_attributes = {
        "default_field": "default_value",
        "environment": "test",
    }

    result = formatter.format(sample_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Check default attributes
    assert log_data["attributes"]["default_field"] == "default_value"
    assert log_data["attributes"]["environment"] == "test"


def test_format_all_log_levels(formatter):
    """Test formatting with all log levels."""
    levels = [
        (logging.DEBUG, "DEBUG", 5),
        (logging.INFO, "INFO", 9),
        (logging.WARNING, "WARNING", 13),
        (logging.ERROR, "ERROR", 17),
        (logging.CRITICAL, "CRITICAL", 21),
    ]

    for level, level_name, expected_number in levels:
        record = logging.LogRecord(
            name="test.logger",
            level=level,
            pathname="/path/to/test.py",
            lineno=42,
            msg=f"Test {level_name} message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Parse JSON part
        json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
        log_data = json.loads(json_part)

        assert log_data["severity_text"] == level_name
        assert log_data["severity_number"] == expected_number


def test_format_with_nested_context_namespaces(formatter, sample_record, context):
    """Test formatting with nested context namespaces."""
    # Set up nested context data
    context.set("opel/resource/service", {"name": "nested-service", "version": "2.0.0"})
    context.set(
        "opel/resource/infrastructure", {"region": "us-east-1", "zone": "us-east-1a"}
    )

    result = formatter.format(sample_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Check nested resource attributes
    resource_attrs = log_data["resource"]["attributes"]
    assert "service.name" in resource_attrs
    assert "service.version" in resource_attrs


def test_format_with_missing_context_data(formatter, sample_record):
    """Test formatting when context has no Opel data."""
    result = formatter.format(sample_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Check that trace data is null when not in context
    assert log_data["trace_id"] is None
    assert log_data["span_id"] is None
    assert log_data["trace_flags"] == 1  # Default value


def test_format_with_custom_service_info(formatter, sample_record):
    """Test formatting with custom service information."""
    formatter.service_name = "custom-service"
    formatter.service_version = "3.0.0"
    formatter.schema_url = "https://custom.schema.url"

    result = formatter.format(sample_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Check service information
    resource_attrs = log_data["resource"]["attributes"]
    assert resource_attrs["service.name"] == "custom-service"
    assert resource_attrs["service.version"] == "3.0.0"

    inst_scope = log_data["instrumentation_scope"]
    assert inst_scope["name"] == "custom-service"
    assert inst_scope["version"] == "3.0.0"
    assert inst_scope["schema_url"] == "https://custom.schema.url"


def test_format_json_serialization(formatter, sample_record):
    """Test that the formatter produces valid JSON."""
    result = formatter.format(sample_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result

    # Should be valid JSON
    log_data = json.loads(json_part)
    assert isinstance(log_data, dict)

    # Should be able to serialize back to JSON
    json.dumps(log_data)


def test_format_with_unicode_characters(formatter, sample_record):
    """Test formatting with Unicode characters."""
    sample_record.msg = "Test message with émojis 🚀 and ñ characters"

    result = formatter.format(sample_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Check Unicode handling
    assert log_data["body"] == "Test message with émojis 🚀 and ñ characters"


def test_format_with_none_context(formatter, sample_record):
    """Test formatting when context is None."""
    formatter.context = None

    result = formatter.format(sample_record)

    # Should not raise an exception
    assert isinstance(result, str)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Should have default values
    assert log_data["trace_id"] is None
    assert log_data["span_id"] is None


def test_format_with_empty_context(formatter, sample_record, context):
    """Test formatting with empty context."""
    # Context is already empty from fixture

    result = formatter.format(sample_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Should have default values
    assert log_data["trace_id"] is None
    assert log_data["span_id"] is None
    assert log_data["trace_flags"] == 1


def test_format_with_complex_extra_attributes(formatter, sample_record):
    """Test formatting with complex extra attributes."""
    sample_record.extra_attributes = {
        "simple_string": "value",
        "nested_dict": {"key1": "value1", "key2": 42},
        "list_value": [1, 2, 3, "string"],
        "boolean_value": True,
        "null_value": None,
    }

    result = formatter.format(sample_record)

    # Parse JSON part
    json_part = result.split(": ", 1)[1] if formatter.add_spark_prefix else result
    log_data = json.loads(json_part)

    # Check complex attributes
    attrs = log_data["attributes"]
    assert attrs["simple_string"] == "value"
    assert attrs["nested_dict"]["key1"] == "value1"
    assert attrs["nested_dict"]["key2"] == 42
    assert attrs["list_value"] == [1, 2, 3, "string"]
    assert attrs["boolean_value"] is True
    assert attrs["null_value"] is None


def test_otel_level_mapping():
    """Test that OTEL level mapping is correct."""
    expected_mapping = {
        logging.DEBUG: 5,
        logging.INFO: 9,
        logging.WARNING: 13,
        logging.ERROR: 17,
        logging.CRITICAL: 21,
    }

    for python_level, expected_otel_level in expected_mapping.items():
        assert OTEL_LEVEL_MAP[python_level] == expected_otel_level


def test_log_record_flags():
    """Test that LOG_RECORD_FLAGS is properly defined."""
    assert isinstance(LOG_RECORD_FLAGS, dict)
    assert "TRACE_FLAGS_DEFAULT" in LOG_RECORD_FLAGS
    assert LOG_RECORD_FLAGS["TRACE_FLAGS_DEFAULT"] == 1
