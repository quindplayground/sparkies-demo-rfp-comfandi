import pytest
from unittest.mock import Mock, patch

from demo_comfandi_project.libs.aws.dynamodb.loader.handlers.delete_handler import (
    DynamoDBDeleteHandler,
)


@pytest.fixture
def handler():
    return DynamoDBDeleteHandler("test-job", "us-east-1", "test-table", 400000)


@pytest.fixture
def mock_batch_writer():
    return Mock()


def test_process_item_success(handler, mock_batch_writer):
    item = {"pk": "pk-value", "sk": "sk-value", "other_field": "other-value"}

    result = handler.process_item(mock_batch_writer, item)

    assert result is True
    mock_batch_writer.delete_item.assert_called_once_with(
        Key={"pk": "pk-value", "sk": "sk-value"}
    )


def test_process_item_success_with_additional_fields(handler, mock_batch_writer):
    item = {
        "pk": "pk-value",
        "sk": "sk-value",
        "gsi1_pk": "gsi1_pk-value",
        "gsi1_sk": "gsi1_sk-value",
        "other_field": "other-value",
    }

    result = handler.process_item(mock_batch_writer, item)

    assert result is True
    # Verificar que solo se usan pk y sk para la eliminación
    mock_batch_writer.delete_item.assert_called_once_with(
        Key={"pk": "pk-value", "sk": "sk-value"}
    )


@patch("demo_comfandi_project.libs.aws.dynamodb.loader.handlers.base.get_logger")
def test_process_item_exception(mock_get_logger, handler, mock_batch_writer):
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    mock_batch_writer.delete_item.side_effect = Exception("DynamoDB error")

    # Recrear handler con logger mockeado
    handler = DynamoDBDeleteHandler("test-job", "us-east-1", "test-table", 400000)

    item = {"pk": "pk-value", "sk": "sk-value"}

    result = handler.process_item(mock_batch_writer, item)

    assert result is False
    mock_batch_writer.delete_item.assert_called_once()

    # Verificar log de error
    mock_logger.error.assert_called_once()
    error_call = mock_logger.error.call_args
    assert error_call[0][0] == "Error deleting item"
    assert error_call[1]["extra"]["attributes"]["job_id"] == "test-job"
    assert error_call[1]["extra"]["attributes"]["keys"] == {
        "pk": "pk-value",
        "sk": "sk-value",
    }
    assert error_call[1]["exc_info"] is not None


def test_process_item_missing_pk(handler, mock_batch_writer):
    item = {"sk": "sk-value", "other_field": "other-value"}

    with pytest.raises(KeyError):
        handler.process_item(mock_batch_writer, item)


def test_process_item_missing_sk(handler, mock_batch_writer):
    item = {"pk": "pk-value", "other_field": "other-value"}

    with pytest.raises(KeyError):
        handler.process_item(mock_batch_writer, item)


def test_process_item_empty_keys(handler, mock_batch_writer):
    item = {"pk": "", "sk": "", "other_field": "other-value"}

    result = handler.process_item(mock_batch_writer, item)

    assert result is True
    mock_batch_writer.delete_item.assert_called_once_with(Key={"pk": "", "sk": ""})


def test_process_item_none_keys(handler, mock_batch_writer):
    item = {"pk": None, "sk": None, "other_field": "other-value"}

    result = handler.process_item(mock_batch_writer, item)

    assert result is True
    mock_batch_writer.delete_item.assert_called_once_with(Key={"pk": None, "sk": None})


def test_process_item_different_key_types(handler, mock_batch_writer):
    item = {"pk": 123, "sk": 456.789, "other_field": "other-value"}

    result = handler.process_item(mock_batch_writer, item)

    assert result is True
    mock_batch_writer.delete_item.assert_called_once_with(
        Key={"pk": 123, "sk": 456.789}
    )


def test_inheritance(handler):
    # Verificar que hereda correctamente de la clase base
    assert hasattr(handler, "job_id")
    assert hasattr(handler, "region")
    assert hasattr(handler, "table_name")
    assert hasattr(handler, "item_size_limit")
    assert hasattr(handler, "_get_item_keys")
    assert hasattr(handler, "create_partition_handler")
    assert hasattr(handler, "process_item")


def test_process_item_preserves_original_item(handler, mock_batch_writer):
    # Test que el item original no se modifica
    original_item = {"pk": "pk-value", "sk": "sk-value", "other_field": "other-value"}
    item_copy = original_item.copy()

    handler.process_item(mock_batch_writer, item_copy)

    # El item no debería haberse modificado
    assert item_copy == original_item


def test_process_item_key_extraction(handler, mock_batch_writer):
    # Test que se extraen correctamente solo pk y sk
    item = {
        "pk": "primary-key",
        "sk": "sort-key",
        "gsi1_pk": "gsi1_primary",
        "gsi1_sk": "gsi1_sort",
        "gsi2_pk": "gsi2_primary",
        "gsi2_sk": "gsi2_sort",
        "data_field": "data_value",
        "another_field": "another_value",
    }

    result = handler.process_item(mock_batch_writer, item)

    assert result is True

    # Verificar que solo se pasaron pk y sk a delete_item
    call_args = mock_batch_writer.delete_item.call_args
    key = call_args[1]["Key"]

    assert key == {"pk": "primary-key", "sk": "sort-key"}
    assert len(key) == 2
    assert "gsi1_pk" not in key
    assert "gsi1_sk" not in key
    assert "gsi2_pk" not in key
    assert "gsi2_sk" not in key
    assert "data_field" not in key
    assert "another_field" not in key
