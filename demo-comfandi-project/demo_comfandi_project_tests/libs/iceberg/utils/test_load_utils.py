from unittest.mock import Mock, patch
from pyspark.sql import SparkSession

from demo_comfandi_project.libs.iceberg.utils.load_utils import load_overwrite


def test_load_overwrite_basic_flow(spark: SparkSession):
    df = spark.createDataFrame([(1, "a")], ["id", "val"])  # type: ignore
    with patch.object(df, "writeTo") as mock_write_to, patch.object(
        spark, "sql"
    ) as mock_sql, patch.object(spark.catalog, "tableExists") as mock_exists:
        mock_exists.return_value = True  # Tabla existe, usa overwritePartitions
        mock_writer = Mock()
        mock_write_to.return_value = mock_writer
        mock_writer.using.return_value = mock_writer
        mock_writer.overwritePartitions.return_value = mock_writer
        mock_writer.tableProperty.return_value = mock_writer
        mock_writer.createOrReplace.return_value = mock_writer

        load_overwrite(spark, df, "test_table")

        mock_write_to.assert_called_once_with("test_table")
        mock_writer.using.assert_called_once_with("iceberg")
        # Verificar que se llama expire_snapshots
        mock_sql.assert_called()


def test_load_overwrite_with_partitions(spark: SparkSession):
    df = spark.createDataFrame([(1, "a")], ["id", "val"])  # type: ignore
    with patch.object(df, "repartition") as mock_repartition, patch.object(
        df, "writeTo"
    ) as mock_write_to, patch.object(spark, "sql") as _mock_sql, patch.object(
        spark.catalog, "tableExists"
    ) as mock_exists:
        mock_exists.return_value = True
        mock_repartition.return_value = df
        mock_writer = Mock()
        mock_write_to.return_value = mock_writer
        mock_writer.using.return_value = mock_writer
        mock_writer.overwritePartitions.return_value = mock_writer
        mock_writer.tableProperty.return_value = mock_writer
        mock_writer.createOrReplace.return_value = mock_writer

        load_overwrite(spark, df, "test_table", num_partitions=4)

        mock_repartition.assert_called_once_with(4)


def test_load_overwrite_with_expire_snapshots(spark: SparkSession):
    df = spark.createDataFrame([(1, "a")], ["id", "val"])  # type: ignore
    with patch.object(df, "writeTo") as mock_write_to, patch.object(
        spark, "sql"
    ) as mock_sql, patch.object(spark.catalog, "tableExists") as mock_exists:
        mock_exists.return_value = True
        mock_writer = Mock()
        mock_write_to.return_value = mock_writer
        mock_writer.using.return_value = mock_writer
        mock_writer.overwritePartitions.return_value = mock_writer
        mock_writer.tableProperty.return_value = mock_writer
        mock_writer.createOrReplace.return_value = mock_writer

        load_overwrite(spark, df, "test_table", expire_snapshots=True)

        # Verificar que se llama expire_snapshots
        mock_sql.assert_called()


def test_load_overwrite_create_new_table(spark: SparkSession):
    df = spark.createDataFrame([(1, "a")], ["id", "val"])  # type: ignore
    with patch.object(df, "writeTo") as mock_write_to, patch.object(
        spark, "sql"
    ) as _mock_sql, patch.object(spark.catalog, "tableExists") as mock_exists:
        mock_exists.return_value = False  # Tabla no existe, usa createOrReplace
        mock_writer = Mock()
        mock_write_to.return_value = mock_writer
        mock_writer.using.return_value = mock_writer
        mock_writer.tableProperty.return_value = mock_writer
        mock_writer.createOrReplace.return_value = mock_writer

        load_overwrite(spark, df, "test_table")

        mock_write_to.assert_called_once_with("test_table")
        mock_writer.using.assert_called_once_with("iceberg")
        mock_writer.createOrReplace.assert_called_once()
        # No debe llamar overwritePartitions para tabla nueva
        mock_writer.overwritePartitions.assert_not_called()
