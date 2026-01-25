"""Demo Comfandi job for data flow.

This job orchestrates the ETL pipeline for Comfandi demo:
1. Extract: Reads data from datos.gov.co API (SODA v3)
2. Transform: Applies transformations and data quality rules
3. Load: Writes to target tables (Silver and Gold layers)

This flow is storage-agnostic and can work with various storage systems
(Iceberg, Delta Lake, Parquet files, databases, etc.). The ETL modules
(extract.py, transform.py, load.py) are implemented based on the
specific requirements for the SSF population data processing.
"""

import time

from pyspark.sql import SparkSession

from demo_comfandi_project.flows.demo_comfandi.extract import extract
from demo_comfandi_project.flows.demo_comfandi.load import load
from demo_comfandi_project.flows.demo_comfandi.transform import transform
from demo_comfandi_project.libs.logging import get_logger
from demo_comfandi_project.libs.resources import VarsResource
from demo_comfandi_project.libs.runner.types import Status


def demo_comfandi_job(spark: SparkSession, vars_instance: VarsResource) -> Status:
    """Demo Comfandi job function for data flow processing.

    This function orchestrates the ETL pipeline by calling extract, transform,
    and load functions in sequence. It provides structured logging and error
    handling throughout the process.

    The actual extraction, transformation, and loading logic is implemented
    in the respective modules (extract.py, transform.py, load.py).

    Any flow-specific orchestration logic (state tracking, change detection,
    restart, etc.) should only be added if your flow specifically requires it,
    based on your requirements.

    Args:
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration loaded from
            config/default.toml. Contains all flow configuration including:
            - Input/output table IDs
            - Flow-specific configuration (only what your flow requires)
            - Partitioning settings

    Returns:
        Status object indicating job completion status.

    Example:
        ```python
        from demo_comfandi_project.libs.resources import get_vars_resource

        # Load configuration
        vars_instance = get_vars_resource(
            env="dev",
            config_paths=["flows/your_flow_name/config/default.toml"]
        )

        # Execute job
        status = demo_comfandi_job(spark, vars_instance)

        if status.status_value == "OK":
            print("Job completed successfully")
        else:
            print(f"Job failed: {status.message}")
        ```

    Note:
        - Rename this function to match your flow name
        - Update operation names in logging attributes
        - Implement extract(), transform(), and load() functions
        - Only add flow-specific logic (state tracking, change detection, etc.) if required
        - Configure flow-specific settings in config/default.toml based on requirements
    """
    logger = get_logger(__name__)

    start_time = time.time()
    job_id = f"demo_comfandi_{int(start_time)}"

    # Get component name from configuration
    component_name = vars_instance.vars.get("component_name", "demo_comfandi")

    logger.info(
        "Starting demo comfandi processing job",
        extra={
            "attributes": {
                "operation": "EXECUTE_DEMO_COMFANDI_JOB",
                "job_id": job_id,
                "job_name": "demo_comfandi_job",
                "component": component_name,
                "input_table": vars_instance.vars.input.table_id,
                "output_table": vars_instance.vars.output.table_id,
                "status": "STARTED",
            }
        },
    )

    # EXTRACT
    logger.info(
        "Starting data extraction",
        extra={
            "attributes": {
                "operation": "EXECUTE_DEMO_COMFANDI_JOB",
                "job_id": job_id,
                "step": "extract",
                "source_table": vars_instance.vars.input.table_id,
                "status": "IN_PROGRESS",
            }
        },
    )

    # Extract data
    # Add any flow-specific parameters here only if your flow requires them
    # Example: if flow requires first_run detection:
    #   first_run = is_empty(spark, vars_instance.vars.output.table_id)
    #   extracted_data = extract(spark=spark, vars_instance=vars_instance, first_run=first_run)
    # Otherwise, use:
    extracted_data = extract(
        spark=spark,
        vars_instance=vars_instance,
    )

    logger.info(
        "Data extraction completed",
        extra={
            "attributes": {
                "operation": "EXECUTE_DEMO_COMFANDI_JOB",
                "job_id": job_id,
                "step": "extract",
                "source_table": vars_instance.vars.input.table_id,
                "status": "DONE",
            }
        },
    )

    # TRANSFORM
    logger.info(
        "Starting data transformation",
        extra={
            "attributes": {
                "operation": "EXECUTE_DEMO_COMFANDI_JOB",
                "job_id": job_id,
                "step": "transform",
                "status": "IN_PROGRESS",
            }
        },
    )

    # Transform data
    # Add any flow-specific parameters here only if your flow requires them
    transformed_data = transform(
        job_id=job_id,
        spark=spark,
        vars_instance=vars_instance,
        extracted_data=extracted_data,
    )

    logger.info(
        "Data transformation completed",
        extra={
            "attributes": {
                "operation": "EXECUTE_DEMO_COMFANDI_JOB",
                "job_id": job_id,
                "step": "transform",
                "status": "DONE",
            }
        },
    )

    # LOAD
    logger.info(
        "Starting data load",
        extra={
            "attributes": {
                "operation": "EXECUTE_DEMO_COMFANDI_JOB",
                "job_id": job_id,
                "step": "load",
                "target_table": vars_instance.vars.output.table_id,
                "status": "IN_PROGRESS",
            }
        },
    )

    # Load data
    # Add any flow-specific parameters here only if your flow requires them
    load(
        job_id=job_id,
        spark=spark,
        vars_instance=vars_instance,
        transformed_data=transformed_data,
    )

    logger.info(
        "Data load completed",
        extra={
            "attributes": {
                "operation": "EXECUTE_DEMO_COMFANDI_JOB",
                "job_id": job_id,
                "step": "load",
                "target_table": vars_instance.vars.output.table_id,
                "status": "DONE",
            }
        },
    )

    execution_time_ms = int((time.time() - start_time) * 1000)

    logger.info(
        "Demo comfandi processing job completed successfully",
        extra={
            "attributes": {
                "operation": "EXECUTE_DEMO_COMFANDI_JOB",
                "job_id": job_id,
                "status": "DONE",
                "execution_time_ms": execution_time_ms,
            }
        },
    )

    return Status(
        status_value="OK", message="Demo comfandi job completed successfully"
    )
