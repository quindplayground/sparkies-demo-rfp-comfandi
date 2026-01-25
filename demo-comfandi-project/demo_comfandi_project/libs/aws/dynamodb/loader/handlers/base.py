"""Base handler for DynamoDB operations."""

from abc import ABC, abstractmethod
from typing import Callable, Iterable, Any
import time
import uuid

from boto3.dynamodb.table import BatchWriter
from pyspark.sql import Row

from demo_comfandi_project.libs.aws.dynamodb.loader.utils import (
    is_retryable_error,
    get_table,
)
from demo_comfandi_project.libs.logging.logger import get_logger


class DynamoDBOperationHandler(ABC):
    """Abstract base handler for DynamoDB operations."""

    def __init__(
        self,
        job_id: str,
        region: str,
        table_name: str,
        item_size_limit: int,
        max_retries: int = 5,
        base_wait: float = 5.0,
    ):
        self.logger = get_logger(__name__, capture_spark_logs=False)
        self.job_id = job_id
        self.region = region
        self.table_name = table_name
        self.item_size_limit = item_size_limit
        self.max_retries = max_retries
        self.base_wait = base_wait

    def _get_table(self):
        """Get the DynamoDB table.

        Returns:
            DynamoDB table resource.
        """
        return get_table(self.region, self.table_name)

    @staticmethod
    def _get_item_keys(item: dict[str, Any]) -> dict[str, Any]:
        """Extract item keys for logging.

        Args:
            item: Item from which to extract keys.

        Returns:
            Dictionary containing the item's partition and sort keys.
        """
        return {
            k: v
            for k, v in item.items()
            if k in ["pk", "sk", "gsi1_pk", "gsi1_sk", "gsi2_pk", "gsi2_sk"]
        }

    @abstractmethod
    def process_item(self, bw: BatchWriter, item: dict[str, Any]) -> bool:
        """Process an individual item.

        Args:
            bw: DynamoDB batch writer.
            item: Item to process.

        Returns:
            True if processing was successful, False otherwise.
        """
        pass

    def _process_partition(self, rows: Iterable[Row]) -> None:
        """Process a partition of Spark rows.

        Args:
            rows: Iterable of Spark rows to process.
        """
        if not rows:
            return

        table = self._get_table()
        count = 0
        count_error = 0
        attempt = 0
        partition_id = uuid.uuid4().hex

        while attempt <= self.max_retries:
            try:
                with table.batch_writer() as bw:
                    for row in rows:
                        item = row.asDict()

                        success = self.process_item(bw, item)
                        if success:
                            count += 1
                        else:
                            count_error += 1

                self.logger.info(
                    "Successfully processed items",
                    extra={
                        "attributes": {
                            "job_id": self.job_id,
                            "partition_id": partition_id,
                            "operation": "PROCESSING_PARTITION",
                            "status": "SUCCESS",
                            "count": count,
                            "count_error": count_error,
                            "attempt": attempt,
                        }
                    },
                )

                break

            except Exception as e:
                if is_retryable_error(e):
                    wait_time = self.base_wait * (2**attempt)
                    self.logger.warning(
                        "ThrottlingException in batch_writer context, retrying partition",
                        extra={
                            "attributes": {
                                "job_id": self.job_id,
                                "partition_id": partition_id,
                                "operation": "PROCESSING_PARTITION",
                                "status": "RETRYING",
                                "wait_time": wait_time,
                                "attempt": attempt + 1,
                                "max_retries": self.max_retries,
                            }
                        },
                        exc_info=e,
                    )
                    time.sleep(wait_time)
                    attempt += 1
                else:
                    self.logger.error(
                        "Uncontrolled exception in batch_writer context",
                        extra={
                            "attributes": {
                                "job_id": self.job_id,
                                "partition_id": partition_id,
                                "operation": "PROCESSING_PARTITION",
                                "status": "ERROR",
                                "attempt": attempt,
                                "max_retries": self.max_retries,
                            }
                        },
                        exc_info=e,
                    )
                    raise e

    def create_partition_handler(self) -> Callable[[Iterable[Row]], None]:
        """Create a handler for processing partitions.

        Returns:
            Function to process partitions.
        """
        return self._process_partition
