"""Table utilities for Iceberg tables."""

from datetime import datetime, timedelta, timezone

from pyspark.sql import SparkSession

from template_project.libs.logging import get_logger


def is_empty(spark: SparkSession, table_id: str) -> bool:
    """Check if an Iceberg table is empty.

    Args:
        spark: Spark session instance.
        table_id: Table name to check.

    Returns:
        True if the table is empty, False otherwise.
    """
    if not spark.catalog.tableExists(table_id):
        return True

    files_metadata = spark.sql(
        "SELECT 1 FROM {files_dataframe} WHERE content = 0 LIMIT 1",
        files_dataframe=spark.table(f"{table_id}.files"),
    )

    has_data = files_metadata.head(1) != []

    return not has_data


def restart_table(
    spark: SparkSession,
    iceberg_catalog: str | None = None,
    table_id: str | None = None,
    cdc_control_table_id: str | None = None,
    expire_snapshots: bool = True,
    remove_orphan_files: bool = True,
    num_snapshots_to_retain: int = 1,
    days_to_retain: int = 1,
) -> bool:
    """Restart a table in the database.

    Args:
        spark: Spark session for processing.
        iceberg_catalog: Iceberg catalog name.
        table_id: Table name to restart.
        cdc_control_table_id: Control table name for snapshot tracking.
        expire_snapshots: Whether to expire old snapshots.
        remove_orphan_files: Whether to remove orphan files.
        num_snapshots_to_retain: Number of snapshots to retain.
        days_to_retain: Number of days to retain files.

    Returns:
        True if the table was restarted successfully, False otherwise.
    """
    logger = get_logger(__name__)
    ok = True

    def _delete_all(table: str) -> bool:
        try:
            logger.info(
                "Deleting all rows", extra={"table": table, "status": "IN_PROGRESS"}
            )
            spark.sql(
                f"""
                DELETE FROM {table}
                WHERE TRUE
            """
            )
            logger.info("All rows deleted", extra={"table": table, "status": "DONE"})
            return True
        except Exception as error:
            logger.error(
                "Failed to delete all rows",
                extra={"table": table, "status": "FAILED"},
                exc_info=error,
            )
            return False

    if table_id and spark.catalog.tableExists(table_id):
        ok = _delete_all(table_id) and ok

        days_ago = datetime.now(timezone.utc) - timedelta(days=days_to_retain)
        catalog = iceberg_catalog if iceberg_catalog else table_id.split(".")[0]

        try:
            if expire_snapshots:
                logger.info(
                    "Expiring snapshots",
                    extra={"table": table_id, "status": "IN_PROGRESS"},
                )
                spark.sql(
                    f"""
                    CALL {catalog}.system.expire_snapshots(
                        table => '{table_id}', 
                        retain_last => {num_snapshots_to_retain}
                    )
                """
                )
                logger.info(
                    "Snapshots expired", extra={"table": table_id, "status": "DONE"}
                )

            if remove_orphan_files:
                logger.info(
                    "Removing orphan files",
                    extra={"table": table_id, "status": "IN_PROGRESS"},
                )
                spark.sql(
                    f"""
                    CALL {catalog}.system.remove_orphan_files(
                        table => '{table_id}', 
                        older_than => TIMESTAMP '{days_ago.strftime('%Y-%m-%d %H:%M:%S')}'
                    )
                """
                )
                logger.info(
                    "Orphan files removed", extra={"table": table_id, "status": "DONE"}
                )
        except Exception as e:
            logger.warning(
                "Failed to expire snapshots or remove orphan files",
                extra={"table": table_id, "status": "FAILED"},
                exc_info=e,
            )

    if cdc_control_table_id and spark.catalog.tableExists(cdc_control_table_id):
        ok = _delete_all(cdc_control_table_id) and ok

    return ok
