import re

from pyspark.sql import DataFrame, SparkSession

from template_project.libs.iceberg.cdc_with_tagging_strategy.exceptions import (
    InvalidTableFormatError,
    CommitChangesError,
)
from template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager import (
    SnapshotManager,
)
from template_project.libs.iceberg.cdc_with_tagging_strategy.strategies.factory import (
    StrategyFactory,
)
from template_project.libs.logging import get_logger


class ChangelogManager:
    def __init__(
        self,
        spark: SparkSession,
        table_id: str,
        tag_name: str,
        snapshot_manager: SnapshotManager | None = None,
        strategy_factory: StrategyFactory | None = None,
    ):
        self.spark = spark
        self.table_id = self._validate_table_id_format(table_id)
        self.catalog = self._extract_catalog_from_table_id(table_id)
        self.tag_name = tag_name
        self.snapshot_manager = snapshot_manager or SnapshotManager(spark, table_id)
        self.strategy_factory = strategy_factory or StrategyFactory()
        self.logger = get_logger(self.__class__.__name__)

    @staticmethod
    def _validate_table_id_format(table_id: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+\.([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)$", table_id):
            raise InvalidTableFormatError(
                f"Invalid table id: {table_id}, it must be a valid iceberg "
                "table id with format <catalog>.<schema>.<table>"
            )
        return table_id

    @staticmethod
    def _extract_catalog_from_table_id(table_id: str) -> str:
        return table_id.split(".")[0]

    def get_changelog_table(
        self, *strategy_args, changelog_strategy: str = "iceberg_sp", **strategy_kwargs
    ) -> DataFrame:
        self.logger.info(
            "Starting get_changelog_table with strategy",
            extra={
                "attributes": {
                    "source_table": self.table_id,
                    "tag_name": self.tag_name,
                    "catalog": self.catalog,
                    "strategy": changelog_strategy,
                    "operation": "GET_CHANGELOG_TABLE",
                    "state": "IN_PROGRESS",
                }
            },
        )

        strategy_class = self.strategy_factory[changelog_strategy](
            spark=self.spark,
            snapshot_manager=self.snapshot_manager,
            table_id=self.table_id,
            catalog=self.catalog,
            tag_name=self.tag_name,
        )

        return strategy_class.create_changelog(*strategy_args, **strategy_kwargs)

    def commit_changes(self) -> None:
        self.logger.info(
            "Starting commit changes",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": self.tag_name,
                    "operation": "COMMIT_CHANGES",
                    "state": "IN_PROGRESS",
                }
            },
        )

        commit_result = self.snapshot_manager.set_last_snapshot_tag(self.tag_name)

        if not commit_result:
            self.logger.warning(
                "Failed to set last snapshot ID tag, the changes will not be committed",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "tag_name": self.tag_name,
                        "operation": "COMMIT_CHANGES",
                        "state": "DONE",
                    }
                },
            )
            raise CommitChangesError(
                f"Failed to set last snapshot ID tag: {commit_result}"
            )

        self.logger.info(
            "Finished committing changes",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": self.tag_name,
                    "commit_result": commit_result,
                    "operation": "COMMIT_CHANGES",
                    "state": "DONE",
                }
            },
        )
