"""Job module for demo_comfandi data flow.

This job orchestrates the ETL pipeline:
1. Extract: Reads data from source
2. Transform: Applies transformations
3. Load: Writes to target
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
    """Orchestrate the demo_comfandi ETL pipeline.

    This function orchestrates the ETL pipeline by calling extract, transform,
    and load functions in sequence. It provides structured logging and error
    handling throughout the process.

    Args:
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration loaded from
            config/default.toml. Contains all flow configuration including:
            - Input/output table IDs
            - Flow-specific configuration
            - Partitioning settings

    Returns:
        Status object indicating job completion status.
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
