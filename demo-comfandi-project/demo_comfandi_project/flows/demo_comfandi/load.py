"""Load module for demo_comfandi data flow.

This module handles loading transformed data to target storage systems.
"""

from pyspark.sql import DataFrame, SparkSession

from demo_comfandi_project.libs.error_handler import handle_errors
from demo_comfandi_project.libs.logging import get_logger
from demo_comfandi_project.libs.resources import VarsResource

logger = get_logger(__name__)


@handle_errors
def load(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    transformed_data: DataFrame,
) -> None:
    """Load transformed data to target storage system.

    Args:
        job_id: Unique identifier for this job execution (for logging).
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration.
        transformed_data: Transformed DataFrame to load.
    """
    target_table_id = vars_instance.vars.output.table_id
    num_partitions = vars_instance.vars.num_partitions.min_global

    logger.info(
        "Loading data",
        extra={
            "attributes": {
                "job_id": job_id,
                "target_table": target_table_id,
                "load_strategy": "overwrite",
            }
        },
    )

    data_to_load = transformed_data
    if num_partitions:
        data_to_load = data_to_load.repartition(num_partitions)

    (
        data_to_load.write.mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(target_table_id)
    )

    logger.info(
        "Data load completed",
        extra={
            "attributes": {
                "job_id": job_id,
                "target_table": target_table_id,
                "load_strategy": "overwrite",
            }
        },
    )
