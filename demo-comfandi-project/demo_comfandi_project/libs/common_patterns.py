"""Common patterns and utilities module for Spark DataFrame manipulation."""

from typing import Any

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as sf
from pyspark.sql.types import StringType


def current_timestamp_with_tz(timestamp_format: str, tz: str) -> Column:
    """Returns the current timestamp formatted with a specific timezone.

    Args:
        timestamp_format: Format to display the timestamp.
        tz: Timezone to apply to the current timestamp.

    Returns:
        Spark column with the formatted timestamp.
    """
    return sf.date_format(sf.from_utc_timestamp(sf.current_timestamp(), tz), timestamp_format).cast("TIMESTAMP")


def clean_spaces_and_tabs(dataframe: DataFrame, cols: list[str] | None = None) -> DataFrame:
    """Removes spaces and tabs from string columns and trims whitespace. Converts empty strings to None.

    Args:
        dataframe: Input Spark DataFrame.
        cols: List of column names to clean. If None, cleans all string columns.

    Returns:
        New DataFrame with cleaned string columns.
    """
    if not cols:
        cols = dataframe.columns

    dataframe = dataframe.withColumns(
        {
            col_name: sf.when(sf.trim(sf.regexp_replace(sf.col(col_name), r"\s+", "")) == "", None).otherwise(
                sf.trim(sf.regexp_replace(sf.col(col_name), r"\s+", ""))
            )
            for col_name in cols
            if isinstance(dataframe.schema[col_name].dataType, StringType)
        }
    )
    return dataframe


def safe_isin_filter(column_name: str, filter_values: list[Any]) -> Column:
    """Filters a column based on a list of values. If the list is empty, returns a True column.

    Args:
        column_name: Name of the column to filter.
        filter_values: List of values to filter the column.

    Returns:
        Spark column with the filtered column.
    """
    if not filter_values:
        return sf.lit(True)
    return sf.col(column_name).isin(filter_values)


def safe_notin_filter(column_name: str, filter_values: list[Any]) -> Column:
    """Filters a column based on a list of values. If the list is empty, returns a True column.

    Args:
        column_name: Name of the column to filter.
        filter_values: List of values to filter the column.

    Returns:
        Spark column with the filtered column.
    """
    if not filter_values:
        return sf.lit(True)
    return ~sf.col(column_name).isin(filter_values)


def get_match_flag_null_condition(col1: str, col2: str, fallback_value: str = "FALSE") -> Column:
    """Returns a column with a match flag based on comparison of two columns.

    Args:
        col1: First column to compare.
        col2: Second column to compare.
        fallback_value: Fallback value to return if columns don't match.

    Returns:
        Spark column with the match flag.
    """
    return sf.expr(
        f"""
        CASE 
            WHEN {col1} IS NULL THEN {fallback_value}
            WHEN {col1} IS NOT NULL AND {col2} IS NULL THEN TRUE
            WHEN {col1} IS NOT NULL AND {col2} IS NOT NULL AND {col1} = {col2} THEN {fallback_value}
            WHEN {col1} IS NOT NULL AND {col2} IS NOT NULL AND {col1} != {col2} THEN TRUE
            ELSE {fallback_value}
        END
    """
    )
