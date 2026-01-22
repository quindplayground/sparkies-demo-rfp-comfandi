import pytest
from unittest.mock import Mock, patch
from pyspark.sql import SparkSession

# Inyectar un módulo falso para evitar el ciclo de importación con demo_comfandi_project.libs.logging
import sys
import types

_dummy_logging = types.SimpleNamespace()
_dummy_logging.get_logger = lambda *args, **kwargs: Mock()


class _DummyLogger:
    def __init__(self, *args, **kwargs):
        pass  # Dummy logger para testing - no requiere inicialización

    def log_level(self, *args, **kwargs):
        return self


_dummy_logging.Logger = _DummyLogger
sys.modules.setdefault("demo_comfandi_project.libs.logging", _dummy_logging)


@pytest.fixture(scope="session")
def spark():
    """Fixture global para crear una única instancia de SparkSession para todos los tests."""
    spark = (
        SparkSession.builder.master("local[1]")
        .appName("test")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    yield spark
    spark.stop()


@pytest.fixture(autouse=True)
def mock_logger():
    """Mock del logger para todos los tests."""
    with patch(
        "demo_comfandi_project.libs.runner.executors.multithread.get_logger"
    ) as mock_get_logger, patch(
        "demo_comfandi_project.libs.runner.executors.sequential.get_logger"
    ) as mock_get_logger2:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_get_logger2.return_value = mock_logger
        yield mock_logger
