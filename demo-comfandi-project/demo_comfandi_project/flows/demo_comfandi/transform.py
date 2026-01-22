"""Transform module for demo_comfandi data flow.

This module handles data transformation logic for the demo_comfandi flow.
Optimized using Spark best practices for performance and resource efficiency.
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

    Optimizations applied:
    - Early filtering to reduce data volume
    - Efficient deduplication with specific columns
    - Combined operations to minimize shuffles
    - Broadcast hints for small lookup tables
    - Column operations instead of row operations

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

    # Step 1: Early filtering (if applicable)
    # Filter early to reduce data volume before expensive operations
    # TODO(user): Add early filters based on business requirements
    # Example: filtered = extracted_data.filter(sf.col("status") == "active")
    filtered = extracted_data

    # Step 2: Clean data - remove duplicates
    # Optimization: Specify columns for deduplication to avoid full row comparison
    # This reduces shuffle overhead compared to dropDuplicates() without columns
    # TODO(user): Define deduplication columns based on business requirements
    # Example: cleaned = filtered.dropDuplicates(["key_column", "timestamp"])
    # If no specific columns, use subset=None but be aware of performance impact
    cleaned = filtered.dropDuplicates()

    # Step 3: Cast types and apply business logic transformations
    # Optimization: Combine type casting and transformations in single pass
    # to minimize number of DataFrame operations and shuffles
    # TODO(user): Define type casting rules and business logic transformations
    # Examples:
    # transformed = cleaned.withColumn(
    #     "date_col", sf.col("date_col").cast("date")
    # ).withColumn(
    #     "numeric_col", sf.col("numeric_col").cast("decimal(18,2)")
    # ).withColumn(
    #     "normalized_name", sf.upper(sf.trim(sf.col("name")))
    # ).withColumn(
    #     "calculated_field", sf.col("price") * sf.col("quantity")
    # ).filter(
    #     sf.col("status") == "active"
    # )
    transformed = cleaned

    # Step 4: Join with reference tables (if needed)
    # Optimization: Use broadcast hint for small lookup tables (< 10MB)
    # This avoids expensive shuffle joins and improves performance significantly
    # TODO(user): Implement joins with reference tables if required
    # Example for small lookup table (< 10MB):
    # from pyspark.sql.functions import broadcast
    # reference_table = spark.table(vars_instance.vars.input.reference_table_id)
    # enriched = transformed.join(
    #     broadcast(reference_table),
    #     transformed["key"] == reference_table["key"],
    #     "left"
    # )
    # Example for large tables (use regular join):
    # enriched = transformed.join(
    #     reference_table,
    #     transformed["key"] == reference_table["key"],
    #     "left"
    # )
    enriched = transformed

    # Step 5: Add metadata columns
    # Optimization: Use column operations (already optimal)
    final = enriched.withColumn(
        "current_timestamp_dwh",
        current_timestamp_with_tz("yyyy-MM-dd HH:mm:ss", "America/Bogota")
    )

    # Optional: Coalesce partitions after filtering/transformation if data volume
    # has been significantly reduced to avoid too many small partitions
    # TODO(user): Uncomment and adjust if needed after filtering operations
    # final = final.coalesce(optimal_partition_count)

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
