"""Load utilities for Iceberg tables."""

from datetime import datetime, timedelta, timezone

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as sf


def load_overwrite(
        spark: SparkSession, 
        dataframe: DataFrame, 
        table_id: str, 
        iceberg_catalog: str = "local",
        partition_by: list[str] | None = None,
        location: str | None = None,
        num_partitions: int | None = None,
        expire_snapshots: bool = True,
        remove_orphan_files: bool = True,
        num_snapshots_to_retain: int = 5,
        days_to_retain: int = 1
    ) -> None:
    """Load data into an Iceberg table with overwrite operation.

    Args:
        spark: Spark session instance.
        dataframe: DataFrame to load into the table.
        table_id: Target Iceberg table name.
        iceberg_catalog: Iceberg catalog name. Defaults to "local".
        partition_by: List of columns to partition the table.
        location: Custom location for the table.
        num_partitions: Number of partitions for repartitioning.
        expire_snapshots: Whether to expire old snapshots.
        remove_orphan_files: Whether to remove orphan files.
        num_snapshots_to_retain: Number of snapshots to retain.
        days_to_retain: Number of days to retain files.
    """"
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=days_to_retain)
    one_day_ago_str = one_day_ago.strftime('%Y-%m-%d %H:%M:%S')

    base_writer = dataframe

    if num_partitions:
        base_writer = base_writer.repartition(num_partitions)

    base_writer = base_writer \
        .writeTo(table_id) \
        .using("iceberg") \
        
    if partition_by:
        base_writer = base_writer.partitionedBy(*[sf.col(col) for col in partition_by])

    if location:
        base_writer = base_writer.tableProperty("location", location)

    if not spark.catalog.tableExists(table_id):
        base_writer \
            .tableProperty("write.merge.isolation-level", "serializable") \
            .tableProperty("write.update.isolation-level", "serializable") \
            .tableProperty("write.delete.isolation-level", "serializable") \
            .tableProperty("write.spark.fanout.enabled", "true") \
            .tableProperty("write.delete.mode", "merge-on-read") \
            .tableProperty("write.update.mode", "merge-on-read") \
            .tableProperty("write.merge.mode", "merge-on-read") \
            .tableProperty("format-version", "2") \
            .createOrReplace()
    else:
        base_writer \
            .option("overwriteSchema", "true") \
            .overwritePartitions()

    if expire_snapshots:
        spark.sql(f"""
            CALL {iceberg_catalog}.system.expire_snapshots(
                table => '{table_id}', 
                retain_last => {num_snapshots_to_retain}
            )
        """)

    if remove_orphan_files:
        spark.sql(f"""
            CALL {iceberg_catalog}.system.remove_orphan_files(
                table => '{table_id}', 
                older_than => TIMESTAMP '{one_day_ago_str}'
            )
        """)