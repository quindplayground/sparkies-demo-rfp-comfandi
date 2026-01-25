import pytest
from unittest.mock import Mock, patch, create_autospec
from pyspark.sql import SparkSession, DataFrame

from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.strategies.create_changelog_with_date_filter import (
    CreateChangelogWithDateFilter,
)
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager import (
    SnapshotManager,
)
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.exceptions import (
    IncrementalExtractException,
)


@pytest.fixture
def mock_spark():
    """Create a mock SparkSession for testing."""
    mock_spark = create_autospec(SparkSession, instance=True)
    mock_spark.sql = Mock()
    mock_spark.table = Mock()
    mock_spark.createDataFrame = Mock()
    return mock_spark


@pytest.fixture
def mock_snapshot_manager():
    """Create a mock SnapshotManager for testing."""
    return create_autospec(SnapshotManager, instance=True)


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_init(mock_get_logger, mock_spark, mock_snapshot_manager):
    """Test CreateChangelogWithDateFilter initialization."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    assert strategy.spark == mock_spark
    assert strategy.snapshot_manager == mock_snapshot_manager
    assert strategy.table_id == "test_catalog.test_schema.test_table"
    assert strategy.catalog == "test_catalog"
    assert strategy.tag_name == "test_tag"


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_validate_date_column_success(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _validate_date_column when column exists."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_table_df = Mock(spec=DataFrame)
    mock_table_df.columns = ["id", "name", "created_at", "updated_at"]
    mock_spark.table.return_value = mock_table_df

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    # Should not raise exception
    strategy._validate_date_column("created_at")

    mock_spark.table.assert_called_once_with("test_catalog.test_schema.test_table")


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_validate_date_column_not_found(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _validate_date_column when column does not exist."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_table_df = Mock(spec=DataFrame)
    mock_table_df.columns = ["id", "name", "created_at"]
    mock_spark.table.return_value = mock_table_df

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    with pytest.raises(IncrementalExtractException) as exc_info:
        strategy._validate_date_column("updated_at")

    assert (
        "Date column updated_at not found in table test_catalog.test_schema.test_table"
        in str(exc_info.value)
    )


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_build_interval_expression_valid(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _build_interval_expression with valid safety intervals."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    test_cases = [
        ("1 day", "- INTERVAL 1 day"),
        ("2 hours", "- INTERVAL 2 hours"),
        ("30 minutes", "- INTERVAL 30 minutes"),
        ("7 days", "- INTERVAL 7 days"),
    ]

    for safety_interval, expected in test_cases:
        result = strategy._build_interval_expression(safety_interval)
        assert result == expected


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_build_interval_expression_invalid(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _build_interval_expression with invalid safety intervals."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    invalid_intervals = [
        "1day",  # No space
        "1 day extra",  # Extra text
        "1",  # No unit
        "day",  # No number
        "1.5 days",  # Decimal number
        "",  # Empty string
    ]

    for safety_interval in invalid_intervals:
        result = strategy._build_interval_expression(safety_interval)
        assert result == ""


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_build_interval_expression_none(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _build_interval_expression with None safety interval."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy._build_interval_expression(None)
    assert result == ""


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_missing_date_col(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test create_changelog when date_col is None."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    with pytest.raises(IncrementalExtractException) as exc_info:
        strategy.create_changelog()

    assert "date_col parameter is required for date filter strategy" in str(
        exc_info.value
    )


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_first_execution(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test create_changelog on first execution (no last snapshot)."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_last_snapshot_id.return_value = None
    mock_table_df = Mock(spec=DataFrame)
    mock_spark.table.return_value = mock_table_df

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy.create_changelog(date_col="created_at")

    assert result == mock_table_df
    mock_snapshot_manager.get_last_snapshot_id.assert_called_once_with("test_tag")
    mock_spark.table.assert_called_once_with("test_catalog.test_schema.test_table")


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_no_start_date(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test create_changelog when no start date is found."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_last_snapshot_id.return_value = 123
    mock_snapshot_manager.get_comitted_at_timestamp.return_value = None
    mock_table_df = Mock(spec=DataFrame)
    mock_spark.table.return_value = mock_table_df

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy.create_changelog(date_col="created_at")

    assert result == mock_table_df
    mock_snapshot_manager.get_comitted_at_timestamp.assert_called_once_with(123)
    mock_spark.table.assert_called_once_with("test_catalog.test_schema.test_table")


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_no_changes(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test create_changelog when there are no changes."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_last_snapshot_id.return_value = 123
    mock_snapshot_manager.get_comitted_at_timestamp.return_value = "2023-12-01 10:30:45"
    mock_snapshot_manager.has_changed.return_value = False

    mock_table_df = Mock(spec=DataFrame)
    mock_table_df.schema = "test_schema"
    mock_spark.table.return_value = mock_table_df
    mock_empty_df = Mock(spec=DataFrame)
    mock_spark.createDataFrame.return_value = mock_empty_df

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy.create_changelog(date_col="created_at")

    assert result == mock_empty_df
    mock_snapshot_manager.has_changed.assert_called_once_with("test_tag")
    mock_spark.createDataFrame.assert_called_once_with([], "test_schema")


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_with_changes_success(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test create_changelog when there are changes and query succeeds."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_last_snapshot_id.return_value = 123
    mock_snapshot_manager.get_comitted_at_timestamp.return_value = "2023-12-01 10:30:45"
    mock_snapshot_manager.has_changed.return_value = True

    mock_table_df = Mock(spec=DataFrame)
    mock_table_df.columns = ["id", "name", "created_at", "updated_at"]
    mock_spark.table.return_value = mock_table_df

    mock_result_df = Mock(spec=DataFrame)
    mock_spark.sql.return_value = mock_result_df

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy.create_changelog(date_col="created_at", safety_interval="1 day")

    assert result == mock_result_df
    mock_snapshot_manager.has_changed.assert_called_once_with("test_tag")
    mock_spark.sql.assert_called_once()

    sql_call = mock_spark.sql.call_args[0][0]
    assert "SELECT *" in sql_call
    assert "FROM test_catalog.test_schema.test_table" in sql_call
    assert (
        "WHERE created_at >= (CAST('2023-12-01 10:30:45' AS TIMESTAMP) - INTERVAL 1 day)"
        in sql_call
    )


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_with_changes_no_safety_interval(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test create_changelog with changes but no safety interval."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_last_snapshot_id.return_value = 123
    mock_snapshot_manager.get_comitted_at_timestamp.return_value = "2023-12-01 10:30:45"
    mock_snapshot_manager.has_changed.return_value = True

    mock_table_df = Mock(spec=DataFrame)
    mock_table_df.columns = ["id", "name", "created_at", "updated_at"]
    mock_spark.table.return_value = mock_table_df

    mock_result_df = Mock(spec=DataFrame)
    mock_spark.sql.return_value = mock_result_df

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy.create_changelog(date_col="created_at")

    assert result == mock_result_df

    sql_call = mock_spark.sql.call_args[0][0]
    assert "WHERE created_at >= (CAST('2023-12-01 10:30:45' AS TIMESTAMP) )" in sql_call


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_query_exception(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test create_changelog when SQL query raises exception."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_last_snapshot_id.return_value = 123
    mock_snapshot_manager.get_comitted_at_timestamp.return_value = "2023-12-01 10:30:45"
    mock_snapshot_manager.has_changed.return_value = True

    mock_table_df = Mock(spec=DataFrame)
    mock_table_df.columns = ["id", "name", "created_at", "updated_at"]
    mock_spark.table.return_value = mock_table_df

    mock_spark.sql.side_effect = Exception("SQL Error")

    strategy = CreateChangelogWithDateFilter(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    with pytest.raises(IncrementalExtractException) as exc_info:
        strategy.create_changelog(date_col="created_at")

    assert "Failed to extract data" in str(exc_info.value)


def test_incremental_extract_exception():
    """Test IncrementalExtractException can be instantiated."""
    exception = IncrementalExtractException("Test error message")
    assert str(exception) == "Test error message"
    assert isinstance(exception, Exception)
