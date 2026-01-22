import pytest
from unittest.mock import Mock, patch, create_autospec
from pyspark.sql import SparkSession, DataFrame

from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.strategies.create_changelog_with_iceberg_sp import (
    CreateChangelogWithIcebergSP,
)
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager import (
    SnapshotManager,
)
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.exceptions import (
    ChangelogManagerException,
)
from demo_comfandi_project.libs.exceptions import ColumnsNotMatchedError


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
    """Test CreateChangelogWithIcebergSP initialization."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    strategy = CreateChangelogWithIcebergSP(
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
def test_build_opts_no_start_timestamp(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _build_opts when start timestamp is None."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_comitted_at_timestamp.side_effect = [None, 1701424245000]

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy._build_opts(123, 456)

    assert result == ""
    mock_snapshot_manager.get_comitted_at_timestamp.assert_any_call(123, "ms")
    mock_snapshot_manager.get_comitted_at_timestamp.assert_any_call(456, "ms")


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_build_opts_no_end_timestamp(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _build_opts when end timestamp is None."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_comitted_at_timestamp.side_effect = [1701424245000, None]

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy._build_opts(123, 456)

    assert result == "'start-timestamp', '1701424245000'"
    mock_snapshot_manager.get_comitted_at_timestamp.assert_any_call(123, "ms")
    mock_snapshot_manager.get_comitted_at_timestamp.assert_any_call(456, "ms")


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_build_opts_both_timestamps(mock_get_logger, mock_spark, mock_snapshot_manager):
    """Test _build_opts when both timestamps are available."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_comitted_at_timestamp.side_effect = [
        1701424245000,
        1701424305000,
    ]

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy._build_opts(123, 456)

    assert (
        result == "'start-timestamp', '1701424245000', 'end-timestamp', '1701424305000'"
    )
    mock_snapshot_manager.get_comitted_at_timestamp.assert_any_call(123, "ms")
    mock_snapshot_manager.get_comitted_at_timestamp.assert_any_call(456, "ms")


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_build_opts_start_greater_than_end(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _build_opts when start timestamp is greater than end timestamp."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_comitted_at_timestamp.side_effect = [
        1701424305000,
        1701424245000,
    ]

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy._build_opts(123, 456)

    assert (
        result == "'start-timestamp', '1701424305000', 'end-timestamp', '1701424245000'"
    )


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_table_success(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _create_changelog_table when successful."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_dataframe = Mock(spec=DataFrame)
    mock_spark.table.return_value = mock_dataframe

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy._create_changelog_table("'start-timestamp', '1701424245000'")

    assert result == mock_dataframe
    mock_spark.sql.assert_called_once()
    sql_call = mock_spark.sql.call_args[0][0]
    assert "CALL test_catalog.system.create_changelog_view" in sql_call
    assert "table => 'test_catalog.test_schema.test_table'" in sql_call
    assert "changelog_view => 'cdc_test_table'" in sql_call
    assert "options => map('start-timestamp', '1701424245000')" in sql_call
    assert "net_changes => true" in sql_call
    mock_spark.table.assert_called_once_with("cdc_test_table")


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_table_no_options(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _create_changelog_table with no options."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_dataframe = Mock(spec=DataFrame)
    mock_spark.table.return_value = mock_dataframe

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy._create_changelog_table("")

    assert result == mock_dataframe
    sql_call = mock_spark.sql.call_args[0][0]
    assert "options => map()" not in sql_call
    assert ", options => map()" not in sql_call


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_table_exception(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _create_changelog_table when SQL query raises exception."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_spark.sql.side_effect = Exception("SQL Error")

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    with pytest.raises(ChangelogManagerException) as exc_info:
        strategy._create_changelog_table("'start-timestamp', '1701424245000'")

    assert "Failed to create changelog view" in str(exc_info.value)


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_get_gold_records_missing_columns(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test _get_gold_records when required columns are missing."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    mock_changelog_df = Mock(spec=DataFrame)
    mock_changelog_df.columns = ["id", "name", "value"]  # Missing required columns

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    with pytest.raises(ColumnsNotMatchedError) as exc_info:
        strategy._get_gold_records(mock_changelog_df)

    assert "Expected columns" in str(exc_info.value)
    assert "do not match actual columns" in str(exc_info.value)


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

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy.create_changelog()

    assert result == mock_table_df
    mock_snapshot_manager.get_last_snapshot_id.assert_called_once_with("test_tag")
    mock_spark.table.assert_called_once_with("test_catalog.test_schema.test_table")


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_no_changes(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test create_changelog when there are no changes."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_last_snapshot_id.return_value = 123
    mock_snapshot_manager.get_current_snapshot_id.return_value = 456
    mock_snapshot_manager.has_changed.return_value = False

    mock_table_df = Mock(spec=DataFrame)
    mock_table_df.schema = "test_schema"
    mock_spark.table.return_value = mock_table_df
    mock_empty_df = Mock(spec=DataFrame)
    mock_spark.createDataFrame.return_value = mock_empty_df

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    result = strategy.create_changelog()

    assert result == mock_empty_df
    mock_snapshot_manager.has_changed.assert_called_once_with("test_tag")
    mock_spark.createDataFrame.assert_called_once_with([], "test_schema")


@patch("demo_comfandi_project.libs.logging.get_logger")
def test_create_changelog_with_changes(
    mock_get_logger, mock_spark, mock_snapshot_manager
):
    """Test create_changelog when there are changes."""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.get_last_snapshot_id.return_value = 123
    mock_snapshot_manager.get_current_snapshot_id.return_value = 456
    mock_snapshot_manager.has_changed.return_value = True
    mock_snapshot_manager.get_comitted_at_timestamp.side_effect = [
        1701424245000,
        1701424305000,
    ]

    mock_changelog_df = Mock(spec=DataFrame)
    mock_gold_df = Mock(spec=DataFrame)

    strategy = CreateChangelogWithIcebergSP(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )

    with patch.object(
        strategy, "_create_changelog_table", return_value=mock_changelog_df
    ), patch.object(strategy, "_get_gold_records", return_value=mock_gold_df):

        result = strategy.create_changelog()

    assert result == mock_gold_df
    mock_snapshot_manager.has_changed.assert_called_once_with("test_tag")
