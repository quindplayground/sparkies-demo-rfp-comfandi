"""Changelog error data extractor."""

import json
import re

from pyspark.sql import DataFrame, SparkSession
from template_project.libs.error_handler.extractors.base import (
    RowDataExtractorInterface,
)
from template_project.libs.logging.logger import get_logger


class SparkChangelogExtractor(RowDataExtractorInterface):
    """Extractor for retrieving row data from a changelog DataFrame."""

    def __init__(self):
        """Initialize the SparkChangelogExtractor."""
        self.logger = get_logger(__name__)

    def extract_row_data(
        self, spark: SparkSession | None = None, source: str | DataFrame | None = None
    ) -> str:
        """Extract row data from a changelog table.

        Args:
            spark: The Spark session to use for data extraction.
            source: The source of the data to extract.

        Returns:
            A JSON string containing up to 10 records from the changelog DataFrame.
            Returns an empty JSON object string if no valid data is found or an exception occurs.
        """
        if spark is None or source is None:
            self.logger.warning(
                "Returning empty JSON string",
                extra={
                    "attributes": {
                        "state": "SKIPPED",
                        "reason": "SparkChangelogExtractor requires both spark and source to be provided",
                    }
                },
            )

            return "{}"

        try:
            if isinstance(source, str):
                result = self._handle_source_str(spark, source)
            else:
                result = self._handle_source_df(source)

            self.logger.info(
                "Returning JSON string",
                extra={
                    "attributes": {
                        "source": source,
                        "state": "SUCCESS",
                        "result": result[:10],
                    }
                },
            )

            return result
        except Exception as e:
            self.logger.error(
                "Error extracting row data from changelog table",
                extra={"attributes": {"source": source, "state": "ERROR"}},
                exc_info=e,
            )

            return "{}"

    def _handle_source_str(self, spark: SparkSession, source: str) -> str:
        """Handle a source string by executing a SQL query.

        Args:
            spark: The Spark session to use.
            source: The source string to execute a SQL query.

        Returns:
            JSON string representation of the data.

        Raises:
            ValueError: If the source string format is invalid.
        """
        if re.match(r"^([a-zA-Z0-9_]+\.)?[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$", source):
            dataframe = spark.table(source).limit(10)
        else:
            raise ValueError(
                f"Invalid source string: {source}, must be in the format of 'database.schema.table'"
            )

        return self._dataframe_to_json_string(dataframe)

    def _handle_source_df(self, source: DataFrame) -> str:
        """Handle a source DataFrame.

        Args:
            source: The DataFrame source to process.

        Returns:
            JSON string representation of the data.
        """
        if source.isEmpty():
            self.logger.warning(
                "Skipping empty DataFrame",
                extra={
                    "attributes": {
                        "source": source,
                        "state": "SKIPPED",
                        "reason": "DataFrame is empty",
                    }
                },
            )
            return "{}"

        return self._dataframe_to_json_string(source)

    @staticmethod
    def _dataframe_to_json_string(df: DataFrame) -> str:
        """Convert a Spark DataFrame to a JSON string.

        Args:
            df: The DataFrame to convert.

        Returns:
            A JSON string representation of up to 10 records from the DataFrame.
            Returns an empty JSON object string if an exception occurs.
        """
        try:
            sample_data = df.toPandas().to_dict("records")
            return json.dumps(sample_data, default=str, ensure_ascii=False)
        except Exception:
            return "{}"
