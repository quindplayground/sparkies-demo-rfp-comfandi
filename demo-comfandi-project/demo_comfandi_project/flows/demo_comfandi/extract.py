"""Extract module for demo_comfandi data flow.

This module handles data extraction from source tables.
"""

from pyspark.sql import DataFrame, SparkSession

from demo_comfandi_project.libs.error_handler import handle_errors
from demo_comfandi_project.libs.logging import get_logger
from demo_comfandi_project.libs.resources import VarsResource

logger = get_logger(__name__)


@handle_errors
def extract(
    spark: SparkSession,
    vars_instance: VarsResource,
) -> DataFrame:
    """Extract data from source table.

    Args:
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration.
            - vars_instance.vars.input.table_id: Source table identifier

    Returns:
        DataFrame containing extracted data from source table.
    """
    source_table_id = vars_instance.vars.input.table_id

    logger.info(
        "Extracting data from source",
        extra={
            "attributes": {
                "source_table": source_table_id,
            }
        },
    )

    extracted_data = spark.table(source_table_id)

    logger.info(
        "Data extraction completed",
        extra={
            "attributes": {
                "source_table": source_table_id,
            }
        },
    )

    return extracted_data
