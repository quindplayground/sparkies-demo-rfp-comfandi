"""Transform module for demo_comfandi data flow.

This module handles data transformation logic for SSF population data.
The transformation pipeline includes:
- Data cleaning and normalization (CCF field)
- Type casting and validation
- Data quality checks and flags
- Metadata addition (year_month, ingestion_ts, job_run_id)
- Deduplication by natural key (a_o, mes, ccf)
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
    **kwargs,
) -> DataFrame:
    """Transform data through transformation pipeline for Silver layer.

    This function orchestrates all transformation steps for the SSF population data:
    1. Clean and normalize CCF field (trim, uppercase, collapse spaces)
    2. Cast types (ensure integers for a_o, mes, and all metrics)
    3. Add metadata columns (year_month, ingestion_ts, job_run_id)
    4. Apply data quality checks and flags
    5. Deduplicate by natural key (a_o, mes, ccf)

    Args:
        job_id: Unique identifier for this job execution (for logging).
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration.
        extracted_data: Input DataFrame from extraction step with schema:
            - a_o (IntegerType)
            - mes (IntegerType)
            - ccf (StringType)
            - empresas_afiliadas (IntegerType)
            - total_afiliados_cajas (IntegerType)
            - trabajadores_afiliados (IntegerType)
            - afiliados_facultativos (IntegerType)
            - afiliados_pensionados (IntegerType)
            - afiliados_fidelidad (IntegerType)
            - no_afiliados_con_derecho (IntegerType)
            - personas_cargo_2 (IntegerType)
            - total_poblaci_n_cubierta (IntegerType)
        **kwargs: Optional parameters based on flow requirements.

    Returns:
        Fully transformed DataFrame ready for loading to Silver layer with:
        - All original columns (typed and cleaned)
        - year_month (string YYYY-MM)
        - ingestion_ts (timestamp)
        - job_run_id (string)
        - DQ flags: dq_is_valid_month, dq_non_negative, dq_total_cubierta_consistente, dq_key_not_null

    Example:
        ```python
        transformed = transform(
            job_id="demo_comfandi_1234567890",
            spark=spark,
            vars_instance=vars_instance,
            extracted_data=extracted_df
        )
        ```
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

    # Optimize: Combine all transformations in a single pass to minimize shuffles
    # Step 1-3: Clean CCF, cast types, and add metadata in one pass
    transformed = (
        extracted_data
        # Clean and normalize CCF field (trim, uppercase, collapse spaces)
        .withColumn(
            "ccf",
            sf.upper(sf.trim(sf.regexp_replace(sf.col("ccf"), r"\s+", " "))),
        )
        # Cast all numeric columns to int in one pass
        .withColumn("a_o", sf.col("a_o").cast("int"))
        .withColumn("mes", sf.col("mes").cast("int"))
        .withColumn("empresas_afiliadas", sf.col("empresas_afiliadas").cast("int"))
        .withColumn("total_afiliados_cajas", sf.col("total_afiliados_cajas").cast("int"))
        .withColumn("trabajadores_afiliados", sf.col("trabajadores_afiliados").cast("int"))
        .withColumn("afiliados_facultativos", sf.col("afiliados_facultativos").cast("int"))
        .withColumn("afiliados_pensionados", sf.col("afiliados_pensionados").cast("int"))
        .withColumn("afiliados_fidelidad", sf.col("afiliados_fidelidad").cast("int"))
        .withColumn("no_afiliados_con_derecho", sf.col("no_afiliados_con_derecho").cast("int"))
        .withColumn("personas_cargo_2", sf.col("personas_cargo_2").cast("int"))
        .withColumn("total_poblaci_n_cubierta", sf.col("total_poblaci_n_cubierta").cast("int"))
        # Add metadata columns
        .withColumn(
            "year_month",
            sf.concat(
                sf.col("a_o").cast("string"),
                sf.lit("-"),
                sf.lpad(sf.col("mes").cast("string"), 2, "0"),
            ),
        )
        .withColumn(
            "ingestion_ts",
            current_timestamp_with_tz("yyyy-MM-dd HH:mm:ss", "America/Bogota"),
        )
        .withColumn("job_run_id", sf.lit(job_id))
        # Step 4: Apply data quality checks and flags
        .withColumn(
            "dq_is_valid_month",
            (sf.col("mes") >= 1) & (sf.col("mes") <= 12),
        )
        .withColumn(
            "dq_non_negative",
            (sf.col("empresas_afiliadas") >= 0)
            & (sf.col("total_afiliados_cajas") >= 0)
            & (sf.col("trabajadores_afiliados") >= 0)
            & (sf.col("afiliados_facultativos") >= 0)
            & (sf.col("afiliados_pensionados") >= 0)
            & (sf.col("afiliados_fidelidad") >= 0)
            & (sf.col("no_afiliados_con_derecho") >= 0)
            & (sf.col("personas_cargo_2") >= 0)
            & (sf.col("total_poblaci_n_cubierta") >= 0),
        )
        .withColumn(
            "dq_total_cubierta_consistente",
            sf.col("total_poblaci_n_cubierta")
            == (sf.col("total_afiliados_cajas") + sf.col("personas_cargo_2")),
        )
        .withColumn(
            "dq_key_not_null",
            sf.col("a_o").isNotNull()
            & sf.col("mes").isNotNull()
            & sf.col("ccf").isNotNull(),
        )
    )

    # Step 5: Deduplicate by natural key (a_o, mes, ccf)
    # dropDuplicates internally optimizes partitioning, so no manual repartition needed
    # If duplicates exist, keep the first occurrence (deterministic)
    natural_key_cols = ["a_o", "mes", "ccf"]
    result = transformed.dropDuplicates(natural_key_cols)

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

    return result
