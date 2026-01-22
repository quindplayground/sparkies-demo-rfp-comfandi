import re

from pyspark.sql import DataFrame

from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.exceptions import (
    IncrementalExtractException,
)
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.strategies.base import (
    IChangelogStrategy,
)


class CreateChangelogWithDateFilter(IChangelogStrategy):
    """Strategy for creating changelog with date filter."""

    def _validate_date_column(self, date_col: str) -> None:
        """Validate that the date column exists in the table.

        Args:
            date_col: Name of the date column.

        Raises:
            IncrementalExtractException: If the date column is not found.
        """
        if date_col not in self.spark.table(self.table_id).columns:
            raise IncrementalExtractException(
                f"Date column {date_col} not found in table {self.table_id}"
            )

    @staticmethod
    def _build_interval_expression(safety_interval: str | None) -> str:
        """Build the interval expression.

        Args:
            safety_interval: Safety interval string.

        Returns:
            Interval expression.
        """
        if safety_interval and re.match(r"^[0-9]+ [A-Za-z]+$", safety_interval):
            return f"- INTERVAL {safety_interval}"
        else:
            return ""

    def create_changelog(
        self,
        *args,
        date_col: str | None = None,
        safety_interval: str | None = None,
        **kwargs,
    ) -> DataFrame:
        """Create the changelog with date filter.

        Args:
            date_col: Name of the date column.
            safety_interval: Safety interval string.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            DataFrame with the changelog.

        Raises:
            IncrementalExtractException: If date_col is not provided or extraction fails.
        """
        if date_col is None:
            raise IncrementalExtractException(
                "date_col parameter is required for date filter strategy"
            )

        self.logger.info(
            "Starting create_changelog with date filter strategy",
            extra={
                "attributes": {
                    "source_table": self.table_id,
                    "tag_name": self.tag_name,
                    "catalog": self.catalog,
                    "date_col": date_col,
                    "safety_interval": safety_interval,
                    "operation": "CREATE_CHANGELOG",
                    "state": "IN_PROGRESS",
                }
            },
        )

        last_snapshot_id = self.snapshot_manager.get_last_snapshot_id(self.tag_name)

        if last_snapshot_id is None:
            self.logger.info(
                "First execution detected for table. Reading complete table.",
                extra={
                    "attributes": {
                        "source_table": self.table_id,
                        "tag_name": self.tag_name,
                        "catalog": self.catalog,
                        "operation": "CREATE_CHANGELOG",
                        "state": "SUCCESS",
                    }
                },
            )
            return self.spark.table(self.table_id)

        start_date = self.snapshot_manager.get_comitted_at_timestamp(last_snapshot_id)

        if start_date is None:
            self.logger.info(
                "No start date found, reading complete table.",
                extra={
                    "attributes": {
                        "source_table": self.table_id,
                        "tag_name": self.tag_name,
                        "catalog": self.catalog,
                        "operation": "CREATE_CHANGELOG",
                        "state": "SUCCESS",
                    }
                },
            )
            return self.spark.table(self.table_id)

        if not self.snapshot_manager.has_changed(self.tag_name):
            self.logger.info(
                "No changes since last snapshot, returning empty dataframe",
                extra={
                    "attributes": {
                        "source_table": self.table_id,
                        "tag_name": self.tag_name,
                        "catalog": self.catalog,
                        "operation": "CREATE_CHANGELOG",
                        "state": "SUCCESS",
                    }
                },
            )
            return self.spark.createDataFrame(
                [], self.spark.table(self.table_id).schema
            )

        self._validate_date_column(date_col)

        interval_expr = self._build_interval_expression(safety_interval)

        try:
            query = f"""
                SELECT *
                FROM {self.table_id}
                WHERE {date_col} >= (CAST('{start_date}' AS TIMESTAMP) {interval_expr})
            """

            self.logger.info(
                "Executing date filter query",
                extra={
                    "attributes": {
                        "source_table": self.table_id,
                        "tag_name": self.tag_name,
                        "catalog": self.catalog,
                        "query": query,
                        "operation": "CREATE_CHANGELOG",
                        "state": "IN_PROGRESS",
                    }
                },
            )

            data = self.spark.sql(query)

            self.logger.info(
                "Successfully created changelog with date filter",
                extra={
                    "attributes": {
                        "source_table": self.table_id,
                        "tag_name": self.tag_name,
                        "catalog": self.catalog,
                        "operation": "CREATE_CHANGELOG",
                        "state": "SUCCESS",
                    }
                },
            )

            return data

        except Exception as e:
            self.logger.error(
                "Failed to create changelog with date filter",
                extra={
                    "attributes": {
                        "source_table": self.table_id,
                        "tag_name": self.tag_name,
                        "catalog": self.catalog,
                        "operation": "CREATE_CHANGELOG",
                        "state": "ERROR",
                    }
                },
                exc_info=e,
            )
            raise IncrementalExtractException(f"Failed to extract data: {e}")
