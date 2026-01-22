import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pyspark.sql import DataFrame
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

from demo_comfandi_project.flows.demo_comfandi.load import load


@pytest.fixture
def mock_vars_resource():
    """Create mock VarsResource."""
    mock_vars = MagicMock()
    mock_vars.vars.output.table_id = "test.output.table"
    mock_vars.vars.num_partitions.min_global = 10
    return mock_vars


def test_load_with_partitions(spark, mock_vars_resource):
    """Test load operation with partitioning."""
    input_data = [("1", 1000), ("2", 2000), ("3", 3000)]
    input_df = spark.createDataFrame(
        input_data,
        schema=["id", "amount"]
    )

    mock_repartitioned_df = MagicMock()
    mock_repartitioned_df.write = MagicMock()
    mock_write_mode = MagicMock()
    mock_write_option = MagicMock()
    mock_write_save = MagicMock()
    mock_repartitioned_df.write.mode.return_value = mock_write_option
    mock_write_option.option.return_value = mock_write_save
    mock_write_save.saveAsTable.return_value = None

    with patch.object(input_df, 'repartition', return_value=mock_repartitioned_df) as mock_repartition:
        load(
            job_id="test_job_1",
            spark=spark,
            vars_instance=mock_vars_resource,
            transformed_data=input_df
        )

        mock_repartition.assert_called_once_with(10)
        mock_repartitioned_df.write.mode.assert_called_once_with("overwrite")
        mock_write_option.option.assert_called_once_with("overwriteSchema", "true")
        mock_write_save.saveAsTable.assert_called_once_with("test.output.table")


def test_load_without_partitions(spark, mock_vars_resource):
    """Test load operation without partitioning when num_partitions is None."""
    mock_vars_resource.vars.num_partitions.min_global = None
    
    input_data = [("1", 1000), ("2", 2000)]
    input_df = spark.createDataFrame(
        input_data,
        schema=["id", "amount"]
    )

    mock_write_mode = MagicMock()
    mock_write_option = MagicMock()
    mock_write_save = MagicMock()
    mock_write_mode.mode.return_value = mock_write_option
    mock_write_option.option.return_value = mock_write_save
    mock_write_save.saveAsTable.return_value = None

    original_write = input_df.write
    try:
        type(input_df).write = PropertyMock(return_value=mock_write_mode)
        load(
            job_id="test_job_2",
            spark=spark,
            vars_instance=mock_vars_resource,
            transformed_data=input_df
        )

        mock_write_mode.mode.assert_called_once_with("overwrite")
        mock_write_option.option.assert_called_once_with("overwriteSchema", "true")
        mock_write_save.saveAsTable.assert_called_once_with("test.output.table")
    finally:
        type(input_df).write = original_write


def test_load_empty_dataframe(spark, mock_vars_resource):
    """Test load operation with empty DataFrame."""
    schema = StructType([
        StructField("id", StringType(), True),
        StructField("amount", IntegerType(), True)
    ])
    empty_df = spark.createDataFrame([], schema=schema)

    mock_repartitioned_df = MagicMock()
    mock_repartitioned_df.write = MagicMock()
    mock_write_mode = MagicMock()
    mock_write_option = MagicMock()
    mock_write_save = MagicMock()
    mock_repartitioned_df.write.mode.return_value = mock_write_option
    mock_write_option.option.return_value = mock_write_save
    mock_write_save.saveAsTable.return_value = None

    with patch.object(empty_df, 'repartition', return_value=mock_repartitioned_df) as mock_repartition:
        load(
            job_id="test_job_3",
            spark=spark,
            vars_instance=mock_vars_resource,
            transformed_data=empty_df
        )

        mock_repartition.assert_called_once_with(10)
        mock_repartitioned_df.write.mode.assert_called_once_with("overwrite")
        mock_write_option.option.assert_called_once_with("overwriteSchema", "true")
        mock_write_save.saveAsTable.assert_called_once_with("test.output.table")


def test_load_with_zero_partitions(spark, mock_vars_resource):
    """Test load operation when num_partitions is 0 (should not repartition)."""
    mock_vars_resource.vars.num_partitions.min_global = 0
    
    input_data = [("1", 1000)]
    input_df = spark.createDataFrame(
        input_data,
        schema=["id", "amount"]
    )

    mock_write_mode = MagicMock()
    mock_write_option = MagicMock()
    mock_write_save = MagicMock()
    mock_write_mode.mode.return_value = mock_write_option
    mock_write_option.option.return_value = mock_write_save
    mock_write_save.saveAsTable.return_value = None

    original_write = input_df.write
    try:
        type(input_df).write = PropertyMock(return_value=mock_write_mode)
        load(
            job_id="test_job_4",
            spark=spark,
            vars_instance=mock_vars_resource,
            transformed_data=input_df
        )

        mock_write_mode.mode.assert_called_once_with("overwrite")
        mock_write_option.option.assert_called_once_with("overwriteSchema", "true")
        mock_write_save.saveAsTable.assert_called_once_with("test.output.table")
    finally:
        type(input_df).write = original_write
