import pytest
from unittest.mock import MagicMock, patch
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructType,
    StructField,
)

from demo_comfandi_project.flows.demo_comfandi.job import demo_comfandi_job
from demo_comfandi_project.libs.runner.types import Status


@pytest.fixture(scope="session")
def spark():
    """Create SparkSession for testing (shared across tests)."""
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    yield spark
    spark.stop()


@pytest.fixture
def mock_vars_resource():
    """Create mock VarsResource."""
    mock_vars = MagicMock()
    mock_vars.vars.input.table_id = "test.input.table"
    mock_vars.vars.output.table_id = "test.output.table"
    mock_vars.vars.get.return_value = "demo_comfandi"
    return mock_vars


@pytest.fixture
def sample_extracted_data(spark):
    """Create sample extracted DataFrame."""
    data = [
        (2024, 1, "CCF001", 10, 100, 80, 5, 10, 5, 0, 20, 120),
    ]
    schema = StructType(
        [
            StructField("a_o", IntegerType(), True),
            StructField("mes", IntegerType(), True),
            StructField("ccf", StringType(), True),
            StructField("empresas_afiliadas", IntegerType(), True),
            StructField("total_afiliados_cajas", IntegerType(), True),
            StructField("trabajadores_afiliados", IntegerType(), True),
            StructField("afiliados_facultativos", IntegerType(), True),
            StructField("afiliados_pensionados", IntegerType(), True),
            StructField("afiliados_fidelidad", IntegerType(), True),
            StructField("no_afiliados_con_derecho", IntegerType(), True),
            StructField("personas_cargo_2", IntegerType(), True),
            StructField("total_poblaci_n_cubierta", IntegerType(), True),
        ]
    )
    return spark.createDataFrame(data, schema)


@pytest.fixture
def sample_transformed_data(spark):
    """Create sample transformed DataFrame."""
    data = [
        (
            2024,
            1,
            "CCF001",
            10,
            100,
            80,
            5,
            10,
            5,
            0,
            20,
            120,
            "2024-01",
            None,
            "test_job_123",
            True,
            True,
            True,
            True,
        ),
    ]
    schema = StructType(
        [
            StructField("a_o", IntegerType(), True),
            StructField("mes", IntegerType(), True),
            StructField("ccf", StringType(), True),
            StructField("empresas_afiliadas", IntegerType(), True),
            StructField("total_afiliados_cajas", IntegerType(), True),
            StructField("trabajadores_afiliados", IntegerType(), True),
            StructField("afiliados_facultativos", IntegerType(), True),
            StructField("afiliados_pensionados", IntegerType(), True),
            StructField("afiliados_fidelidad", IntegerType(), True),
            StructField("no_afiliados_con_derecho", IntegerType(), True),
            StructField("personas_cargo_2", IntegerType(), True),
            StructField("total_poblaci_n_cubierta", IntegerType(), True),
            StructField("year_month", StringType(), True),
            StructField("ingestion_ts", StringType(), True),
            StructField("job_run_id", StringType(), True),
            StructField("dq_is_valid_month", StringType(), True),
            StructField("dq_non_negative", StringType(), True),
            StructField("dq_total_cubierta_consistente", StringType(), True),
            StructField("dq_key_not_null", StringType(), True),
        ]
    )
    return spark.createDataFrame(data, schema)


@patch("demo_comfandi_project.flows.demo_comfandi.job.load")
@patch("demo_comfandi_project.flows.demo_comfandi.job.transform")
@patch("demo_comfandi_project.flows.demo_comfandi.job.extract")
def test_job_success(
    mock_extract,
    mock_transform,
    mock_load,
    spark,
    mock_vars_resource,
    sample_extracted_data,
    sample_transformed_data,
):
    """Test successful job execution."""
    mock_extract.return_value = sample_extracted_data
    mock_transform.return_value = sample_transformed_data
    mock_load.return_value = None

    result = demo_comfandi_job(spark, mock_vars_resource)

    assert isinstance(result, Status)
    assert result.status_value == "OK"
    assert "completed successfully" in result.message.lower()

    mock_extract.assert_called_once()
    mock_transform.assert_called_once()
    mock_load.assert_called_once()


@patch("demo_comfandi_project.flows.demo_comfandi.job.load")
@patch("demo_comfandi_project.flows.demo_comfandi.job.transform")
@patch("demo_comfandi_project.flows.demo_comfandi.job.extract")
def test_job_calls_extract_with_correct_params(
    mock_extract,
    mock_transform,
    mock_load,
    spark,
    mock_vars_resource,
    sample_extracted_data,
    sample_transformed_data,
):
    """Test that extract is called with correct parameters."""
    mock_extract.return_value = sample_extracted_data
    mock_transform.return_value = sample_transformed_data
    mock_load.return_value = None

    demo_comfandi_job(spark, mock_vars_resource)

    mock_extract.assert_called_once_with(
        spark=spark,
        vars_instance=mock_vars_resource,
    )


@patch("demo_comfandi_project.flows.demo_comfandi.job.load")
@patch("demo_comfandi_project.flows.demo_comfandi.job.transform")
@patch("demo_comfandi_project.flows.demo_comfandi.job.extract")
def test_job_calls_transform_with_correct_params(
    mock_extract,
    mock_transform,
    mock_load,
    spark,
    mock_vars_resource,
    sample_extracted_data,
    sample_transformed_data,
):
    """Test that transform is called with correct parameters."""
    mock_extract.return_value = sample_extracted_data
    mock_transform.return_value = sample_transformed_data
    mock_load.return_value = None

    demo_comfandi_job(spark, mock_vars_resource)

    mock_transform.assert_called_once()
    call_kwargs = mock_transform.call_args[1]
    assert call_kwargs["spark"] == spark
    assert call_kwargs["vars_instance"] == mock_vars_resource
    assert call_kwargs["extracted_data"] == sample_extracted_data
    assert "job_id" in call_kwargs


@patch("demo_comfandi_project.flows.demo_comfandi.job.load")
@patch("demo_comfandi_project.flows.demo_comfandi.job.transform")
@patch("demo_comfandi_project.flows.demo_comfandi.job.extract")
def test_job_calls_load_with_correct_params(
    mock_extract,
    mock_transform,
    mock_load,
    spark,
    mock_vars_resource,
    sample_extracted_data,
    sample_transformed_data,
):
    """Test that load is called with correct parameters."""
    mock_extract.return_value = sample_extracted_data
    mock_transform.return_value = sample_transformed_data
    mock_load.return_value = None

    demo_comfandi_job(spark, mock_vars_resource)

    mock_load.assert_called_once()
    call_kwargs = mock_load.call_args[1]
    assert call_kwargs["spark"] == spark
    assert call_kwargs["vars_instance"] == mock_vars_resource
    assert call_kwargs["transformed_data"] == sample_transformed_data
    assert "job_id" in call_kwargs


@patch("demo_comfandi_project.flows.demo_comfandi.job.load")
@patch("demo_comfandi_project.flows.demo_comfandi.job.transform")
@patch("demo_comfandi_project.flows.demo_comfandi.job.extract")
def test_job_returns_status_ok_on_success(
    mock_extract,
    mock_transform,
    mock_load,
    spark,
    mock_vars_resource,
    sample_extracted_data,
    sample_transformed_data,
):
    """Test that job returns Status with OK status_value on success."""
    mock_extract.return_value = sample_extracted_data
    mock_transform.return_value = sample_transformed_data
    mock_load.return_value = None

    result = demo_comfandi_job(spark, mock_vars_resource)

    assert result.status_value == "OK"
    assert isinstance(result, Status)
