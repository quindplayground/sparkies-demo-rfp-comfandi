"""Template load module for data flow.

This module handles loading transformed data to target storage systems.
The load strategy is determined by your flow requirements and can support
various strategies (overwrite, merge, append, etc.) depending on your needs.

The target can be any storage system accessible via Spark:
- Tables (Iceberg, Delta, Hive, etc.)
- Files (Parquet, CSV, JSON, etc.)
- Databases (via JDBC)
- Other systems (DynamoDB, etc.)

Available utilities:
- Iceberg: Utilities available in demo_comfandi_project.libs.iceberg (if using Iceberg)
- Other systems: Implement appropriate loading logic for your storage system
"""

from pyspark.sql import DataFrame, SparkSession

from demo_comfandi_project.libs.error_handler import handle_errors
from demo_comfandi_project.libs.resources import VarsResource


@handle_errors
def load(
    job_id: str,
    spark: SparkSession,
    vars_instance: VarsResource,
    transformed_data: DataFrame,
    **kwargs
) -> None:
    """Load transformed data to target storage system.

    This function implements the loading logic for the flow based on your
    specific requirements. The load strategy should be determined by your
    flow requirements, not by configuration flags.

    Args:
        job_id: Unique identifier for this job execution (for logging).
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration.
            - vars_instance.vars.output.table_id: Target identifier (table, path, etc.)
            - vars_instance.vars.output.merge_keys: Keys for merge operations (if using merge)
            - vars_instance.vars.num_partitions.min_global: Partition count (if applicable)
        transformed_data: Transformed DataFrame to load.
        **kwargs: Optional parameters based on flow requirements.
            Only add parameters if your flow specifically requires them.
            Examples: first_run, incremental, etc.

    Raises:
        NotImplementedError: This function must be implemented for your specific flow.

    Example:
        Overwrite mode to table:
        ```python
        transformed_data.write \
            .mode("overwrite") \
            .saveAsTable(vars_instance.vars.output.table_id)
        ```

        Overwrite mode to files:
        ```python
        output_path = vars_instance.vars.output.table_id  # Can be a path
        transformed_data.write \
            .mode("overwrite") \
            .parquet(output_path)
        ```

        Overwrite mode with Iceberg utilities (if using Iceberg):
        ```python
        from demo_comfandi_project.libs.iceberg.utils import load_overwrite

        load_overwrite(
            spark=spark,
            dataframe=transformed_data,
            table_id=vars_instance.vars.output.table_id,
            num_partitions=vars_instance.vars.num_partitions.min_global
        )
        ```

        Merge mode with Iceberg utilities (if using merge strategy):
        ```python
        from demo_comfandi_project.libs.iceberg.utils import load_merge

        load_merge(
            spark=spark,
            dataframe=transformed_data,
            table_id=vars_instance.vars.output.table_id,
            merge_keys=vars_instance.vars.output.merge_keys,
            num_partitions=vars_instance.vars.num_partitions.min_global
        )
        ```

        Merge mode with Delta Lake:
        ```python
        from delta.tables import DeltaTable

        delta_table = DeltaTable.forName(spark, vars_instance.vars.output.table_id)
        delta_table.alias("target") \
            .merge(
                transformed_data.alias("source"),
                "target.id = source.id"  # Your merge condition
            ) \
            .whenMatchedUpdateAll() \
            .whenNotMatchedInsertAll() \
            .execute()
        ```

        Load to DynamoDB (example):
        ```python
        from demo_comfandi_project.libs.aws.dynamodb.loader import DynamoDBLoader
        
        loader = DynamoDBLoader(spark, vars_instance)
        loader.load(transformed_data)
        ```

        Load with optional parameters (if flow requires):
        ```python
        # Only add parameters if your flow specifically needs them
        first_run = kwargs.get("first_run", True)
        if first_run:
            load_overwrite(...)
        else:
            load_merge(...)
        ```

    Note:
        - Implement load strategy based on your flow requirements, not assumptions
        - Only add parameters (like first_run) if the flow specifically requires them
        - Configure merge_keys in [default.output] section of config/default.toml only if using merge
        - Iceberg utilities are available in demo_comfandi_project.libs.iceberg if using Iceberg
        - You can implement loading for any storage system using appropriate methods
        - See REFERENCE.md for more information on available utilities
    """
    raise NotImplementedError(
        "Load function must be implemented. "
        "Implement your loading logic based on your target storage system and configuration. "
        "See function docstring for examples."
    )
