from typing import Literal

from pyspark.sql import SparkSession

from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.exceptions import (
    SnapshotManagerException,
)
from demo_comfandi_project.libs.logging import get_logger


class SnapshotManager:
    def __init__(self, spark: SparkSession, table_id: str):
        self.spark = spark
        self.table_id = table_id
        self.logger = get_logger(self.__class__.__name__)

        self._table_exists()

    def _table_exists(self) -> None:
        self.logger.info(
            "Checking if table exists",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "operation": "TABLE_EXISTS",
                    "state": "IN_PROGRESS",
                }
            },
        )
        if not self.spark.catalog.tableExists(self.table_id):
            self.logger.warning(
                "Table does not exist",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "operation": "TABLE_EXISTS",
                        "state": "DONE",
                    }
                },
            )
            raise SnapshotManagerException("Table does not exist")

        self.logger.info(
            "Table exists",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "operation": "TABLE_EXISTS",
                    "state": "DONE",
                }
            },
        )

    def get_last_snapshot_id(self, tag_name: str) -> int | None:
        self.logger.info(
            "Getting last snapshot ID",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": tag_name,
                    "operation": "GET_LAST_SNAPSHOT_ID",
                    "state": "IN_PROGRESS",
                }
            },
        )

        try:
            last_snapshot_row = self.spark.sql(
                f"""
                SELECT snapshot_id
                FROM {self.table_id}.refs
                WHERE name = '{tag_name}'
                """
            ).first()
        except Exception as e:
            self.logger.error(
                "Failed to get last snapshot ID",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "tag_name": tag_name,
                        "operation": "GET_LAST_SNAPSHOT_ID",
                        "state": "ERROR",
                    }
                },
                exc_info=e,
            )
            raise SnapshotManagerException(f"Failed to get last snapshot ID: {e}")

        if last_snapshot_row is None:
            self.logger.warning(
                "No last snapshot ID found",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "last_snapshot_id": None,
                        "tag_name": tag_name,
                        "operation": "GET_LAST_SNAPSHOT_ID",
                        "state": "DONE",
                    }
                },
            )
            return None

        self.logger.info(
            "Last snapshot ID",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "last_snapshot_id": last_snapshot_row.snapshot_id,
                    "tag_name": tag_name,
                    "operation": "GET_LAST_SNAPSHOT_ID",
                    "state": "DONE",
                }
            },
        )

        return last_snapshot_row.snapshot_id

    def get_current_snapshot_id(self) -> int | None:
        self.logger.info(
            "Getting current snapshot ID",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "operation": "GET_CURRENT_SNAPSHOT_ID",
                    "state": "IN_PROGRESS",
                }
            },
        )
        try:
            current_snapshot_row = self.spark.sql(
                f"""
                SELECT snapshot_id
                FROM {self.table_id}.snapshots
                ORDER BY committed_at DESC
                LIMIT 1 OFFSET 0
                """
            ).first()
        except Exception as e:
            self.logger.error(
                "Failed to get current snapshot ID",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "operation": "GET_CURRENT_SNAPSHOT_ID",
                        "state": "ERROR",
                    }
                },
                exc_info=e,
            )
            raise SnapshotManagerException(f"Failed to get current snapshot ID: {e}")

        if current_snapshot_row is None:
            self.logger.warning(
                "No current snapshot ID found",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "current_snapshot_id": None,
                        "operation": "GET_CURRENT_SNAPSHOT_ID",
                        "state": "DONE",
                    }
                },
            )
            return None

        self.logger.info(
            "Current snapshot ID",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "current_snapshot_id": current_snapshot_row.snapshot_id,
                    "operation": "GET_CURRENT_SNAPSHOT_ID",
                    "state": "DONE",
                }
            },
        )

        return current_snapshot_row.snapshot_id

    def has_changed(self, tag_name: str) -> bool:
        self.logger.info(
            "Checking if has changed",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": tag_name,
                    "operation": "HAS_CHANGED",
                    "state": "IN_PROGRESS",
                }
            },
        )

        last_snapshot_id = self.get_last_snapshot_id(tag_name)
        current_snapshot_id = self.get_current_snapshot_id()

        if last_snapshot_id is None or current_snapshot_id is None:
            self.logger.info(
                "No last or current snapshot ID found, it has not changed",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "tag_name": tag_name,
                        "last_snapshot_id": last_snapshot_id,
                        "current_snapshot_id": current_snapshot_id,
                        "operation": "HAS_CHANGED",
                        "state": "DONE",
                    }
                },
            )
            return False

        _has_changed = last_snapshot_id != current_snapshot_id

        self.logger.info(
            "Finished checking if has changed",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": tag_name,
                    "last_snapshot_id": last_snapshot_id,
                    "current_snapshot_id": current_snapshot_id,
                    "has_changed": _has_changed,
                    "operation": "HAS_CHANGED",
                    "state": "DONE",
                }
            },
        )

        return _has_changed

    def last_snapshot_tag_exists(self, tag_name: str) -> bool:
        self.logger.info(
            "Checking if the tag exists",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": tag_name,
                    "operation": "LAST_SNAPSHOT_TAG_EXISTS",
                    "state": "IN_PROGRESS",
                }
            },
        )

        last_snapshot_id = self.get_last_snapshot_id(tag_name)

        if last_snapshot_id is None:
            self.logger.info(
                "No last snapshot ID found, the tag does not exist",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "tag_name": tag_name,
                        "last_snapshot_id": last_snapshot_id,
                        "operation": "LAST_SNAPSHOT_TAG_EXISTS",
                        "state": "DONE",
                    }
                },
            )
            return False

        self.logger.info(
            "The tag exists",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": tag_name,
                    "last_snapshot_id": last_snapshot_id,
                    "operation": "LAST_SNAPSHOT_TAG_EXISTS",
                    "state": "DONE",
                }
            },
        )

        return True

    def get_comitted_at_timestamp(
        self, snapshot_id: int, output_format: Literal["str", "ms", "datetime"] = "str"
    ) -> str | None:
        self.logger.info(
            "Getting committed at timestamp",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "snapshot_id": snapshot_id,
                    "operation": "GET_COMMITTED_AT_TIMESTAMP",
                    "state": "IN_PROGRESS",
                }
            },
        )

        try:
            timestamp_row = self.spark.sql(
                f"""
                SELECT 
                    committed_at AS committed_at_datetime,
                    DATE_FORMAT(committed_at, 'yyyy-MM-dd HH:mm:ss') AS committed_at_str,
                    (unix_timestamp(committed_at) + 1) * 1000 AS committed_at_ms
                FROM {self.table_id}.snapshots
                WHERE snapshot_id = {snapshot_id}
                LIMIT 1
                """
            ).first()
        except Exception as e:
            self.logger.error(
                "Failed to get committed at timestamp",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "snapshot_id": snapshot_id,
                        "operation": "GET_COMMITTED_AT_TIMESTAMP",
                        "state": "ERROR",
                        "output_format": output_format,
                    }
                },
                exc_info=e,
            )
            raise SnapshotManagerException(f"Failed to get committed at timestamp: {e}")

        if timestamp_row is None:
            self.logger.warning(
                "No committed at timestamp found",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "snapshot_id": snapshot_id,
                        "committed_at": None,
                        "output_format": output_format,
                        "operation": "GET_COMMITTED_AT_TIMESTAMP",
                        "state": "DONE",
                    }
                },
            )
            return None

        match output_format:
            case "str":
                output = timestamp_row.committed_at_str
            case "ms":
                output = timestamp_row.committed_at_ms
            case "datetime":
                output = timestamp_row.committed_at_datetime
            case _:
                raise SnapshotManagerException(
                    f"Invalid output format: {output_format}"
                )

        self.logger.info(
            "Committed at timestamp",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "snapshot_id": snapshot_id,
                    "committed_at": output,
                    "output_format": output_format,
                    "operation": "GET_COMMITTED_AT_TIMESTAMP",
                    "state": "DONE",
                }
            },
        )

        return output

    def set_last_snapshot_tag(self, tag_name: str) -> bool:
        current_snapshot_id = self.get_current_snapshot_id()

        self.logger.info(
            "Setting last snapshot ID tag",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": tag_name,
                    "operation": "SET_LAST_SNAPSHOT_TAG",
                    "state": "IN_PROGRESS",
                }
            },
        )

        if current_snapshot_id is None:
            self.logger.warning(
                "No current snapshot ID found, the last snapshot ID tag will not be set",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "tag_name": tag_name,
                        "current_snapshot_id": current_snapshot_id,
                        "operation": "SET_LAST_SNAPSHOT_TAG",
                        "state": "DONE",
                    }
                },
            )
            return False
        try:
            self.spark.sql(
                f"""
                ALTER TABLE {self.table_id}
                CREATE OR REPLACE TAG `{tag_name}` AS OF VERSION {current_snapshot_id}
                """
            )
        except Exception as e:
            self.logger.error(
                "Failed to set last snapshot tag",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "tag_name": tag_name,
                        "current_snapshot_id": current_snapshot_id,
                        "operation": "SET_LAST_SNAPSHOT_TAG",
                        "state": "ERROR",
                    }
                },
                exc_info=e,
            )
            return False

        self.logger.info(
            "Last snapshot tag set",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": tag_name,
                    "current_snapshot_id": current_snapshot_id,
                    "operation": "SET_LAST_SNAPSHOT_TAG",
                    "state": "DONE",
                }
            },
        )

        return True

    def drop_last_snapshot_tag(self, tag_name: str) -> bool:
        self.logger.info(
            "Dropping last snapshot ID tag",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": tag_name,
                    "operation": "DROP_LAST_SNAPSHOT_TAG",
                    "state": "IN_PROGRESS",
                }
            },
        )

        try:
            self.spark.sql(
                f"""
                ALTER TABLE {self.table_id}
                DROP TAG IF EXISTS `{tag_name}`
                """
            )
        except Exception as e:
            self.logger.error(
                "Failed to drop last snapshot tag",
                extra={
                    "attributes": {
                        "table_id": self.table_id,
                        "tag_name": tag_name,
                        "operation": "DROP_LAST_SNAPSHOT_TAG",
                        "state": "ERROR",
                    }
                },
                exc_info=e,
            )
            return False

        self.logger.info(
            "Last snapshot tag dropped",
            extra={
                "attributes": {
                    "table_id": self.table_id,
                    "tag_name": tag_name,
                    "operation": "DROP_LAST_SNAPSHOT_TAG",
                    "state": "DONE",
                }
            },
        )

        return True
