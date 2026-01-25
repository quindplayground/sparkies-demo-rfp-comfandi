import pytest
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.testing.utils import assertDataFrameEqual
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

from demo_comfandi_project.libs.common_patterns import (
    current_timestamp_with_tz,
    clean_spaces_and_tabs,
)

from unittest.mock import MagicMock

from demo_comfandi_project.libs.iceberg.utils.load_utils import load_overwrite


@pytest.fixture(scope="session")
def spark():
    spark = SparkSession.builder.master("local[1]").appName("unit-tests").getOrCreate()
    yield spark
    spark.stop()


def test_current_timestamp_with_tz(spark):
    # Preparar
    timestamp_format = "yyyy-MM-dd HH:mm:ss"
    tz = "America/New_York"

    # Ejecutar
    df = spark.createDataFrame([(1,)], ["id"])
    df = df.withColumn("timestamp", current_timestamp_with_tz(timestamp_format, tz))

    # Verificar
    assert df.select("timestamp").first()[0] is not None
    assert isinstance(df.select("timestamp").first()[0], datetime)


def test_clean_spaces_and_tabs_all_columns(spark):
    # Preparar
    input_data = [
        ("  test  ", "  hello  world  ", "123"),
        ("test\t\t", "hello\t\tworld", "456"),
        ("   ", "\t\t  \t", "789"),
        (None, None, "012"),
    ]
    input_schema = StructType(
        [
            StructField("col1", StringType(), True),
            StructField("col2", StringType(), True),
            StructField("col3", StringType(), True),
        ]
    )
    input_df = spark.createDataFrame(input_data, input_schema)

    expected_data = [
        ("test", "helloworld", "123"),
        ("test", "helloworld", "456"),
        (None, None, "789"),
        (None, None, "012"),
    ]
    expected_df = spark.createDataFrame(expected_data, input_schema)

    # Ejecutar
    result_df = clean_spaces_and_tabs(input_df)

    # Verificar
    assertDataFrameEqual(result_df, expected_df)


def test_clean_spaces_and_tabs_specific_columns(spark):
    # Preparar
    input_data = [
        ("  test  ", "  hello  world  ", "123"),
        ("test\t\t", "hello\t\tworld", "456"),
        ("   ", "\t\t  \t", "789"),
        (None, None, "012"),
    ]
    input_schema = StructType(
        [
            StructField("col1", StringType(), True),
            StructField("col2", StringType(), True),
            StructField("col3", StringType(), True),
        ]
    )
    input_df = spark.createDataFrame(input_data, input_schema)

    expected_data = [
        ("test", "  hello  world  ", "123"),
        ("test", "hello\t\tworld", "456"),
        (None, "\t\t  \t", "789"),
        (None, None, "012"),
    ]
    expected_df = spark.createDataFrame(expected_data, input_schema)

    # Ejecutar
    result_df = clean_spaces_and_tabs(input_df, cols=["col1"])

    # Verificar
    assertDataFrameEqual(result_df, expected_df)


def test_clean_spaces_and_tabs_mixed_types(spark):
    # Preparar
    input_data = [
        ("  test  ", datetime(2024, 1, 1)),
        ("test\t\t", datetime(2024, 1, 2)),
        ("   ", datetime(2024, 1, 3)),
        (None, datetime(2024, 1, 4)),
    ]
    input_schema = StructType(
        [
            StructField("col1", StringType(), True),
            StructField("col2", TimestampType(), True),
        ]
    )
    input_df = spark.createDataFrame(input_data, input_schema)

    expected_data = [
        ("test", datetime(2024, 1, 1)),
        ("test", datetime(2024, 1, 2)),
        (None, datetime(2024, 1, 3)),
        (None, datetime(2024, 1, 4)),
    ]
    expected_df = spark.createDataFrame(expected_data, input_schema)

    # Ejecutar
    result_df = clean_spaces_and_tabs(input_df)

    # Verificar
    assertDataFrameEqual(result_df, expected_df)


def test_load_to_iceberg_creates_table_when_not_exists():
    spark = MagicMock()
    dataframe = MagicMock()
    spark.catalog.tableExists.return_value = False

    repartitioned_df = MagicMock()
    dataframe.repartition.return_value = repartitioned_df
    writeTo = MagicMock()
    repartitioned_df.writeTo.return_value = writeTo
    writeTo.using.return_value = writeTo
    writeTo.tableProperty.return_value = writeTo

    load_overwrite(spark, dataframe, "test_table", num_partitions=2)

    spark.catalog.tableExists.assert_called_once_with("test_table")
    dataframe.repartition.assert_called_once_with(2)
    repartitioned_df.writeTo.assert_called_once_with("test_table")
    writeTo.using.assert_called_once_with("iceberg")
    # Verificar que se configuraron propiedades de merge-on-read
    expected_props = [
        ("write.merge.isolation-level", "serializable"),
        ("write.update.isolation-level", "serializable"),
        ("write.delete.isolation-level", "serializable"),
        ("write.spark.fanout.enabled", "true"),
        ("write.delete.mode", "merge-on-read"),
        ("write.update.mode", "merge-on-read"),
        ("write.merge.mode", "merge-on-read"),
        ("format-version", "2"),
    ]
    actual_calls = [tuple(call.args) for call in writeTo.tableProperty.call_args_list]
    assert actual_calls == expected_props
    writeTo.createOrReplace.assert_called_once()
    # Verifica que se llamen los procedimientos de limpieza
    assert spark.sql.call_count == 2


def test_load_to_iceberg_overwrites_partitions_when_table_exists():
    spark = MagicMock()
    dataframe = MagicMock()
    spark.catalog.tableExists.return_value = True

    repartitioned_df = MagicMock()
    dataframe.repartition.return_value = repartitioned_df
    writeTo = MagicMock()
    repartitioned_df.writeTo.return_value = writeTo
    writeTo.using.return_value = writeTo
    writeTo.option.return_value = writeTo

    load_overwrite(spark, dataframe, "test_table", num_partitions=3)

    spark.catalog.tableExists.assert_called_once_with("test_table")
    dataframe.repartition.assert_called_once_with(3)
    repartitioned_df.writeTo.assert_called_once_with("test_table")
    writeTo.using.assert_called_once_with("iceberg")
    writeTo.option.assert_called_once_with("overwriteSchema", "true")
    writeTo.overwritePartitions.assert_called_once()
    # Verifica que se llamen los procedimientos de limpieza
    assert spark.sql.call_count == 2
