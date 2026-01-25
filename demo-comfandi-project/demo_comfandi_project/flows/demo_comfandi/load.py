"""Load module for demo_comfandi data flow.

This module handles loading transformed data to target storage systems.
The load strategy uses overwrite mode to replace all data in the target table.
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
    **kwargs,
) -> None:
    """Load transformed data to target storage system using overwrite strategy.

    This function implements loading logic for the SSF population data flow.
    It uses overwrite mode to replace all data in the target table, which is
    appropriate for this flow since:
    - The transform step already performs deduplication by natural key (a_o, mes, ccf)
    - The flow processes full dataset from the API each run
    - No merge keys are configured in the flow requirements

    Args:
        job_id: Unique identifier for this job execution (for logging).
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration.
            - vars_instance.vars.output.table_id: Target table identifier
            - vars_instance.vars.num_partitions.min_global: Partition count (if applicable)
        transformed_data: Transformed DataFrame to load.
        **kwargs: Optional parameters (not used in this implementation).

    Note:
        - If the flow requirements specify a different storage system (Iceberg, Delta, etc.)
          or load strategy (merge, append), update this implementation accordingly.
        - If merge strategy is required, configure merge_keys in config/default.toml
          and implement merge logic instead of overwrite.
    """
    target_table_id = vars_instance.vars.output.table_id
    num_partitions = vars_instance.vars.num_partitions.min_global

    logger.info(
        "Loading data to target table",
        extra={
            "attributes": {
                "job_id": job_id,
                "target_table": target_table_id,
                "load_strategy": "overwrite",
                "input_rows": transformed_data.count(),
                "num_partitions": num_partitions,
            }
        },
    )

    # Repartition if configured
    data_to_load = transformed_data
    if num_partitions:
        data_to_load = transformed_data.repartition(num_partitions)

    # Load data using overwrite mode
    # This works with any Spark-compatible storage system (tables, files, etc.)
    data_to_load.write.mode("overwrite").saveAsTable(target_table_id)

    logger.info(
        "Data load completed successfully",
        extra={
            "attributes": {
                "job_id": job_id,
                "target_table": target_table_id,
                "load_strategy": "overwrite",
                "rows_loaded": data_to_load.count(),
            }
        },
    )
