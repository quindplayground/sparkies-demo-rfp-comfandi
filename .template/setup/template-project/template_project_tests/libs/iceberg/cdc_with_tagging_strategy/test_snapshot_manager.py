import pytest
from unittest.mock import Mock, patch, create_autospec
from pyspark.sql import SparkSession, Row

from template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager import (
    SnapshotManager,
)
from template_project.libs.iceberg.cdc_with_tagging_strategy.exceptions import (
    SnapshotManagerException,
)


@pytest.fixture
def mock_spark():
    """Create a mock SparkSession for testing."""
    mock_spark = create_autospec(SparkSession, instance=True)
    mock_spark.catalog = Mock()
    mock_spark.sql = Mock()
    return mock_spark


@pytest.fixture
def snapshot_manager(mock_spark):
    """Create a SnapshotManager instance for testing."""
    return SnapshotManager(mock_spark, "test_database.test_table")


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    mock_logger = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    return mock_logger


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_init(mock_get_logger, mock_spark, mock_logger):
    """Test SnapshotManager initialization."""
    mock_get_logger.return_value = mock_logger

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    assert manager.spark == mock_spark
    assert manager.table_id == "test_db.test_table"
    assert manager.logger == mock_logger
    mock_get_logger.assert_called_once_with("SnapshotManager")


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_table_exists_true(mock_get_logger, mock_spark, mock_logger):
    """Test _table_exists when table exists."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    manager = SnapshotManager(mock_spark, "test_db.test_table")
    manager._table_exists()  # No asignar el resultado ya que no retorna nada

    # Se llama dos veces: una en el constructor y otra en _table_exists()
    assert mock_spark.catalog.tableExists.call_count == 2
    mock_logger.info.assert_called()
    mock_logger.warning.assert_not_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_table_exists_false(mock_get_logger, mock_spark, mock_logger):
    """Test _table_exists when table does not exist."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = False

    with pytest.raises(SnapshotManagerException) as exc_info:
        SnapshotManager(mock_spark, "test_db.test_table")

    assert "Table does not exist" in str(exc_info.value)
    mock_spark.catalog.tableExists.assert_called_once_with("test_db.test_table")
    mock_logger.warning.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_last_snapshot_id_table_not_exists(
    mock_get_logger, mock_spark, mock_logger
):
    """Test get_last_snapshot_id when table does not exist."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = False

    with pytest.raises(SnapshotManagerException) as exc_info:
        SnapshotManager(mock_spark, "test_db.test_table")

    assert "Table does not exist" in str(exc_info.value)


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_last_snapshot_id_success(mock_get_logger, mock_spark, mock_logger):
    """Test get_last_snapshot_id when successful."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    # Mock the SQL query result
    mock_row = Mock(spec=Row)
    mock_row.snapshot_id = 123
    mock_dataframe = Mock()
    mock_dataframe.first.return_value = mock_row
    mock_spark.sql.return_value = mock_dataframe

    manager = SnapshotManager(mock_spark, "test_db.test_table")
    result = manager.get_last_snapshot_id("test_tag")

    assert result == 123
    mock_spark.sql.assert_called_once()
    sql_call = mock_spark.sql.call_args[0][0]
    assert "SELECT snapshot_id" in sql_call
    assert "FROM test_db.test_table.refs" in sql_call
    assert "WHERE name = 'test_tag'" in sql_call


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_last_snapshot_id_no_result(mock_get_logger, mock_spark, mock_logger):
    """Test get_last_snapshot_id when no result is found."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    # Mock the SQL query result returning None
    mock_dataframe = Mock()
    mock_dataframe.first.return_value = None
    mock_spark.sql.return_value = mock_dataframe

    manager = SnapshotManager(mock_spark, "test_db.test_table")
    result = manager.get_last_snapshot_id("test_tag")

    assert result is None
    mock_logger.warning.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_last_snapshot_id_exception(mock_get_logger, mock_spark, mock_logger):
    """Test get_last_snapshot_id when SQL query raises exception."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True
    mock_spark.sql.side_effect = Exception("SQL Error")

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    with pytest.raises(SnapshotManagerException) as exc_info:
        manager.get_last_snapshot_id("test_tag")

    assert "Failed to get last snapshot ID" in str(exc_info.value)
    mock_logger.error.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_current_snapshot_id_table_not_exists(
    mock_get_logger, mock_spark, mock_logger
):
    """Test get_current_snapshot_id when table does not exist."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = False

    with pytest.raises(SnapshotManagerException) as exc_info:
        SnapshotManager(mock_spark, "test_db.test_table")

    assert "Table does not exist" in str(exc_info.value)


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_current_snapshot_id_success(mock_get_logger, mock_spark, mock_logger):
    """Test get_current_snapshot_id when successful."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    # Mock the SQL query result
    mock_row = Mock(spec=Row)
    mock_row.snapshot_id = 456
    mock_dataframe = Mock()
    mock_dataframe.first.return_value = mock_row
    mock_spark.sql.return_value = mock_dataframe

    manager = SnapshotManager(mock_spark, "test_db.test_table")
    result = manager.get_current_snapshot_id()

    assert result == 456
    mock_spark.sql.assert_called_once()
    sql_call = mock_spark.sql.call_args[0][0]
    assert "SELECT snapshot_id" in sql_call
    assert "FROM test_db.test_table.snapshots" in sql_call
    assert "ORDER BY committed_at DESC" in sql_call


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_current_snapshot_id_no_result(mock_get_logger, mock_spark, mock_logger):
    """Test get_current_snapshot_id when no result is found."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    # Mock the SQL query result returning None
    mock_dataframe = Mock()
    mock_dataframe.first.return_value = None
    mock_spark.sql.return_value = mock_dataframe

    manager = SnapshotManager(mock_spark, "test_db.test_table")
    result = manager.get_current_snapshot_id()

    assert result is None
    mock_logger.warning.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_current_snapshot_id_exception(mock_get_logger, mock_spark, mock_logger):
    """Test get_current_snapshot_id when SQL query raises exception."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True
    mock_spark.sql.side_effect = Exception("SQL Error")

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    with pytest.raises(SnapshotManagerException) as exc_info:
        manager.get_current_snapshot_id()

    assert "Failed to get current snapshot ID" in str(exc_info.value)
    mock_logger.error.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_has_changed_table_not_exists(mock_get_logger, mock_spark, mock_logger):
    """Test has_changed when table does not exist."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = False

    with pytest.raises(SnapshotManagerException) as exc_info:
        SnapshotManager(mock_spark, "test_db.test_table")

    assert "Table does not exist" in str(exc_info.value)


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_has_changed_no_snapshots(mock_get_logger, mock_spark, mock_logger):
    """Test has_changed when no snapshots exist."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    # Mock get_last_snapshot_id and get_current_snapshot_id to return None
    with patch.object(manager, "get_last_snapshot_id", return_value=None), patch.object(
        manager, "get_current_snapshot_id", return_value=None
    ):
        result = manager.has_changed("test_tag")

    assert result is False


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_has_changed_snapshots_different(mock_get_logger, mock_spark, mock_logger):
    """Test has_changed when snapshots are different."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    # Mock get_last_snapshot_id and get_current_snapshot_id to return different values
    with patch.object(manager, "get_last_snapshot_id", return_value=123), patch.object(
        manager, "get_current_snapshot_id", return_value=456
    ):
        result = manager.has_changed("test_tag")

    assert result is True


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_has_changed_snapshots_same(mock_get_logger, mock_spark, mock_logger):
    """Test has_changed when snapshots are the same."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    # Mock get_last_snapshot_id and get_current_snapshot_id to return same values
    with patch.object(manager, "get_last_snapshot_id", return_value=123), patch.object(
        manager, "get_current_snapshot_id", return_value=123
    ):
        result = manager.has_changed("test_tag")

    assert result is False


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_exists_tag_table_not_exists(mock_get_logger, mock_spark, mock_logger):
    """Test exists_tag when table does not exist."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = False

    with pytest.raises(SnapshotManagerException) as exc_info:
        SnapshotManager(mock_spark, "test_db.test_table")

    assert "Table does not exist" in str(exc_info.value)


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_exists_tag_no_last_snapshot(mock_get_logger, mock_spark, mock_logger):
    """Test exists_tag when no last snapshot exists."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    with patch.object(manager, "get_last_snapshot_id", return_value=None):
        result = manager.last_snapshot_tag_exists("test_tag")

    assert result is False


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_exists_tag_has_last_snapshot(mock_get_logger, mock_spark, mock_logger):
    """Test exists_tag when last snapshot exists."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    with patch.object(manager, "get_last_snapshot_id", return_value=123):
        result = manager.last_snapshot_tag_exists("test_tag")

    assert result is True


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_comitted_at_timestamp_table_not_exists(
    mock_get_logger, mock_spark, mock_logger
):
    """Test get_comitted_at_timestamp when table does not exist."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = False

    with pytest.raises(SnapshotManagerException) as exc_info:
        SnapshotManager(mock_spark, "test_db.test_table")

    assert "Table does not exist" in str(exc_info.value)


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_comitted_at_timestamp_success(mock_get_logger, mock_spark, mock_logger):
    """Test get_comitted_at_timestamp when successful."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    # Mock the SQL query result
    mock_row = Mock(spec=Row)
    mock_row.committed_at_str = "2023-12-01 10:30:45"
    mock_row.committed_at_ms = 1701424245000
    mock_row.committed_at_datetime = "2023-12-01 10:30:45"
    mock_dataframe = Mock()
    mock_dataframe.first.return_value = mock_row
    mock_spark.sql.return_value = mock_dataframe

    manager = SnapshotManager(mock_spark, "test_db.test_table")
    result = manager.get_comitted_at_timestamp(123)

    assert result == "2023-12-01 10:30:45"
    mock_spark.sql.assert_called_once()
    sql_call = mock_spark.sql.call_args[0][0]
    assert "SELECT" in sql_call
    assert "DATE_FORMAT(committed_at" in sql_call
    assert "FROM test_db.test_table.snapshots" in sql_call
    assert "WHERE snapshot_id = 123" in sql_call


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_comitted_at_timestamp_no_result(mock_get_logger, mock_spark, mock_logger):
    """Test get_comitted_at_timestamp when no result is found."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    # Mock the SQL query result returning None
    mock_dataframe = Mock()
    mock_dataframe.first.return_value = None
    mock_spark.sql.return_value = mock_dataframe

    manager = SnapshotManager(mock_spark, "test_db.test_table")
    result = manager.get_comitted_at_timestamp(123)

    assert result is None
    mock_logger.warning.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_get_comitted_at_timestamp_exception(mock_get_logger, mock_spark, mock_logger):
    """Test get_comitted_at_timestamp when SQL query raises exception."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True
    mock_spark.sql.side_effect = Exception("SQL Error")

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    with pytest.raises(SnapshotManagerException) as exc_info:
        manager.get_comitted_at_timestamp(123)

    assert "Failed to get committed at timestamp" in str(exc_info.value)
    mock_logger.error.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_set_last_snapshot_id_tag_table_not_exists(
    mock_get_logger, mock_spark, mock_logger
):
    """Test set_last_snapshot_id_tag when table does not exist."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = False

    with pytest.raises(SnapshotManagerException) as exc_info:
        SnapshotManager(mock_spark, "test_db.test_table")

    assert "Table does not exist" in str(exc_info.value)


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_set_last_snapshot_id_tag_no_current_snapshot(
    mock_get_logger, mock_spark, mock_logger
):
    """Test set_last_snapshot_id_tag when no current snapshot exists."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    with patch.object(manager, "get_current_snapshot_id", return_value=None):
        result = manager.set_last_snapshot_tag("test_tag")

    assert result is False
    mock_spark.sql.assert_not_called()
    mock_logger.warning.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_set_last_snapshot_id_tag_success(mock_get_logger, mock_spark, mock_logger):
    """Test set_last_snapshot_id_tag when successful."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    with patch.object(manager, "get_current_snapshot_id", return_value=789):
        manager.set_last_snapshot_tag("test_tag")

    mock_spark.sql.assert_called_once()
    sql_call = mock_spark.sql.call_args[0][0]
    assert "ALTER TABLE test_db.test_table" in sql_call
    assert "CREATE OR REPLACE TAG `test_tag`" in sql_call
    assert "AS OF VERSION 789" in sql_call


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_set_last_snapshot_id_tag_exception(mock_get_logger, mock_spark, mock_logger):
    """Test set_last_snapshot_id_tag when SQL query raises exception."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True
    mock_spark.sql.side_effect = Exception("SQL Error")

    manager = SnapshotManager(mock_spark, "test_db.test_table")

    with patch.object(manager, "get_current_snapshot_id", return_value=789):
        result = manager.set_last_snapshot_tag("test_tag")

    assert result is False
    mock_logger.error.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_drop_last_snapshot_tag_success(mock_get_logger, mock_spark, mock_logger):
    """Test drop_last_snapshot_tag when successful."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True

    manager = SnapshotManager(mock_spark, "test_db.test_table")
    result = manager.drop_last_snapshot_tag("test_tag")

    assert result is True
    mock_spark.sql.assert_called_once()
    sql_call = mock_spark.sql.call_args[0][0]
    assert "ALTER TABLE test_db.test_table" in sql_call
    assert "DROP TAG IF EXISTS `test_tag`" in sql_call


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager.get_logger"
)
def test_drop_last_snapshot_tag_exception(mock_get_logger, mock_spark, mock_logger):
    """Test drop_last_snapshot_tag when SQL query raises exception."""
    mock_get_logger.return_value = mock_logger
    mock_spark.catalog.tableExists.return_value = True
    mock_spark.sql.side_effect = Exception("SQL Error")

    manager = SnapshotManager(mock_spark, "test_db.test_table")
    result = manager.drop_last_snapshot_tag("test_tag")

    assert result is False
    mock_logger.error.assert_called()


def test_snapshot_manager_exception():
    """Test SnapshotManagerException can be instantiated."""
    exception = SnapshotManagerException("Test error message")
    assert str(exception) == "Test error message"
    assert isinstance(exception, Exception)
