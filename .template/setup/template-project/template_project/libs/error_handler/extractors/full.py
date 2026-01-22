"""Full error data extractor."""

import json
import re
from pyspark.sql import DataFrame, SparkSession
from template_project.libs.error_handler.extractors.base import (
    RowDataExtractorInterface,
)
from template_project.libs.logging import get_logger


class SparkFullExtractor(RowDataExtractorInterface):
    """Extractor for retrieving row data from a full DataFrame."""

    def __init__(self):
        """Initialize the SparkFullExtractor."""
        self.logger = get_logger(__name__)

    def extract_row_data(
        self, spark: SparkSession | None = None, source: str | DataFrame | None = None
    ) -> str:
        """Extract row data from a full table.

        Args:
            spark: The Spark session to use for data extraction.
            source: The source of the data to extract.

        Returns:
            A JSON string containing the full table metadata.
        """
        if spark is None or source is None:
            self.logger.warning(
                "Returning empty JSON string",
                extra={
                    "attributes": {
                        "state": "SKIPPED",
                        "reason": "SparkFullExtractor requires both spark and source to be provided",
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
                "Error extracting row data from full table",
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
            JSON string representation of the metadata.

        Raises:
            ValueError: If the source string format is invalid.
        """
        if re.match(r"^([a-zA-Z0-9_]+\.)?[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$", source):
            df = spark.sql(f"DESCRIBE FORMATTED {source}")
        else:
            raise ValueError(
                f"Invalid source string: {source}, must be in the format of 'database.schema.table'"
            )

        return self._get_full_tbl_metadata(df)

    def _handle_source_df(self, source: DataFrame) -> str:
        """Handle a source DataFrame.

        Args:
            source: The DataFrame source to process.

        Returns:
            JSON string representation of the metadata.
        """
        if source.isEmpty():
            self.logger.warning(
                "Source DataFrame is empty",
                extra={
                    "attributes": {
                        "source": source,
                        "state": "SKIPPED",
                        "reason": "DataFrame is empty",
                    }
                },
            )
            return "{}"

        return self._get_full_tbl_metadata(source)

    @staticmethod
    def _get_full_tbl_metadata(df: DataFrame) -> str:
        """Extract full table metadata from a DataFrame.

        Args:
            df: DataFrame containing table description information.

        Returns:
            JSON string containing structured table metadata.
        """
        desc_rows = df.select("col_name", "data_type", "comment").collect()

        columns = []
        metadata_cols = []
        detailed = {}

        section = "columns"
        for row in desc_rows:
            name = (row["col_name"] or "").strip()
            dtype = row["data_type"]
            comment = row["comment"] if row["comment"] is not None else ""

            if name == "# Metadata Columns":
                section = "metadata"
                continue
            if name == "# Detailed Table Information":
                section = "detailed"
                continue

            if not name:
                continue

            if section == "columns":
                columns.append({"name": name, "type": dtype, "comment": comment})

            elif section == "metadata":
                metadata_cols.append({"name": name, "type": dtype, "comment": comment})

            else:
                key = re.sub(r"[\s\-]+", "_", name.lower())

                if key == "table_properties":
                    props_list = dtype.strip("[]").split(",")
                    props_dict = {}
                    for p in props_list:
                        k, v = p.strip().split("=", 1)
                        props_dict[k] = v
                    detailed[key] = props_dict
                else:
                    detailed[key] = dtype

        result = {"cols": columns, "metadata_cols": metadata_cols, "detailed": detailed}

        return json.dumps(result, ensure_ascii=False)
