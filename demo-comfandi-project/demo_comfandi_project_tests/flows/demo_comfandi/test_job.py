import pytest
from unittest.mock import MagicMock, patch
from pyspark.sql import DataFrame
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

from demo_comfandi_project.flows.demo_comfandi.job import demo_comfandi_job
from demo_comfandi_project.libs.runner.types import Status


@pytest.fixture
def mock_vars_resource():
    """Create mock VarsResource."""
    mock_vars = MagicMock()
    mock_vars.vars.input.table_id = "test.input.table"
    mock_vars.vars.output.table_id = "test.output.table"
    mock_vars.vars.get.return_value = "demo_comfandi"
    mock_vars.vars.num_partitions.min_global = 10
    return mock_vars


def test_job_full_pipeline_success(spark, mock_vars_resource):
    """Test full ETL pipeline execution."""
    extracted_data = spark.createDataFrame(
        [("1", 1000), ("2", 2000)],
        schema=["id", "amount"]
    )

    with patch('demo_comfandi_project.flows.demo_comfandi.job.extract') as mock_extract, \
         patch('demo_comfandi_project.flows.demo_comfandi.job.transform') as mock_transform, \
         patch('demo_comfandi_project.flows.demo_comfandi.job.load') as mock_load:
        
        mock_extract.return_value = extracted_data
        mock_transform.return_value = extracted_data
        mock_load.return_value = None

        result = demo_comfandi_job(spark, mock_vars_resource)

        assert isinstance(result, Status)
        assert result.status_value == "OK"
        assert "completed successfully" in result.message.lower()
        
        mock_extract.assert_called_once_with(
            spark=spark,
            vars_instance=mock_vars_resource
        )
        mock_transform.assert_called_once()
        mock_load.assert_called_once()


def test_job_returns_status_object(spark, mock_vars_resource):
    """Test that job returns Status object with correct values."""
    extracted_data = spark.createDataFrame(
        [("1", 1000)],
        schema=["id", "amount"]
    )

    with patch('demo_comfandi_project.flows.demo_comfandi.job.extract') as mock_extract, \
         patch('demo_comfandi_project.flows.demo_comfandi.job.transform') as mock_transform, \
         patch('demo_comfandi_project.flows.demo_comfandi.job.load') as mock_load:
        
        mock_extract.return_value = extracted_data
        mock_transform.return_value = extracted_data
        mock_load.return_value = None

        result = demo_comfandi_job(spark, mock_vars_resource)

        assert isinstance(result, Status)
        assert result.status_value == "OK"
        assert result.code == 200


def test_job_calls_all_steps(spark, mock_vars_resource):
    """Test that job calls extract, transform, and load in sequence."""
    extracted_data = spark.createDataFrame(
        [("1", 1000)],
        schema=["id", "amount"]
    )

    with patch('demo_comfandi_project.flows.demo_comfandi.job.extract') as mock_extract, \
         patch('demo_comfandi_project.flows.demo_comfandi.job.transform') as mock_transform, \
         patch('demo_comfandi_project.flows.demo_comfandi.job.load') as mock_load:
        
        mock_extract.return_value = extracted_data
        mock_transform.return_value = extracted_data
        mock_load.return_value = None

        demo_comfandi_job(spark, mock_vars_resource)

        assert mock_extract.called
        assert mock_transform.called
        assert mock_load.called
        
        extract_call_args = mock_extract.call_args
        assert extract_call_args.kwargs['spark'] == spark
        assert extract_call_args.kwargs['vars_instance'] == mock_vars_resource
        
        transform_call_args = mock_transform.call_args
        assert transform_call_args.kwargs['spark'] == spark
        assert transform_call_args.kwargs['vars_instance'] == mock_vars_resource
        assert transform_call_args.kwargs['extracted_data'] == extracted_data
        
        load_call_args = mock_load.call_args
        assert load_call_args.kwargs['spark'] == spark
        assert load_call_args.kwargs['vars_instance'] == mock_vars_resource
        assert load_call_args.kwargs['transformed_data'] == extracted_data


def test_job_with_empty_data(spark, mock_vars_resource):
    """Test job execution with empty extracted data."""
    schema = StructType([
        StructField("id", StringType(), True),
        StructField("amount", IntegerType(), True)
    ])
    empty_df = spark.createDataFrame([], schema=schema)

    with patch('demo_comfandi_project.flows.demo_comfandi.job.extract') as mock_extract, \
         patch('demo_comfandi_project.flows.demo_comfandi.job.transform') as mock_transform, \
         patch('demo_comfandi_project.flows.demo_comfandi.job.load') as mock_load:
        
        mock_extract.return_value = empty_df
        mock_transform.return_value = empty_df
        mock_load.return_value = None

        result = demo_comfandi_job(spark, mock_vars_resource)

        assert isinstance(result, Status)
        assert result.status_value == "OK"
        mock_extract.assert_called_once()
        mock_transform.assert_called_once()
        mock_load.assert_called_once()
