from unittest.mock import Mock, patch
from pyspark.sql import SparkSession

from template_project.libs.iceberg.utils.table_utils import is_empty


def test_is_empty_table_not_exists(spark: SparkSession):
    with patch.object(spark.catalog, "tableExists") as mock_exists:
        mock_exists.return_value = False

        result = is_empty(spark, "nonexistent_table")

        assert result is True
        mock_exists.assert_called_once_with("nonexistent_table")


def test_is_empty_table_exists_with_data(spark: SparkSession):
    with patch.object(spark.catalog, "tableExists") as mock_exists, patch.object(
        spark, "table"
    ) as mock_table, patch.object(spark, "sql") as mock_sql:
        mock_exists.return_value = True

        # Mock the table() call to return a mock DataFrame
        mock_files_df = Mock()
        mock_table.return_value = mock_files_df

        # Mock the sql() call to return a DataFrame with data
        mock_result_df = Mock()
        mock_result_df.head.return_value = [1]  # Tiene datos
        mock_sql.return_value = mock_result_df

        result = is_empty(spark, "existing_table")

        assert result is False
        mock_exists.assert_called_once_with("existing_table")
        mock_table.assert_called_once_with("existing_table.files")
        mock_sql.assert_called_once()


def test_is_empty_table_exists_without_data(spark: SparkSession):
    with patch.object(spark.catalog, "tableExists") as mock_exists, patch.object(
        spark, "table"
    ) as mock_table, patch.object(spark, "sql") as mock_sql:
        mock_exists.return_value = True

        # Mock the table() call to return a mock DataFrame
        mock_files_df = Mock()
        mock_table.return_value = mock_files_df

        # Mock the sql() call to return a DataFrame without data
        mock_result_df = Mock()
        mock_result_df.head.return_value = []  # Sin datos
        mock_sql.return_value = mock_result_df

        result = is_empty(spark, "empty_table")

        assert result is True
        mock_exists.assert_called_once_with("empty_table")
        mock_table.assert_called_once_with("empty_table.files")
        mock_sql.assert_called_once()
