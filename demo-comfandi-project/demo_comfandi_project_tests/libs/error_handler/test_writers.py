from unittest.mock import patch
from pyspark.sql import SparkSession

from demo_comfandi_project.libs.error_handler.writers.base import ErrorWriterInterface
from demo_comfandi_project.libs.error_handler.writers.spark_csv import (
    SparkCsvErrorWriter,
)


def test_error_writer_interface():
    class DummyWriter(ErrorWriterInterface):
        def write_error(self, error_data):
            pass  # Implementación dummy para testing de la interfaz

    writer = DummyWriter()
    assert hasattr(writer, "write_error")


def test_spark_csv_writer_writes_dataframe(spark: SparkSession, tmp_path):
    df = spark.createDataFrame([(1, "a")], ["id", "val"])  # type: ignore
    with patch("os.path.exists") as mock_exists, patch("os.makedirs") as mock_makedirs:
        mock_exists.return_value = False
        writer = SparkCsvErrorWriter(spark, str(tmp_path))
        # Crear ErrorData real con timestamp válido
        from demo_comfandi_project.libs.error_handler.models import ErrorData

        error_data = ErrorData(
            source=df, step="test", error=Exception("test"), row_data="{}"
        )
        writer.write_error(error_data)
        # El writer no llama makedirs directamente, solo escribe con Spark
        mock_makedirs.assert_not_called()


def test_spark_csv_writer_handles_string_error(spark: SparkSession, tmp_path):
    with patch("os.path.exists") as mock_exists, patch("os.makedirs") as mock_makedirs:
        mock_exists.return_value = True
        writer = SparkCsvErrorWriter(spark, str(tmp_path))
        # Crear ErrorData real con timestamp válido
        from demo_comfandi_project.libs.error_handler.models import ErrorData

        error_data = ErrorData(
            source="error text", step="test", error=Exception("test"), row_data="{}"
        )
        writer.write_error(error_data)
        # No excepción: se serializa string en DF temporal y se escribe
        mock_makedirs.assert_not_called()
