"""Base extractor for error data."""

from abc import ABC, abstractmethod
from pyspark.sql import SparkSession, DataFrame


# pylint: disable=too-few-public-methods
class RowDataExtractorInterface(ABC):
    """Abstract base class for extracting row data."""

    @abstractmethod
    def extract_row_data(
        self, spark: SparkSession | None = None, source: str | DataFrame | None = None
    ) -> str:
        """Extract row data and return it as a string.

        Args:
            spark: The Spark session to use for data extraction.
            source: The source of the data to extract.

        Returns:
            A string representation of the extracted row data.
        """
        pass
