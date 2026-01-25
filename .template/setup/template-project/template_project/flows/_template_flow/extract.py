"""Template extract module for data flow.

This module handles data extraction from source tables or data sources.
The extraction logic is determined by your flow requirements and can support
various extraction strategies (full load, incremental, CDC, etc.) depending
on your needs.

The implementation should be based on your specific requirements:
- Source type (table, files, database, API, etc.)
- Storage system (Iceberg, Delta Lake, Parquet, JDBC, etc.)
- Extraction strategy (full, incremental, CDC, etc.) - if needed
- Any other flow-specific requirements

Available utilities:
- Iceberg: Utilities available in template_project.libs.iceberg (if using Iceberg)
- Other systems: Implement appropriate extraction logic for your storage system
"""

from pyspark.sql import DataFrame, SparkSession

from template_project.libs.error_handler import handle_errors
from template_project.libs.resources import VarsResource


@handle_errors
def extract(
    spark: SparkSession,
    vars_instance: VarsResource,
    **kwargs
) -> DataFrame:
    """Extract data from source.

    This function implements the extraction logic for the flow based on your
    specific requirements. The source can be any data source accessible via Spark.

    The source can be any data source accessible via Spark:
    - Tables (Iceberg, Delta, Hive, etc.)
    - Files (Parquet, CSV, JSON, etc.)
    - Databases (via JDBC)
    - APIs or other sources

    Args:
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration.
            - vars_instance.vars.input.table_id: Source identifier (table, path, etc.)
            - vars_instance.vars.input.error_path: Path for error logs
        **kwargs: Optional parameters based on flow requirements.
            Only add parameters if your flow specifically requires them.
            Examples: first_run, incremental, date_range, etc.

    Returns:
        DataFrame containing extracted data from source.

    Raises:
        NotImplementedError: This function must be implemented for your specific flow.

    Example:
        Basic extraction from table:
        ```python
        source_table = spark.table(vars_instance.vars.input.table_id)
        return source_table
        ```

        Extraction from files:
        ```python
        source_path = vars_instance.vars.input.table_id  # Can be a path
        return spark.read.parquet(source_path)
        ```

        Extraction from JDBC database:
        ```python
        return spark.read.format("jdbc") \
            .option("url", connection_string) \
            .option("dbtable", table_name) \
            .load()
        ```

        Extraction with optional parameters (if flow requires):
        ```python
        # Only add parameters if your flow specifically needs them
        first_run = kwargs.get("first_run", True)
        if first_run:
            return spark.table(vars_instance.vars.input.table_id)
        else:
            # Implement incremental extraction logic
            return incremental_extract(spark, vars_instance)
        ```

        Incremental extraction with Iceberg (if using Iceberg and flow requires it):
        ```python
        # Only implement if your flow specifically requires incremental extraction
        from template_project.libs.iceberg.cdc_with_tagging_strategy import ChangelogManager
        
        changelog_manager = ChangelogManager(
            spark=spark,
            table_id=vars_instance.vars.input.table_id,
            tag_name=vars_instance.vars.get("last_snapshot_tag_name")
        )
        return changelog_manager.get_changelog_table(...)
        ```

    Note:
        - Implement extraction based on your flow requirements, not assumptions
        - Only add parameters (like first_run, incremental) if the flow specifically requires them
        - Iceberg utilities are available in template_project.libs.iceberg if using Iceberg
        - You can implement extraction for any storage system using appropriate methods
        - See REFERENCE.md for more information on available utilities
    """
    raise NotImplementedError(
        "Extract function must be implemented. "
        "Implement your extraction logic based on your source data and storage system. "
        "See function docstring for examples."
    )
