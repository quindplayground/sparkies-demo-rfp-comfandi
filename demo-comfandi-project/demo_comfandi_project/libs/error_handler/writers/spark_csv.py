"""Spark CSV error writer."""

from pyspark.sql import SparkSession

from demo_comfandi_project.libs.error_handler.writers.base import ErrorWriterInterface
from demo_comfandi_project.libs.error_handler.models import ErrorData
from demo_comfandi_project.libs.logging import get_logger

logger = get_logger(__name__)


class SparkCsvErrorWriter(ErrorWriterInterface):
    """CSV error writer that logs error data using a Spark DataFrame."""

    def __init__(self, spark: SparkSession, error_path: str):
        """Initialize the SparkCsvErrorWriter.

        Args:
            spark: The active Spark session.
            error_path: The destination path for writing error CSV files.
        """
        self.spark = spark
        self.error_path = error_path
        self.error_schema = """
            source: STRING,
            step: STRING,
            row: STRING,
            dt: TIMESTAMP,
            error: STRING
        """

    def write_error(self, error_data: ErrorData) -> None:
        """Write error data to a CSV file using Spark.

        Args:
            error_data: The error data to write.
        """
        error_df = self.spark.createDataFrame(
            [
                (
                    error_data.source,
                    error_data.step,
                    error_data.row_data,
                    error_data.timestamp,
                    error_data.error_message,
                )
            ],
            self.error_schema,
        )

        try:
            error_df.coalesce(1).write.format("csv").mode("append").option(
                "header", True
            ).option("quote", "'").option("escape", "'").save(self.error_path)
        except Exception as e:
            logger.error("Error writing to error log file: %s", str(e))
