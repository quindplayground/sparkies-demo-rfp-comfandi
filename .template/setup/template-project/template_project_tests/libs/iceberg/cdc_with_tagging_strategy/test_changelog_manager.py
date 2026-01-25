import pytest
from unittest.mock import Mock, patch, create_autospec
from pyspark.sql import SparkSession, DataFrame

from template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager import (
    ChangelogManager,
)
from template_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager import (
    SnapshotManager,
)
from template_project.libs.iceberg.cdc_with_tagging_strategy.strategies.factory import (
    StrategyFactory,
)
from template_project.libs.iceberg.cdc_with_tagging_strategy.exceptions import (
    InvalidTableFormatError,
    CommitChangesError,
)


@pytest.fixture
def mock_spark():
    """Create a mock SparkSession for testing."""
    mock_spark = create_autospec(SparkSession, instance=True)
    mock_spark.catalog = Mock()
    mock_spark.sql = Mock()
    return mock_spark


@pytest.fixture
def mock_snapshot_manager():
    """Create a mock SnapshotManager for testing."""
    return create_autospec(SnapshotManager, instance=True)


@pytest.fixture
def mock_strategy_factory():
    """Create a mock StrategyFactory for testing."""
    return create_autospec(StrategyFactory, instance=True)


@pytest.fixture
def mock_strategy():
    """Create a mock strategy for testing."""
    mock_strategy = Mock()
    mock_strategy.create_changelog.return_value = Mock(spec=DataFrame)
    return mock_strategy


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    mock_logger = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    return mock_logger


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager.get_logger"
)
def test_init_with_defaults(mock_get_logger, mock_spark, mock_logger):
    """Test ChangelogManager initialization with default parameters."""
    mock_get_logger.return_value = mock_logger

    manager = ChangelogManager(
        mock_spark, "test_catalog.test_schema.test_table", "test_tag"
    )

    assert manager.spark == mock_spark
    assert manager.table_id == "test_catalog.test_schema.test_table"
    assert manager.catalog == "test_catalog"
    assert manager.tag_name == "test_tag"
    assert isinstance(manager.snapshot_manager, SnapshotManager)
    assert isinstance(manager.strategy_factory, StrategyFactory)
    assert manager.logger == mock_logger
    mock_get_logger.assert_called_once_with("ChangelogManager")


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager.get_logger"
)
def test_init_with_custom_managers(
    mock_get_logger,
    mock_spark,
    mock_snapshot_manager,
    mock_strategy_factory,
    mock_logger,
):
    """Test ChangelogManager initialization with custom managers."""
    mock_get_logger.return_value = mock_logger

    manager = ChangelogManager(
        mock_spark,
        "test_catalog.test_schema.test_table",
        "test_tag",
        snapshot_manager=mock_snapshot_manager,
        strategy_factory=mock_strategy_factory,
    )

    assert manager.spark == mock_spark
    assert manager.table_id == "test_catalog.test_schema.test_table"
    assert manager.catalog == "test_catalog"
    assert manager.tag_name == "test_tag"
    assert manager.snapshot_manager == mock_snapshot_manager
    assert manager.strategy_factory == mock_strategy_factory
    assert manager.logger == mock_logger


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager.get_logger"
)
def test_init_invalid_table_format(mock_get_logger, mock_spark, mock_logger):
    """Test ChangelogManager initialization with invalid table format."""
    mock_get_logger.return_value = mock_logger

    with pytest.raises(InvalidTableFormatError) as exc_info:
        ChangelogManager(mock_spark, "invalid_table_format", "test_tag")

    assert "Invalid table id" in str(exc_info.value)
    assert (
        "it must be a valid iceberg table id with format <catalog>.<schema>.<table>"
        in str(exc_info.value)
    )


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager.get_logger"
)
def test_validate_table_id_format_valid(mock_get_logger, mock_spark, mock_logger):
    """Test _validate_table_id_format with valid formats."""
    mock_get_logger.return_value = mock_logger

    _ = ChangelogManager(mock_spark, "test_catalog.test_schema.test_table", "test_tag")

    # Test various valid formats
    valid_formats = ["catalog.schema.table", "catalog123.schema123.table123", "a.b.c"]

    for table_id in valid_formats:
        result = ChangelogManager._validate_table_id_format(table_id)
        assert result == table_id


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager.get_logger"
)
def test_validate_table_id_format_invalid(mock_get_logger, mock_spark, mock_logger):
    """Test _validate_table_id_format with invalid formats."""
    mock_get_logger.return_value = mock_logger

    _ = ChangelogManager(mock_spark, "test_catalog.test_schema.test_table", "test_tag")

    # Test various invalid formats
    invalid_formats = [
        "catalog.schema",  # Missing table
        "catalog",  # Only catalog
        "catalog.schema.table.extra",  # Too many parts
        "catalog.schema.table-name",  # Invalid characters
        "catalog.schema.table name",  # Spaces
        "",  # Empty string
        "catalog.schema.",  # Empty table name
    ]

    for table_id in invalid_formats:
        with pytest.raises(InvalidTableFormatError):
            ChangelogManager._validate_table_id_format(table_id)


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager.get_logger"
)
def test_extract_catalog_from_table_id(mock_get_logger, mock_spark, mock_logger):
    """Test _extract_catalog_from_table_id."""
    mock_get_logger.return_value = mock_logger

    _ = ChangelogManager(mock_spark, "test_catalog.test_schema.test_table", "test_tag")

    test_cases = [
        ("catalog.schema.table", "catalog"),
        ("my_catalog.my_schema.my_table", "my_catalog"),
        ("a.b.c", "a"),
        ("catalog123.schema123.table123", "catalog123"),
    ]

    for table_id, expected_catalog in test_cases:
        result = ChangelogManager._extract_catalog_from_table_id(table_id)
        assert result == expected_catalog


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager.get_logger"
)
def test_get_changelog_table_success(
    mock_get_logger,
    mock_spark,
    mock_snapshot_manager,
    mock_strategy_factory,
    mock_strategy,
    mock_logger,
):
    """Test get_changelog_table when successful."""
    mock_get_logger.return_value = mock_logger
    mock_strategy_factory.__getitem__.return_value.return_value = mock_strategy

    manager = ChangelogManager(
        mock_spark,
        "test_catalog.test_schema.test_table",
        "test_tag",
        snapshot_manager=mock_snapshot_manager,
        strategy_factory=mock_strategy_factory,
    )

    result = manager.get_changelog_table(
        changelog_strategy="iceberg_sp", exclude_cols=["col1", "col2"]
    )

    assert result == mock_strategy.create_changelog.return_value
    mock_strategy_factory.__getitem__.assert_called_once_with("iceberg_sp")
    mock_strategy_factory.__getitem__.return_value.assert_called_once_with(
        spark=mock_spark,
        snapshot_manager=mock_snapshot_manager,
        table_id="test_catalog.test_schema.test_table",
        catalog="test_catalog",
        tag_name="test_tag",
    )
    mock_strategy.create_changelog.assert_called_once_with(
        exclude_cols=["col1", "col2"]
    )
    mock_logger.info.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager.get_logger"
)
def test_get_changelog_table_with_kwargs(
    mock_get_logger,
    mock_spark,
    mock_snapshot_manager,
    mock_strategy_factory,
    mock_strategy,
    mock_logger,
):
    """Test get_changelog_table with keyword arguments."""
    mock_get_logger.return_value = mock_logger
    mock_strategy_factory.__getitem__.return_value.return_value = mock_strategy

    manager = ChangelogManager(
        mock_spark,
        "test_catalog.test_schema.test_table",
        "test_tag",
        snapshot_manager=mock_snapshot_manager,
        strategy_factory=mock_strategy_factory,
    )

    result = manager.get_changelog_table(
        changelog_strategy="date_filter", date_col="created_at", safety_interval="1 day"
    )

    assert result == mock_strategy.create_changelog.return_value
    mock_strategy_factory.__getitem__.assert_called_once_with("date_filter")
    mock_strategy.create_changelog.assert_called_once_with(
        date_col="created_at", safety_interval="1 day"
    )
    mock_logger.info.assert_called()


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager.get_logger"
)
def test_commit_changes_success(
    mock_get_logger, mock_spark, mock_snapshot_manager, mock_logger
):
    """Test commit_changes when successful."""
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.set_last_snapshot_tag.return_value = True

    manager = ChangelogManager(
        mock_spark,
        "test_catalog.test_schema.test_table",
        "test_tag",
        snapshot_manager=mock_snapshot_manager,
    )

    manager.commit_changes()  # No asignar el resultado ya que no retorna nada útil

    mock_snapshot_manager.set_last_snapshot_tag.assert_called_once_with("test_tag")
    mock_logger.info.assert_called()
    # Verificar que se llama info dos veces: inicio y fin
    assert mock_logger.info.call_count == 2


@patch(
    "template_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager.get_logger"
)
def test_commit_changes_failure(
    mock_get_logger, mock_spark, mock_snapshot_manager, mock_logger
):
    """Test commit_changes when it fails."""
    mock_get_logger.return_value = mock_logger
    mock_snapshot_manager.set_last_snapshot_tag.return_value = False

    manager = ChangelogManager(
        mock_spark,
        "test_catalog.test_schema.test_table",
        "test_tag",
        snapshot_manager=mock_snapshot_manager,
    )

    with pytest.raises(CommitChangesError) as exc_info:
        manager.commit_changes()

    assert "Failed to set last snapshot ID tag" in str(exc_info.value)
    mock_snapshot_manager.set_last_snapshot_tag.assert_called_once_with("test_tag")
    mock_logger.warning.assert_called()


def test_invalid_table_format_error():
    """Test InvalidTableFormatError can be instantiated."""
    exception = InvalidTableFormatError("Test error message")
    assert str(exception) == "Test error message"
    assert isinstance(exception, Exception)


def test_commit_changes_error():
    """Test CommitChangesError can be instantiated."""
    exception = CommitChangesError("Test error message")
    assert str(exception) == "Test error message"
    assert isinstance(exception, Exception)
