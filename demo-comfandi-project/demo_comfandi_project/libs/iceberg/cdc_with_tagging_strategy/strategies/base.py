from abc import ABC, abstractmethod

from pyspark.sql import DataFrame, SparkSession

from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager import (
    SnapshotManager,
)
from demo_comfandi_project.libs.logging import get_logger


class IChangelogStrategy(ABC):
    """Base class for changelog creation strategies.

    Attributes:
        spark: Spark session for processing.
        snapshot_manager: Snapshot manager.
        table_id: Table ID.
        catalog: Table catalog.
        tag_name: Tag name to use.
    """

    def __init__(
        self,
        spark: SparkSession,
        snapshot_manager: SnapshotManager,
        table_id: str,
        catalog: str,
        tag_name: str,
    ):
        """Initialize the changelog creation strategy.

        Args:
            spark: Spark session for processing.
            snapshot_manager: Snapshot manager.
            table_id: Table ID.
            catalog: Table catalog.
            tag_name: Tag name to use.
        """
        self.spark = spark
        self.snapshot_manager = snapshot_manager
        self.table_id = table_id
        self.catalog = catalog
        self.tag_name = tag_name
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def create_changelog(self, *args, **kwargs) -> DataFrame:
        """Create the changelog.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            DataFrame with the changelog.
        """
        pass
