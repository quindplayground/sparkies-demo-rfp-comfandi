import pytest
from unittest.mock import Mock, patch
from pyspark.sql import Row
from botocore.exceptions import ClientError

from template_project.libs.aws.dynamodb.loader.handlers.base import (
    DynamoDBOperationHandler,
)


class ConcreteHandler(DynamoDBOperationHandler):
    """Concrete implementation for testing abstract class"""

    def process_item(self, bw, item):
        return True


@pytest.fixture
def handler():
    return ConcreteHandler("test-job", "us-east-1", "test-table", 400000)


def test_init_default_values():
    handler = ConcreteHandler("job-1", "region-1", "table-1", 100000)

    assert handler.job_id == "job-1"
    assert handler.region == "region-1"
    assert handler.table_name == "table-1"
    assert handler.item_size_limit == 100000
    assert handler.max_retries == 5
    assert handler.base_wait == 5.0


def test_init_custom_values():
    handler = ConcreteHandler(
        "job-1", "region-1", "table-1", 100000, max_retries=3, base_wait=2.0
    )

    assert handler.max_retries == 3
    assert handler.base_wait == 2.0


@patch("template_project.libs.aws.dynamodb.loader.handlers.base.get_table")
def test_get_table(mock_get_table, handler):
    mock_table = Mock()
    mock_get_table.return_value = mock_table

    result = handler._get_table()

    mock_get_table.assert_called_once_with("us-east-1", "test-table")
    assert result == mock_table


def test_get_item_keys_with_all_keys(handler):
    item = {
        "pk": "pk-value",
        "sk": "sk-value",
        "gsi1_pk": "gsi1_pk-value",
        "gsi1_sk": "gsi1_sk-value",
        "gsi2_pk": "gsi2_pk-value",
        "gsi2_sk": "gsi2_sk-value",
        "other_field": "other-value",
    }

    result = handler._get_item_keys(item)

    expected = {
        "pk": "pk-value",
        "sk": "sk-value",
        "gsi1_pk": "gsi1_pk-value",
        "gsi1_sk": "gsi1_sk-value",
        "gsi2_pk": "gsi2_pk-value",
        "gsi2_sk": "gsi2_sk-value",
    }
    assert result == expected


def test_get_item_keys_with_partial_keys(handler):
    item = {"pk": "pk-value", "sk": "sk-value", "other_field": "other-value"}

    result = handler._get_item_keys(item)

    expected = {"pk": "pk-value", "sk": "sk-value"}
    assert result == expected


def test_get_item_keys_empty(handler):
    item = {"other_field": "other-value"}

    result = handler._get_item_keys(item)

    assert result == {}


def test_log_item_error(handler):
    # Este test ya no es relevante porque _log_item_error fue removido
    # El logging ahora se hace directamente en los métodos específicos
    pass


def test_create_partition_handler(handler):
    partition_handler = handler.create_partition_handler()

    assert callable(partition_handler)
    assert partition_handler == handler._process_partition


@patch("template_project.libs.aws.dynamodb.loader.handlers.base.get_table")
def test_process_partition_empty_rows(mock_get_table, handler):
    handler._process_partition([])

    mock_get_table.assert_not_called()


@patch("template_project.libs.aws.dynamodb.loader.handlers.base.get_table")
@patch("template_project.libs.aws.dynamodb.loader.handlers.base.get_logger")
def test_process_partition_success(mock_get_logger, mock_get_table, handler):
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    mock_table = Mock()
    mock_batch_writer = Mock()
    mock_context_manager = Mock()
    mock_context_manager.__enter__ = Mock(return_value=mock_batch_writer)
    mock_context_manager.__exit__ = Mock(return_value=None)
    mock_table.batch_writer.return_value = mock_context_manager
    mock_get_table.return_value = mock_table

    # Recrear handler con logger mockeado
    handler = ConcreteHandler("test-job", "us-east-1", "test-table", 400000)

    # Mock rows
    mock_row1 = Mock(spec=Row)
    mock_row1.asDict.return_value = {"pk": "pk1", "sk": "sk1"}
    mock_row2 = Mock(spec=Row)
    mock_row2.asDict.return_value = {"pk": "pk2", "sk": "sk2"}
    rows = [mock_row1, mock_row2]

    handler._process_partition(rows)

    mock_get_table.assert_called_once_with("us-east-1", "test-table")
    mock_table.batch_writer.assert_called_once()

    # Verificar que se procesaron ambos items
    assert mock_row1.asDict.call_count == 1
    assert mock_row2.asDict.call_count == 1

    # Verificar logs de éxito
    mock_logger.info.assert_called_once()
    call_args = mock_logger.info.call_args
    assert call_args[0][0] == "Successfully processed items"
    assert call_args[1]["extra"]["attributes"]["count"] == 2
    assert call_args[1]["extra"]["attributes"]["count_error"] == 0


@patch("template_project.libs.aws.dynamodb.loader.handlers.base.get_table")
def test_process_partition_with_errors(mock_get_table, handler):
    # Crear handler que falla en algunos items
    class FailingHandler(ConcreteHandler):
        def process_item(self, bw, item):
            return item["pk"] != "pk2"  # Falla en pk2

    failing_handler = FailingHandler("test-job", "us-east-1", "test-table", 400000)

    mock_table = Mock()
    mock_batch_writer = Mock()
    mock_context_manager = Mock()
    mock_context_manager.__enter__ = Mock(return_value=mock_batch_writer)
    mock_context_manager.__exit__ = Mock(return_value=None)
    mock_table.batch_writer.return_value = mock_context_manager
    mock_get_table.return_value = mock_table

    # Mock rows
    mock_row1 = Mock(spec=Row)
    mock_row1.asDict.return_value = {"pk": "pk1", "sk": "sk1"}
    mock_row2 = Mock(spec=Row)
    mock_row2.asDict.return_value = {"pk": "pk2", "sk": "sk2"}
    rows = [mock_row1, mock_row2]

    failing_handler._process_partition(rows)

    # Verificar que se procesaron ambos items
    assert mock_row1.asDict.call_count == 1
    assert mock_row2.asDict.call_count == 1


@patch("template_project.libs.aws.dynamodb.loader.handlers.base.get_table")
@patch("template_project.libs.aws.dynamodb.loader.handlers.base.is_retryable_error")
@patch("template_project.libs.aws.dynamodb.loader.handlers.base.time.sleep")
@patch("template_project.libs.aws.dynamodb.loader.handlers.base.get_logger")
def test_process_partition_retryable_error(
    mock_get_logger, mock_sleep, mock_is_retryable, mock_get_table, handler
):
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_is_retryable.return_value = True
    mock_table = Mock()
    mock_table.batch_writer.side_effect = ClientError(
        {"Error": {"Code": "ThrottlingException"}}, "BatchWriteItem"
    )
    mock_get_table.return_value = mock_table

    # Recrear handler con logger mockeado
    handler = ConcreteHandler("test-job", "us-east-1", "test-table", 400000)

    mock_row = Mock(spec=Row)
    mock_row.asDict.return_value = {"pk": "pk1", "sk": "sk1"}
    rows = [mock_row]

    handler._process_partition(rows)

    # Verificar que se intentó retry
    assert mock_sleep.call_count == 6  # max_retries + 1
    mock_is_retryable.assert_called()

    # Verificar logs de warning
    mock_logger.warning.assert_called()


@patch("template_project.libs.aws.dynamodb.loader.handlers.base.get_table")
@patch("template_project.libs.aws.dynamodb.loader.handlers.base.is_retryable_error")
@patch("template_project.libs.aws.dynamodb.loader.handlers.base.get_logger")
def test_process_partition_non_retryable_error(
    mock_get_logger, mock_is_retryable, mock_get_table, handler
):
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_is_retryable.return_value = False
    mock_table = Mock()
    mock_table.batch_writer.side_effect = Exception("Non-retryable error")
    mock_get_table.return_value = mock_table

    # Recrear handler con logger mockeado
    handler = ConcreteHandler("test-job", "us-east-1", "test-table", 400000)

    mock_row = Mock(spec=Row)
    mock_row.asDict.return_value = {"pk": "pk1", "sk": "sk1"}
    rows = [mock_row]

    with pytest.raises(Exception, match="Non-retryable error"):
        handler._process_partition(rows)

    # Verificar que no se hizo retry
    mock_is_retryable.assert_called_once()

    # Verificar log de error
    mock_logger.error.assert_called_once()
    error_call = mock_logger.error.call_args
    assert error_call[0][0] == "Uncontrolled exception in batch_writer context"
