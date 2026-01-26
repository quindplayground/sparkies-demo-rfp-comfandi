import pytest
from unittest.mock import MagicMock
from pyspark.sql import SparkSession
from pyspark.testing.utils import assertDataFrameEqual, assertSchemaEqual
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructType,
    StructField,
    TimestampType,
    BooleanType,
)

from demo_comfandi_project.flows.demo_comfandi.transform import transform


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
    return mock_vars


@pytest.fixture
def sample_extracted_data(spark):
    """Create sample extracted DataFrame."""
    data = [
        (
            2024,
            1,
            "  ccf001  ",
            10,
            100,
            80,
            5,
            10,
            5,
            0,
            20,
            120,
        ),
        (
            2024,
            2,
            "ccf002",
            20,
            200,
            160,
            10,
            20,
            10,
            0,
            40,
            240,
        ),
        (
            2024,
            13,
            "ccf003",
            30,
            300,
            240,
            15,
            30,
            15,
            0,
            60,
            360,
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
        ]
    )
    return spark.createDataFrame(data, schema)


def test_transform_cleans_ccf_field(spark, mock_vars_resource, sample_extracted_data):
    """Test that CCF field is cleaned (trimmed, uppercased, spaces collapsed)."""
    job_id = "test_job_123"

    result = transform(
        job_id=job_id,
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=sample_extracted_data,
    )

    ccf_values = [row["ccf"] for row in result.select("ccf").collect()]
    assert "CCF001" in ccf_values
    assert "CCF002" in ccf_values
    assert "CCF003" in ccf_values
    assert "  ccf001  " not in ccf_values


def test_transform_adds_metadata_columns(spark, mock_vars_resource, sample_extracted_data):
    """Test that metadata columns (year_month, ingestion_ts, job_run_id) are added."""
    job_id = "test_job_123"

    result = transform(
        job_id=job_id,
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=sample_extracted_data,
    )

    assert "year_month" in result.columns
    assert "ingestion_ts" in result.columns
    assert "job_run_id" in result.columns

    year_month_values = [row["year_month"] for row in result.select("year_month").collect()]
    assert "2024-01" in year_month_values
    assert "2024-02" in year_month_values

    job_run_ids = [row["job_run_id"] for row in result.select("job_run_id").collect()]
    assert all(jid == job_id for jid in job_run_ids)


def test_transform_adds_dq_flags(spark, mock_vars_resource, sample_extracted_data):
    """Test that data quality flags are added."""
    job_id = "test_job_123"

    result = transform(
        job_id=job_id,
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=sample_extracted_data,
    )

    assert "dq_is_valid_month" in result.columns
    assert "dq_non_negative" in result.columns
    assert "dq_total_cubierta_consistente" in result.columns
    assert "dq_key_not_null" in result.columns

    dq_rows = result.select(
        "mes", "dq_is_valid_month", "dq_non_negative", "dq_total_cubierta_consistente"
    ).collect()

    for row in dq_rows:
        if row["mes"] == 13:
            assert row["dq_is_valid_month"] is False
        else:
            assert row["dq_is_valid_month"] is True


def test_transform_deduplicates_by_natural_key(spark, mock_vars_resource):
    """Test that duplicates are removed by natural key (a_o, mes, ccf)."""
    data = [
        (2024, 1, "CCF001", 10, 100, 80, 5, 10, 5, 0, 20, 120),
        (2024, 1, "CCF001", 15, 150, 120, 7, 15, 7, 0, 30, 150),
        (2024, 2, "CCF002", 20, 200, 160, 10, 20, 10, 0, 40, 240),
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
    extracted_data = spark.createDataFrame(data, schema)
    job_id = "test_job_123"

    result = transform(
        job_id=job_id,
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=extracted_data,
    )

    assert result.count() == 2

    keys = [(row["a_o"], row["mes"], row["ccf"]) for row in result.select("a_o", "mes", "ccf").collect()]
    assert (2024, 1, "CCF001") in keys
    assert (2024, 2, "CCF002") in keys
    assert len(set(keys)) == 2

    expected_schema = StructType(
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
            StructField("ingestion_ts", TimestampType(), True),
            StructField("job_run_id", StringType(), False),
            StructField("dq_is_valid_month", BooleanType(), True),
            StructField("dq_non_negative", BooleanType(), True),
            StructField("dq_total_cubierta_consistente", BooleanType(), True),
            StructField("dq_key_not_null", BooleanType(), False),
        ]
    )
    assertSchemaEqual(result.schema, expected_schema)


def test_transform_handles_empty_dataframe(spark, mock_vars_resource):
    """Test transformation with empty DataFrame."""
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
    empty_df = spark.createDataFrame([], schema)
    job_id = "test_job_123"

    result = transform(
        job_id=job_id,
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=empty_df,
    )

    assert result.count() == 0
    assert "year_month" in result.columns
    assert "ingestion_ts" in result.columns
    assert "job_run_id" in result.columns

    expected_schema = StructType(
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
            StructField("ingestion_ts", TimestampType(), True),
            StructField("job_run_id", StringType(), False),
            StructField("dq_is_valid_month", BooleanType(), True),
            StructField("dq_non_negative", BooleanType(), True),
            StructField("dq_total_cubierta_consistente", BooleanType(), True),
            StructField("dq_key_not_null", BooleanType(), False),
        ]
    )
    assertSchemaEqual(result.schema, expected_schema)


def test_transform_dq_total_cubierta_consistente(spark, mock_vars_resource):
    """Test that dq_total_cubierta_consistente flag works correctly."""
    data = [
        (2024, 1, "CCF001", 10, 100, 80, 5, 10, 5, 0, 20, 120),
        (2024, 2, "CCF002", 20, 200, 160, 10, 20, 10, 0, 40, 250),
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
    extracted_data = spark.createDataFrame(data, schema)
    job_id = "test_job_123"

    result = transform(
        job_id=job_id,
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=extracted_data,
    )

    dq_rows = result.select("ccf", "dq_total_cubierta_consistente").collect()
    for row in dq_rows:
        if row["ccf"] == "CCF001":
            assert row["dq_total_cubierta_consistente"] is True
        elif row["ccf"] == "CCF002":
            assert row["dq_total_cubierta_consistente"] is False


def test_transform_dq_non_negative(spark, mock_vars_resource):
    """Test that dq_non_negative flag works correctly."""
    data = [
        (2024, 1, "CCF001", 10, 100, 80, 5, 10, 5, 0, 20, 120),
        (2024, 2, "CCF002", -5, 200, 160, 10, 20, 10, 0, 40, 240),
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
    extracted_data = spark.createDataFrame(data, schema)
    job_id = "test_job_123"

    result = transform(
        job_id=job_id,
        spark=spark,
        vars_instance=mock_vars_resource,
        extracted_data=extracted_data,
    )

    dq_rows = result.select("ccf", "dq_non_negative").collect()
    for row in dq_rows:
        if row["ccf"] == "CCF001":
            assert row["dq_non_negative"] is True
        elif row["ccf"] == "CCF002":
            assert row["dq_non_negative"] is False
