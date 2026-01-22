"""Template transform module for data flow.

This module handles data transformation logic. Transformations can be simple
(for basic flows) or complex with multiple steps (for advanced flows).

The transformation pipeline typically includes:
- Data cleaning and normalization
- Type casting and validation
- Joins with reference tables
- Aggregations and calculations
- Business logic application

Transformations are organized as a series of steps that can be executed
sequentially. Each step should be focused on a single transformation concern.
"""

from pyspark.sql import DataFrame, SparkSession

from template_project.libs.error_handler import handle_errors
from template_project.libs.resources import VarsResource


@handle_errors
def transform(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    extracted_data: DataFrame,
    **kwargs
) -> DataFrame:
    """Transform data through transformation pipeline.

    This function orchestrates all transformation steps for the flow. It receives
    the extracted data and applies a series of transformations to prepare it
    for loading based on your specific business requirements.

    Args:
        job_id: Unique identifier for this job execution (for logging).
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration.
        extracted_data: Input DataFrame from extraction step.
        **kwargs: Optional parameters based on flow requirements.
            Only add parameters if your flow specifically requires them.
            Examples: first_run, incremental, etc.

    Returns:
        Fully transformed DataFrame ready for loading.

    Raises:
        NotImplementedError: This function must be implemented for your specific flow.

    Example:
        Simple transformation pipeline:
        ```python
        from pyspark.sql import functions as sf
        from template_project.libs.logging import get_logger

        logger = get_logger(__name__)

        # Step 1: Clean data
        cleaned = extracted_data.dropDuplicates()

        # Step 2: Cast types
        typed = cleaned.withColumn("date_col", sf.col("date_col").cast("date"))

        # Step 3: Add metadata
        from template_project.libs.common_patterns import current_timestamp_with_tz
        final = typed.withColumn(
            "current_timestamp_dwh",
            current_timestamp_with_tz("yyyy-MM-dd HH:mm:ss", "America/Bogota")
        )

        return final
        ```

        Complex transformation with multiple steps:
        ```python
        # Import step functions
        from template_project.flows.your_flow.steps import (
            step_100_clean_data,
            step_200_cast_types,
            step_300_join_reference,
            step_400_aggregate
        )

        # Execute steps sequentially
        step_100 = step_100_clean_data(extracted_data)
        step_200 = step_200_cast_types(step_100)
        step_300 = step_300_join_reference(spark, vars_instance, step_200)
        step_400 = step_400_aggregate(step_300)

        return step_400
        ```

        Transformation with optional parameters (if flow requires):
        ```python
        # Only add parameters if your flow specifically needs them
        first_run = kwargs.get("first_run", True)
        if first_run:
            # Full transformation logic
            return full_transform(extracted_data)
        else:
            # Incremental transformation logic
            return incremental_transform(extracted_data)
        ```

    Note:
        - Organize complex transformations into separate step functions
        - Place step functions in the `steps/` directory
        - Use logging to track transformation progress
        - Only add parameters (like first_run) if the flow specifically requires them
        - Implement transformations based on your business requirements
    """
    raise NotImplementedError(
        "Transform function must be implemented. "
        "Implement your transformation logic based on your business requirements. "
        "See function docstring for examples."
    )
