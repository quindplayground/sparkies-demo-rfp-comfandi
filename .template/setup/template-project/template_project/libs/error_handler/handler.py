"""Main error handler module."""

from pyspark.sql import SparkSession, DataFrame

from template_project.libs.error_handler.models import ErrorData
from template_project.libs.error_handler.writers.base import ErrorWriterInterface
from template_project.libs.error_handler.extractors import RowDataExtractorInterface
from template_project.libs.logging.logger import get_logger

from template_project.libs.error_handler.writers import MAP_WRITERS
from template_project.libs.error_handler.extractors import MAP_EXTRACTORS


class ErrorHandler:
    """Handle error processing and logging using a writer and extractor."""

    def __init__(
        self,
        error_writer: ErrorWriterInterface,
        row_data_extractor: RowDataExtractorInterface,
    ):
        """Initialize the ErrorHandler.

        Args:
            error_writer: The writer used to log error data.
            row_data_extractor: The extractor used to retrieve relevant row data.
        """
        self.logger = get_logger(__name__)
        self.error_writer = error_writer
        self.row_data_extractor = row_data_extractor

    def handle_error(
        self,
        spark: SparkSession,
        error: Exception,
        source: str | DataFrame | None = None,
        step: str | None = None,
    ) -> None:
        """Handle an exception by extracting row data and writing error information.

        Args:
            spark: The active Spark session.
            error: The exception that occurred.
            source: Identifier of the error source.
            step: Step in the process where the error occurred.
        """

        row_data = self.row_data_extractor.extract_row_data(spark, source)
        error_data = ErrorData(source=source, step=step, error=error, row_data=row_data)
        self.error_writer.write_error(error_data)
        self.logger.error(
            "Error in stage",
            extra={"attributes": {"step": step, "source": source, "state": "ERROR"}},
            exc_info=error,
        )


def get_error_handler(
    spark: SparkSession,
    error_path: str,
    extractor: str = "changelog",
    writer: str = "spark_csv",
) -> ErrorHandler:
    """Create an ErrorHandler with specified components.

    Args:
        spark: The active Spark session.
        error_path: Path where error logs should be written.
        extractor: Key for the row data extractor. Defaults to 'changelog'.
        writer: Key for the error writer. Defaults to 'spark_csv'.

    Returns:
        An ErrorHandler instance configured with the specified writer and extractor.
    """
    writer_instance = MAP_WRITERS[writer](spark=spark, error_path=error_path)
    extractor_instance = MAP_EXTRACTORS[extractor]()

    return ErrorHandler(writer_instance, extractor_instance)
