import pytest
from unittest.mock import MagicMock, patch
from pyspark.sql import DataFrame
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from pyspark.testing.utils import assertDataFrameEqual, assertSchemaEqual

from demo_comfandi_project.flows.demo_comfandi.extract import extract


@pytest.fixture
def mock_vars_resource():
    """Create mock VarsResource."""
    mock_vars = MagicMock()
    mock_vars.vars.input.table_id = "test.input.table"
    return mock_vars


def test_extract_full_load(spark, mock_vars_resource):
    """Test full extraction from source table."""
    expected_data = [("1", 1000), ("2", 3000)]
    expected_df = spark.createDataFrame(
        expected_data,
        schema=["id", "amount"]
    )

    with patch.object(spark, 'table') as mock_table:
        mock_table.return_value = expected_df

        result = extract(spark, mock_vars_resource)

        assertDataFrameEqual(result, expected_df)
        assertSchemaEqual(result.schema, expected_df.schema)
        mock_table.assert_called_once_with("test.input.table")


def test_extract_empty_source(spark, mock_vars_resource):
    """Test extraction with empty source table."""
    schema = StructType([
        StructField("id", StringType(), True),
        StructField("amount", IntegerType(), True)
    ])
    empty_df = spark.createDataFrame([], schema=schema)

    with patch.object(spark, 'table') as mock_table:
        mock_table.return_value = empty_df

        result = extract(spark, mock_vars_resource)

        assertDataFrameEqual(result, empty_df)
        assert result.count() == 0


def test_extract_with_different_schema(spark, mock_vars_resource):
    """Test extraction with different column types."""
    expected_data = [
        ("1", 1000, 0.5),
        ("2", 3000, 1.5)
    ]
    expected_df = spark.createDataFrame(
        expected_data,
        schema=["id", "amount", "ratio"]
    )

    with patch.object(spark, 'table') as mock_table:
        mock_table.return_value = expected_df

        result = extract(spark, mock_vars_resource)

        assertDataFrameEqual(result, expected_df)
        assertSchemaEqual(result.schema, expected_df.schema)
