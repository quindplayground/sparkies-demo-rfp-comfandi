"""Maintenance utilities for Iceberg tables."""

from datetime import datetime, timedelta, timezone

from pyspark.sql import SparkSession

from demo_comfandi_project.libs.logging import get_logger


def _get_table_property(spark: SparkSession, table_id: str, prop: str) -> str | None:
    """Get a property from an Iceberg table.

    Args:
        spark: Spark session for processing.
        table_id: Iceberg table name.
        prop: Property name to retrieve.

    Returns:
        Property value or None if it doesn't exist.
    """
    try:
        single_prop_df = spark.sql(f"SHOW TBLPROPERTIES {table_id}('{prop}')")
        vals = single_prop_df.limit(1).collect()
        if vals:
            return vals[0][0]
    except Exception:
        pass

    try:
        props_df = spark.sql(f"SHOW TBLPROPERTIES {table_id}")
        row = props_df.filter(props_df.key == prop).limit(1).collect()
        if row:
            return row[0][1]
    except Exception:
        pass

    return None


def _set_table_property(
    spark: SparkSession, table_id: str, prop: str, value: str
) -> None:
    """Set a property on an Iceberg table.

    Args:
        spark: Spark session for processing.
        table_id: Iceberg table name.
        prop: Property name to set.
        value: Property value to set.
    """
    spark.sql(f"ALTER TABLE {table_id} SET TBLPROPERTIES ('{prop}'='{value}')")


def _should_run(now: datetime, last_run_str: str | None, frequency: str) -> bool:
    """Determine if maintenance should run.

    Args:
        now: Current date and time.
        last_run_str: Last run date and time string.
        frequency: Maintenance frequency (daily or weekly).

    Returns:
        True if maintenance should run, False otherwise.
    """
    if not last_run_str:
        return True
    try:
        last_run = datetime.fromisoformat(last_run_str)
    except Exception:
        return True

    if frequency == "daily":
        return now.date() > last_run.date()
    if frequency == "weekly":
        return (now - last_run).days >= 7 or (
            now.isocalendar().week != last_run.isocalendar().week
        )
    return True


def run_daily_maintenance(
    spark: SparkSession,
    catalog: str,
    table_id: str,
    num_snapshots_to_retain: int = 2,
    orphan_files_older_than_days: int = 1,
) -> None:
    """Run daily maintenance for an Iceberg table.

    Args:
        spark: Spark session for processing.
        catalog: Iceberg catalog name.
        table_id: Iceberg table name.
        num_snapshots_to_retain: Number of snapshots to retain.
        orphan_files_older_than_days: Number of days to retain files.
    """
    logger = get_logger(__name__)

    now = datetime.now(timezone.utc)
    prop_key = "maintenance.daily.last_run"
    last_run = _get_table_property(spark, table_id, prop_key)

    if not _should_run(now, last_run, "daily"):
        return None

    errors: list[str] = []

    try:
        spark.sql(
            f"""
            CALL {catalog}.system.expire_snapshots(
                table => '{table_id}', 
                retain_last => {num_snapshots_to_retain}
            )
            """
        )
    except Exception as e:
        errors.append(f"expire_snapshots failed: {e}")

    try:
        older_than = now - timedelta(days=orphan_files_older_than_days)
        older_than_str = older_than.strftime("%Y-%m-%d %H:%M:%S")
        spark.sql(
            f"""CALL {catalog}.system.remove_orphan_files(
                table => '{table_id}', 
                older_than => TIMESTAMP '{older_than_str}'
            )
            """
        )
    except Exception as e:
        errors.append(f"remove_orphan_files failed: {e}")

    if errors:
        logger.error(
            "Daily maintenance finished with errors",
            extra={"attributes": {"table": table_id, "errors": errors}},
        )
    else:
        logger.info(
            "Daily maintenance completed",
            extra={"attributes": {"table": table_id, "status": "DONE"}},
        )

    _set_table_property(spark, table_id, prop_key, now.isoformat())

    return None


def run_weekly_maintenance(
    spark: SparkSession,
    catalog: str,
    table_id: str,
    target_file_size_mb: int = 256,
    delete_min_input_files: int | None = None,
    delete_rewrite_all: bool = False,
    delete_target_file_size_mb: int | None = None,
) -> None:
    """Run weekly maintenance for an Iceberg table.

    Args:
        spark: Spark session for processing.
        catalog: Iceberg catalog name.
        table_id: Iceberg table name.
        target_file_size_mb: Target file size in MB.
        delete_min_input_files: Minimum number of input files to delete.
        delete_rewrite_all: Whether to rewrite all files.
        delete_target_file_size_mb: Target file size for deletion in MB.
    """
    logger = get_logger(__name__)

    now = datetime.now(timezone.utc)
    prop_key = "maintenance.weekly.last_run"
    last_run = _get_table_property(spark, table_id, prop_key)

    if not _should_run(now, last_run, "weekly"):
        return None

    errors: list[str] = []

    try:
        spark.sql(f"CALL {catalog}.system.rewrite_manifests(table => '{table_id}')")
    except Exception as e:
        errors.append(f"rewrite_manifests failed: {e}")

    try:
        spark.sql(
            f"""CALL {catalog}.system.rewrite_data_files(
                table => '{table_id}', 
                options => map('target-file-size-bytes','{target_file_size_mb * 1024 * 1024}')
            )
            """
        )
    except Exception as e:
        errors.append(f"rewrite_data_files failed: {e}")

    try:
        delete_opts: list[str] = []
        if delete_rewrite_all:
            delete_opts.append("'rewrite-all','true'")
        if delete_min_input_files is not None:
            delete_opts.append(f"'min-input-files','{delete_min_input_files}'")
        if delete_target_file_size_mb is not None:
            delete_opts.append(
                f"'target-file-size-bytes','{delete_target_file_size_mb * 1024 * 1024}'"
            )

        options_clause = ""
        if delete_opts:
            options_clause = ", options => map(" + ", ".join(delete_opts) + ")"

        spark.sql(
            f"CALL {catalog}.system.rewrite_position_delete_files(table => '{table_id}'{options_clause})"
        )
    except Exception as e:
        errors.append(f"rewrite_position_delete_files failed: {e}")

    if errors:
        logger.error(
            "Weekly maintenance finished with errors",
            extra={"attributes": {"table": table_id, "errors": errors}},
        )
    else:
        logger.info(
            "Weekly maintenance completed",
            extra={"attributes": {"table": table_id, "status": "DONE"}},
        )

    _set_table_property(spark, table_id, prop_key, now.isoformat())

    return None
