from logging import LogRecord
import importlib.util
from pathlib import Path

# Cargar el módulo de filtro directamente por ruta para evitar ejecutar __init__.py del paquete
_filter_path = (
    Path(__file__).parents[3]
    / "demo_comfandi_project"
    / "demo_comfandi_project"
    / "libs"
    / "logging"
    / "filter.py"
)
# La ruta correcta es demo-comfandi-project/demo_comfandi_project/libs/logging/filter.py
_filter_path = (
    Path(__file__).parents[3] / "demo_comfandi_project" / "libs" / "logging" / "filter.py"
)
spec = importlib.util.spec_from_file_location("ppd_logging_filter", str(_filter_path))
ppd_logging_filter = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
assert spec is not None and spec.loader is not None
spec.loader.exec_module(ppd_logging_filter)  # type: ignore[assignment]
NoRecursiveFilter = ppd_logging_filter.NoRecursiveFilter


def test_filter_rejects_log4j_proxy_handler():
    """Test that the filter rejects records with Log4JProxyHandler in the name."""
    test_filter = NoRecursiveFilter()
    record = LogRecord(
        name="test.Log4JProxyHandler.something",
        level=20,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    assert not test_filter.filter(record)


def test_filter_accepts_normal_records():
    """Test that the filter accepts normal records."""
    test_filter = NoRecursiveFilter()
    record = LogRecord(
        name="test.normal.logger",
        level=20,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    assert test_filter.filter(record)


def test_filter_rejects_none_record():
    """Test that the filter rejects None records."""
    test_filter = NoRecursiveFilter()
    assert not test_filter.filter(None)


def test_filter_rejects_invalid_record_type():
    """Test that the filter rejects records of invalid type."""
    test_filter = NoRecursiveFilter()
    invalid_records = ["not a record", 123, {}, []]
    for record in invalid_records:
        assert not test_filter.filter(record)


def test_filter_rejects_long_name():
    """Test that the filter rejects records with very long names."""
    test_filter = NoRecursiveFilter()
    record = LogRecord(
        name="x" * 2000,
        level=20,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    assert not test_filter.filter(record)


def test_filter_rejects_invalid_name_type():
    """Test that the filter rejects records with invalid name types."""
    test_filter = NoRecursiveFilter()
    _record = LogRecord(
        name="test.logger",
        level=20,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )

    # Cambiar a un objeto simulado con atributo name inválido sin reasignar tipo directamente
    class _Obj:
        pass

    rec = _Obj()
    rec.name = 123  # type: ignore[attr-defined]
    assert not test_filter.filter(rec)  # type: ignore[arg-type]


def test_filter_rejects_invalid_level_type():
    """Test that the filter rejects records with invalid level types."""
    test_filter = NoRecursiveFilter()

    class _BadRecord:
        def __init__(self):
            self.name = "test.logger"
            self.levelno = "not a number"  # type: ignore[assignment]
            self.msg = "x"

    assert not test_filter.filter(_BadRecord())  # type: ignore[arg-type]


def test_filter_rejects_missing_msg():
    """Test that the filter rejects records without msg attribute."""
    test_filter = NoRecursiveFilter()

    class _BadRecord2:
        def __init__(self):
            self.name = "test.logger"
            self.levelno = 20

    assert not test_filter.filter(_BadRecord2())  # type: ignore[arg-type]


def test_filter_custom_name():
    """Test that the filter works with custom name."""
    test_filter = NoRecursiveFilter(name="custom.filter")
    record = LogRecord(
        name="test.normal.logger",
        level=20,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    assert test_filter.filter(record)
