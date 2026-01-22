from unittest.mock import Mock, patch
from pyspark.sql import SparkSession, DataFrame, Row

from template_project.libs.error_handler.extractors.full import SparkFullExtractor


def test_spark_full_extractor_init():
    """Test SparkFullExtractor initialization."""
    extractor = SparkFullExtractor()
    assert extractor is not None


def test_spark_full_extractor_extract_row_data_no_spark():
    """Test extract_row_data with no spark parameter."""
    extractor = SparkFullExtractor()
    result = extractor.extract_row_data()
    assert result == "{}"


def test_spark_full_extractor_extract_row_data_no_source():
    """Test extract_row_data with no source parameter."""
    extractor = SparkFullExtractor()
    mock_spark = Mock(spec=SparkSession)
    result = extractor.extract_row_data(spark=mock_spark)
    assert result == "{}"


def test_spark_full_extractor_extract_row_data_string_source(spark: SparkSession):
    """Test extract_row_data with string source."""
    extractor = SparkFullExtractor()

    with patch.object(spark, "sql") as mock_sql:
        # Mock the DESCRIBE FORMATTED result
        mock_df = Mock(spec=DataFrame)
        mock_rows = [
            Row(col_name="col1", data_type="string", comment="comment1"),
            Row(col_name="col2", data_type="int", comment="comment2"),
            Row(col_name="# Metadata Columns", data_type="", comment=""),
            Row(col_name="table_type", data_type="EXTERNAL", comment=""),
            Row(col_name="# Detailed Table Information", data_type="", comment=""),
            Row(col_name="Database", data_type="test_db", comment=""),
        ]
        mock_df.select.return_value.collect.return_value = mock_rows
        mock_sql.return_value = mock_df

        result = extractor.extract_row_data(spark=spark, source="test_db.test_table")

        assert result != "{}"
        assert "cols" in result
        assert "metadata_cols" in result
        assert "detailed" in result
        mock_sql.assert_called_once_with("DESCRIBE FORMATTED test_db.test_table")


def test_spark_full_extractor_extract_row_data_dataframe_source(spark: SparkSession):
    """Test extract_row_data with DataFrame source."""
    extractor = SparkFullExtractor()

    # Create a mock DataFrame with describe-like data
    mock_df = Mock(spec=DataFrame)
    mock_rows = [
        Row(col_name="col1", data_type="string", comment="comment1"),
        Row(col_name="col2", data_type="int", comment="comment2"),
        Row(col_name="# Metadata Columns", data_type="", comment=""),
        Row(col_name="table_type", data_type="EXTERNAL", comment=""),
        Row(col_name="# Detailed Table Information", data_type="", comment=""),
        Row(col_name="Database", data_type="test_db", comment=""),
    ]
    mock_df.select.return_value.collect.return_value = mock_rows
    mock_df.isEmpty.return_value = False

    result = extractor.extract_row_data(spark=spark, source=mock_df)

    assert result != "{}"
    assert "cols" in result
    assert "metadata_cols" in result
    assert "detailed" in result


def test_spark_full_extractor_extract_row_data_exception_handling(spark: SparkSession):
    """Test extract_row_data with exception handling."""
    extractor = SparkFullExtractor()

    with patch.object(spark, "sql") as mock_sql:
        mock_sql.side_effect = Exception("Table not found")

        result = extractor.extract_row_data(spark=spark, source="nonexistent_table")

        assert result == "{}"


def test_spark_full_extractor_extract_row_data_dataframe_exception(spark: SparkSession):
    """Test extract_row_data with DataFrame source that raises exception."""
    extractor = SparkFullExtractor()

    # Create a mock DataFrame that raises exception
    mock_df = Mock(spec=DataFrame)
    mock_df.isEmpty.return_value = False
    mock_df.select.return_value.collect.side_effect = Exception("Collect failed")

    result = extractor.extract_row_data(spark=spark, source=mock_df)

    assert result == "{}"


def test_spark_full_extractor_extract_row_data_empty_dataframe(spark: SparkSession):
    """Test extract_row_data with empty DataFrame."""
    extractor = SparkFullExtractor()

    # Create a mock empty DataFrame
    mock_df = Mock(spec=DataFrame)
    mock_df.isEmpty.return_value = True

    result = extractor.extract_row_data(spark=spark, source=mock_df)

    assert result == "{}"


def test_spark_full_extractor_extract_row_data_invalid_string_format(
    spark: SparkSession,
):
    """Test extract_row_data with invalid string format."""
    extractor = SparkFullExtractor()

    result = extractor.extract_row_data(spark=spark, source="invalid_format")

    assert result == "{}"


def test_spark_full_extractor_get_full_tbl_metadata():
    """Test _get_full_tbl_metadata static method."""
    # Create mock DataFrame with describe-like data
    mock_df = Mock(spec=DataFrame)
    mock_rows = [
        Row(col_name="col1", data_type="string", comment="comment1"),
        Row(col_name="col2", data_type="int", comment="comment2"),
        Row(col_name="# Metadata Columns", data_type="", comment=""),
        Row(col_name="table_type", data_type="EXTERNAL", comment=""),
        Row(col_name="# Detailed Table Information", data_type="", comment=""),
        Row(col_name="Database", data_type="test_db", comment=""),
    ]
    mock_df.select.return_value.collect.return_value = mock_rows

    result = SparkFullExtractor._get_full_tbl_metadata(mock_df)

    assert result != "{}"
    assert "cols" in result
    assert "metadata_cols" in result
    assert "detailed" in result
