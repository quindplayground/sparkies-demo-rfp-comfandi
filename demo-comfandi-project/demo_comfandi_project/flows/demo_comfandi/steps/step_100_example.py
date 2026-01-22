"""Example step for analytics flow transformations.

This is a template step that demonstrates the pattern for creating
individual transformation steps in analytics flows.

Steps should be:
- Focused on a single transformation concern
- Well-documented with docstrings
- Testable in isolation
- Reusable across flows if needed
- Optimized using Spark best practices (column operations, minimal shuffles)
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as sf


def step_100_example_transformation(dataframe: DataFrame) -> DataFrame:
    """Example transformation step.

    This step demonstrates a typical transformation pattern optimized
    for Spark performance. Replace this with your actual transformation logic.

    Optimization guidelines:
    - Use column operations instead of row operations (withColumn, select)
    - Combine multiple transformations in a single pass when possible
    - Filter early if applicable to reduce data volume
    - Avoid unnecessary shuffles by grouping operations

    Args:
        dataframe: Input DataFrame to transform.

    Returns:
        Transformed DataFrame.

    Example:
        ```python
        transformed_df = step_100_example_transformation(input_df)
        ```

    Example optimized transformation:
        ```python
        # Good: Column operations combined
        transformed = dataframe.withColumn(
            "calculated_field",
            sf.col("field1") * sf.col("field2")
        ).withColumn(
            "normalized_field",
            sf.upper(sf.trim(sf.col("field3")))
        ).filter(
            sf.col("status") == "active"
        )

        # Bad: Row operations (avoid)
        # transformed = dataframe.rdd.map(lambda row: ...).toDF()
        ```
    """
    # Example transformation: add a calculated column using column operations
    # Optimization: Use column operations (withColumn) instead of row operations
    # transformed = dataframe.withColumn(
    #     "calculated_field",
    #     sf.col("field1") * sf.col("field2")
    # )

    return dataframe

