"""Error data writers."""

from demo_comfandi_project.libs.error_handler.writers.base import ErrorWriterInterface
from demo_comfandi_project.libs.error_handler.writers.spark_csv import (
    SparkCsvErrorWriter,
)

MAP_WRITERS = {"spark_csv": SparkCsvErrorWriter}

__all__ = ["ErrorWriterInterface", "SparkCsvErrorWriter", "MAP_WRITERS"]
