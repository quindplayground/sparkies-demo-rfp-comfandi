"""Example step for analytics flow transformations.

This is a template step that demonstrates the pattern for creating
individual transformation steps in analytics flows.

Steps should be:
- Focused on a single transformation concern
- Well-documented with docstrings
- Testable in isolation
- Reusable across flows if needed
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as sf


def step_100_example_transformation(dataframe: DataFrame) -> DataFrame:
    """Example transformation step.

    This step demonstrates a typical transformation pattern.
    Replace this with your actual transformation logic.

    Args:
        dataframe: Input DataFrame to transform.

    Returns:
        Transformed DataFrame.

    Example:
        ```python
        transformed_df = step_100_example_transformation(input_df)
        ```
    """
    # Example transformation: add a calculated column
    # transformed = dataframe.withColumn(
    #     "calculated_field",
    #     sf.col("field1") * sf.col("field2")
    # )

    return dataframe

