import pytest
from unittest.mock import MagicMock, patch
from pyspark.sql import DataFrame
from pyspark.testing.utils import assertDataFrameEqual
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

from demo_comfandi_project.flows.demo_comfandi.transform import transform


@pytest.fixture
def mock_vars_resource():
    """Create mock VarsResource."""
    mock_vars = MagicMock()
    mock_vars.vars.input.table_id = "test.input.table"
    mock_vars.vars.output.table_id = "test.output.table"
    return mock_vars


def test_transform_basic_cleaning(spark, mock_vars_resource):
    """Test basic transformation with deduplication."""
    input_data = [
        ("1", 1000),
        ("2", 2000),
        ("1", 1000),
        ("3", 3000)
    ]
    input_df = spark.createDataFrame(
        input_data,
        schema=["id", "amount"]
    )

    result = transform(
        job_id="test_job_1",
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=input_df
    )

    assert result.count() == 3
    assert "current_timestamp_dwh" in result.columns
    assert result.schema["current_timestamp_dwh"].dataType == TimestampType()


def test_transform_empty_dataframe(spark, mock_vars_resource):
    """Test transformation with empty DataFrame."""
    schema = StructType([
        StructField("id", StringType(), True),
        StructField("amount", IntegerType(), True)
    ])
    empty_df = spark.createDataFrame([], schema=schema)

    result = transform(
        job_id="test_job_2",
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=empty_df
    )

    assert result.count() == 0
    assert "current_timestamp_dwh" in result.columns


def test_transform_adds_metadata_column(spark, mock_vars_resource):
    """Test that transformation adds metadata timestamp column."""
    input_data = [("1", 1000), ("2", 2000)]
    input_df = spark.createDataFrame(
        input_data,
        schema=["id", "amount"]
    )

    result = transform(
        job_id="test_job_3",
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=input_df
    )

    assert "current_timestamp_dwh" in result.columns
    assert result.schema["current_timestamp_dwh"].dataType == TimestampType()
    
    rows = result.collect()
    for row in rows:
        assert row["current_timestamp_dwh"] is not None


def test_transform_preserves_original_columns(spark, mock_vars_resource):
    """Test that transformation preserves original columns."""
    input_data = [("1", 1000, "A"), ("2", 2000, "B")]
    input_df = spark.createDataFrame(
        input_data,
        schema=["id", "amount", "category"]
    )

    result = transform(
        job_id="test_job_4",
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=input_df
    )

    assert "id" in result.columns
    assert "amount" in result.columns
    assert "category" in result.columns
    assert "current_timestamp_dwh" in result.columns
    
    result_data = result.select("id", "amount", "category").collect()
    expected_data = input_df.collect()
    
    assert len(result_data) == len(expected_data)
    for i, row in enumerate(result_data):
        assert row["id"] == expected_data[i]["id"]
        assert row["amount"] == expected_data[i]["amount"]
        assert row["category"] == expected_data[i]["category"]


def test_transform_deduplication(spark, mock_vars_resource):
    """Test that transformation removes duplicates."""
    input_data = [
        ("1", 1000),
        ("1", 1000),
        ("1", 1000),
        ("2", 2000),
        ("2", 2000)
    ]
    input_df = spark.createDataFrame(
        input_data,
        schema=["id", "amount"]
    )

    result = transform(
        job_id="test_job_5",
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=input_df
    )

    assert result.count() == 2
    
    result_data = result.select("id", "amount").collect()
    ids = [row["id"] for row in result_data]
    assert set(ids) == {"1", "2"}
