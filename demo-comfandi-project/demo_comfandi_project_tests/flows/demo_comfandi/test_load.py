import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pyspark.sql import SparkSession
from pyspark.testing.utils import assertDataFrameEqual
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructType,
    StructField,
)

from demo_comfandi_project.flows.demo_comfandi.load import load


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
    mock_vars.vars.num_partitions.min_global = None
    return mock_vars


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
        (
            2024,
            2,
            "CCF002",
            20,
            200,
            160,
            10,
            20,
            10,
            0,
            40,
            240,
            "2024-02",
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


def test_load_overwrite_mode(spark, mock_vars_resource, sample_transformed_data):
    """Test that load uses overwrite mode."""
    job_id = "test_job_123"

    mock_write = MagicMock()
    mock_mode = MagicMock(return_value=mock_write)
    mock_write_obj = MagicMock()
    mock_write_obj.mode = mock_mode

    with patch.object(type(sample_transformed_data), "write", PropertyMock(return_value=mock_write_obj)):
        load(
            job_id=job_id,
            spark=spark,
            vars_instance=mock_vars_resource,
            transformed_data=sample_transformed_data,
        )

        mock_mode.assert_called_once_with("overwrite")
        mock_write.saveAsTable.assert_called_once_with("test.output.table")


def test_load_with_partitions(spark, sample_transformed_data):
    """Test that load repartitions when num_partitions is configured."""
    mock_vars = MagicMock()
    mock_vars.vars.input.table_id = "test.input.table"
    mock_vars.vars.output.table_id = "test.output.table"
    mock_vars.vars.num_partitions.min_global = 4

    job_id = "test_job_123"

    with patch.object(sample_transformed_data, "repartition") as mock_repartition:
        mock_repartitioned = MagicMock()
        mock_repartition.return_value = mock_repartitioned
        mock_write = MagicMock()
        mock_repartitioned.write = MagicMock()
        mock_repartitioned.write.mode = MagicMock(return_value=mock_write)
        mock_write.saveAsTable = MagicMock()

        load(
            job_id=job_id,
            spark=spark,
            vars_instance=mock_vars,
            transformed_data=sample_transformed_data,
        )

        mock_repartition.assert_called_once_with(4)
        mock_write.saveAsTable.assert_called_once_with("test.output.table")


def test_load_without_partitions(spark, mock_vars_resource, sample_transformed_data):
    """Test that load does not repartition when num_partitions is None."""
    job_id = "test_job_123"

    mock_write = MagicMock()
    mock_mode = MagicMock(return_value=mock_write)
    mock_write_obj = MagicMock()
    mock_write_obj.mode = mock_mode

    with patch.object(sample_transformed_data, "repartition") as mock_repartition:
        with patch.object(type(sample_transformed_data), "write", PropertyMock(return_value=mock_write_obj)):
            load(
                job_id=job_id,
                spark=spark,
                vars_instance=mock_vars_resource,
                transformed_data=sample_transformed_data,
            )

            mock_repartition.assert_not_called()
            mock_mode.assert_called_once_with("overwrite")
            mock_write.saveAsTable.assert_called_once_with("test.output.table")


def test_load_empty_dataframe(spark, mock_vars_resource):
    """Test load with empty DataFrame."""
    schema = StructType(
        [
            StructField("a_o", IntegerType(), True),
            StructField("mes", IntegerType(), True),
            StructField("ccf", StringType(), True),
        ]
    )
    empty_df = spark.createDataFrame([], schema)
    job_id = "test_job_123"

    mock_write = MagicMock()
    mock_mode = MagicMock(return_value=mock_write)
    mock_write_obj = MagicMock()
    mock_write_obj.mode = mock_mode

    with patch.object(type(empty_df), "write", PropertyMock(return_value=mock_write_obj)):
        load(
            job_id=job_id,
            spark=spark,
            vars_instance=mock_vars_resource,
            transformed_data=empty_df,
        )

        mock_mode.assert_called_once_with("overwrite")
        mock_write.saveAsTable.assert_called_once_with("test.output.table")
