"""Transform module for demo_comfandi data flow.

This module handles data transformation logic for the demo_comfandi flow.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as sf

from demo_comfandi_project.libs.common_patterns import current_timestamp_with_tz
from demo_comfandi_project.libs.error_handler import handle_errors
from demo_comfandi_project.libs.logging import get_logger
from demo_comfandi_project.libs.resources import VarsResource

logger = get_logger(__name__)


@handle_errors
def transform(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    extracted_data: DataFrame,
    **kwargs
) -> DataFrame:
    """Transform data through transformation pipeline.

    Args:
        job_id: Unique identifier for this job execution (for logging).
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration.
        extracted_data: Input DataFrame from extraction step.
        **kwargs: Optional parameters based on flow requirements.

    Returns:
        Fully transformed DataFrame ready for loading.
    """
    input_table_id = vars_instance.vars.input.table_id
    output_table_id = vars_instance.vars.output.table_id

    logger.info(
        "Transformation started",
        extra={
            "attributes": {
                "job_id": job_id,
                "input_table_id": input_table_id,
                "output_table_id": output_table_id,
            }
        },
    )

    # Step 1: Clean data - remove duplicates
    # TODO(user): Define deduplication columns based on business requirements
    # Example: cleaned = extracted_data.dropDuplicates(["key_column"])
    cleaned = extracted_data.dropDuplicates()

    # Step 2: Cast types
    # TODO(user): Define type casting rules based on input schema and requirements
    # Example:
    # typed = cleaned.withColumn("date_col", sf.col("date_col").cast("date"))
    # typed = typed.withColumn("numeric_col", sf.col("numeric_col").cast("decimal(18,2)"))
    typed = cleaned

    # Step 3: Apply business logic transformations
    # TODO(user): Implement business logic transformations according to requirements
    # Examples:
    # - Normalize string columns: sf.upper(sf.trim(sf.col("name")))
    # - Calculate derived columns: sf.col("price") * sf.col("quantity")
    # - Apply filters: .filter(sf.col("status") == "active")
    transformed = typed

    # Step 4: Join with reference tables (if needed)
    # TODO(user): Implement joins with reference tables if required
    # Example:
    # reference_table = spark.table(vars_instance.vars.input.reference_table_id)
    # enriched = transformed.join(
    #     reference_table,
    #     transformed["key"] == reference_table["key"],
    #     "left"
    # )
    enriched = transformed

    # Step 5: Add metadata columns
    final = enriched.withColumn(
        "current_timestamp_dwh",
        current_timestamp_with_tz("yyyy-MM-dd HH:mm:ss", "America/Bogota")
    )

    logger.info(
        "Transformation completed",
        extra={
            "attributes": {
                "job_id": job_id,
                "input_table_id": input_table_id,
                "output_table_id": output_table_id,
            }
        },
    )

    return final
