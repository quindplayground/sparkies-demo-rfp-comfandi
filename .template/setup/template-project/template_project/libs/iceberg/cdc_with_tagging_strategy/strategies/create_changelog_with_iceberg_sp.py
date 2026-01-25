import functools

from pyspark.sql import DataFrame
from pyspark.sql import functions as sf

from template_project.libs.exceptions import ColumnsNotMatchedError
from template_project.libs.iceberg.cdc_with_tagging_strategy.exceptions import (
    ChangelogManagerException,
)
from template_project.libs.iceberg.cdc_with_tagging_strategy.strategies.base import (
    IChangelogStrategy,
)


class CreateChangelogWithIcebergSP(IChangelogStrategy):
    """Strategy for creating changelog with Iceberg stored procedures."""

    def _build_opts(
        self, last_snapshot: int | None, current_snapshot: int | None
    ) -> str:
        """Build changelog options.

        Args:
            last_snapshot: Last snapshot ID.
            current_snapshot: Current snapshot ID.

        Returns:
            Changelog options string.
        """
        start_ts_ms = self.snapshot_manager.get_comitted_at_timestamp(
            last_snapshot, "ms"
        )
        end_ts_ms = self.snapshot_manager.get_comitted_at_timestamp(
            current_snapshot, "ms"
        )

        self.logger.info(
            "Building changelog options",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "catalog": self.catalog,
                    "start_ts_ms": start_ts_ms,
                    "end_ts_ms": end_ts_ms,
                    "operation": "BUILD_OPTS",
                    "state": "IN_PROGRESS",
                }
            },
        )

        if start_ts_ms is None:
            self.logger.info(
                "No start timestamp provided, returning empty options",
                extra={
                    "attributes": {
                        "source_table": self.table_id,
                        "catalog": self.catalog,
                        "operation": "BUILD_OPTS",
                        "state": "SUCCESS",
                        "start_ts_ms": start_ts_ms,
                        "end_ts_ms": end_ts_ms,
                    }
                },
            )
            return ""

        if end_ts_ms is None:
            self.logger.info(
                "No end timestamp provided, no end-timestamp will be set",
                extra={
                    "attributes": {
                        "source_table": self.table_id,
                        "catalog": self.catalog,
                        "operation": "BUILD_OPTS",
                        "state": "SUCCESS",
                        "start_ts_ms": start_ts_ms,
                        "end_ts_ms": end_ts_ms,
                    }
                },
            )
            return f"'start-timestamp', '{start_ts_ms}'"

        if start_ts_ms >= end_ts_ms:
            self.logger.warning(
                "Start timestamp is greater than or equal to end timestamp",
                extra={
                    "attributes": {
                        "source_table": self.table_id,
                        "catalog": self.catalog,
                        "start_ts_ms": start_ts_ms,
                        "end_ts_ms": end_ts_ms,
                        "operation": "BUILD_OPTS",
                        "state": "IN_PROGRESS",
                    }
                },
            )

        opts_str = f"'start-timestamp', '{start_ts_ms}', 'end-timestamp', '{end_ts_ms}'"

        self.logger.info(
            "Built options string",
            extra={
                "attributes": {
                    "source_table": self.table_id,
                    "catalog": self.catalog,
                    "opts_str": opts_str,
                    "operation": "BUILD_OPTS",
                    "state": "SUCCESS",
                }
            },
        )

        return opts_str

    def _create_changelog_table(self, opts_str: str) -> DataFrame:
        """Create the changelog view.

        Args:
            opts_str: Changelog options string.

        Returns:
            Changelog view DataFrame.

        Raises:
            ChangelogManagerException: If view creation fails.
        """
        cdc_view = "cdc_" + self.table_id.split(".")[-1]
        options_clause = f", options => map({opts_str})" if opts_str else ""

        self.logger.info(
            "Creating changelog view",
            extra={
                "attributes": {
                    "source_table": self.table_id,
                    "catalog": self.catalog,
                    "operation": "CREATE_CHANGELOG_VIEW",
                    "state": "IN_PROGRESS",
                }
            },
        )

        query = f"""
            CALL {self.catalog}.system.create_changelog_view(
                table => '{self.table_id}',
                changelog_view => '{cdc_view}'
                {options_clause},
                net_changes => true
            )
        """

        self.logger.info(
            "Create changelog view query:" + query,
            extra={
                "attributes": {
                    "source_table": self.table_id,
                    "catalog": self.catalog,
                    "operation": "CREATE_CHANGELOG_VIEW",
                    "state": "IN_PROGRESS",
                    "query": query,
                }
            },
        )

        try:
            self.spark.sql(query)
        except Exception as e:
            self.logger.error(
                "Failed to create changelog view",
                extra={
                    "attributes": {
                        "source_table": self.table_id,
                        "catalog": self.catalog,
                        "operation": "CREATE_CHANGELOG_VIEW",
                        "state": "ERROR",
                        "query": query,
                    }
                },
                exc_info=e,
            )
            raise ChangelogManagerException(f"Failed to create changelog view: {e}")

        self.logger.info(
            "Successfully created changelog view",
            extra={
                "attributes": {
                    "source_table": self.table_id,
                    "catalog": self.catalog,
                    "operation": "CREATE_CHANGELOG_VIEW",
                    "state": "SUCCESS",
                    "cdc_view": cdc_view,
                }
            },
        )
        return self.spark.table(cdc_view)

    def _get_gold_records(
        self, changelog_dataframe: DataFrame, exclude_cols: list[str] | None = None
    ) -> DataFrame:
        """Get gold records from changelog.

        Args:
            changelog_dataframe: Changelog DataFrame.
            exclude_cols: Columns to exclude.

        Returns:
            DataFrame with gold records.

        Raises:
            ColumnsNotMatchedError: If required columns are missing.
        """
        self.logger.info(
            "Getting gold records",
            extra={
                "attributes": {"operation": "GET_GOLD_RECORDS", "state": "IN_PROGRESS"}
            },
        )

        if exclude_cols is None:
            exclude_cols = []

        metadata_cols = ["_change_type", "_change_ordinal", "_commit_snapshot_id"]

        required_cols = set(metadata_cols)
        available_cols = set(changelog_dataframe.columns)

        if not required_cols.issubset(available_cols):
            self.logger.error(
                "Expected columns are not in the changelog_df columns",
                extra={
                    "attributes": {
                        "operation": "GET_GOLD_RECORDS",
                        "state": "ERROR",
                        "required_cols": required_cols,
                        "available_cols": available_cols,
                    }
                },
            )
            raise ColumnsNotMatchedError(required_cols, available_cols)

        data_cols = [
            c
            for c in changelog_dataframe.columns
            if c not in metadata_cols + exclude_cols
        ]

        deletes = changelog_dataframe.filter(sf.col("_change_type") == "DELETE").alias(
            "d"
        )
        inserts = changelog_dataframe.filter(sf.col("_change_type") == "INSERT").alias(
            "i"
        )

        equal_conds = [deletes[c].eqNullSafe(inserts[c]) for c in data_cols]
        equal_join_expr = functools.reduce(lambda a, b: a & b, equal_conds)

        equal_pairs = (
            deletes.join(inserts, on=equal_join_expr, how="inner")
            .select(*[sf.col(f"d.{c}").alias(c) for c in data_cols])
            .distinct()
        )

        equal_drops = equal_pairs.withColumn("to_drop", sf.lit(True)).alias("e")
        changelog = changelog_dataframe.alias("c")

        marked_conds = [
            sf.col(f"c.{c}").eqNullSafe(sf.col(f"e.{c}")) for c in data_cols
        ]
        marked_join_expr = functools.reduce(lambda a, b: a & b, marked_conds)

        df_marked = changelog.join(equal_drops, on=marked_join_expr, how="left").select(
            "c.*", "e.to_drop"
        )

        gold = df_marked.filter(
            (sf.col("_change_type") == "INSERT") & sf.col("to_drop").isNull()
        ).drop(*metadata_cols, "to_drop")

        self.logger.info(
            "Successfully got gold records",
            extra={"attributes": {"operation": "GET_GOLD_RECORDS", "state": "SUCCESS"}},
        )

        return gold

    def create_changelog(
        self, *args, exclude_cols: list[str] | None = None, **kwargs
    ) -> DataFrame:
        """Create the changelog with Iceberg stored procedures.

        Args:
            exclude_cols: Columns to exclude.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            DataFrame with the changelog.
        """
        self.logger.info(
            "Starting create_changelog with Iceberg SP strategy",
            extra={
                "attributes": {
                    "source_table": self.table_id,
                    "tag_name": self.tag_name,
                    "catalog": self.catalog,
                    "operation": "CREATE_CHANGELOG",
                    "state": "IN_PROGRESS",
                }
            },
        )

        last_snapshot = self.snapshot_manager.get_last_snapshot_id(self.tag_name)

        if last_snapshot is None:
            self.logger.info(
                "First execution detected for table. Reading complete table without CDC view.",
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

        current_snapshot = self.snapshot_manager.get_current_snapshot_id()

        has_changed = self.snapshot_manager.has_changed(self.tag_name)

        if not has_changed:
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

        opts_pair = self._build_opts(last_snapshot, current_snapshot)
        changelog_tbl = self._create_changelog_table(opts_pair)
        gold_records = self._get_gold_records(changelog_tbl, exclude_cols)

        return gold_records
