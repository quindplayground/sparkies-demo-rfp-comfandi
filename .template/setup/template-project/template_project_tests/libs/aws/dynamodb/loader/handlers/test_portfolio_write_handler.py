import pytest
from unittest.mock import Mock, patch
from boto3.dynamodb.types import Binary

from template_project.libs.aws.dynamodb.loader.handlers.portfolio_write_handler import (
    PortfolioDynamoDBWriteHandler,
)


@pytest.fixture
def handler():
    return PortfolioDynamoDBWriteHandler("test-job", "us-east-1", "test-table", 400000)


@pytest.fixture
def mock_batch_writer():
    return Mock()


def test_compress_productos_with_productos(handler):
    item = {"pk": "pk-value", "sk": "sk-value", "productos": "test data to compress"}

    result = handler._compress_productos(item)

    assert "productos" in result
    assert isinstance(result["productos"], Binary)
    assert result["pk"] == "pk-value"
    assert result["sk"] == "sk-value"


def test_compress_productos_without_productos(handler):
    item = {"pk": "pk-value", "sk": "sk-value"}

    result = handler._compress_productos(item)

    assert result == item
    assert "productos" not in result


def test_compress_productos_empty_string(handler):
    item = {"pk": "pk-value", "productos": ""}

    result = handler._compress_productos(item)

    assert "productos" in result
    assert isinstance(result["productos"], Binary)


def test_process_item_success(handler, mock_batch_writer):
    item = {"pk": "pk-value", "sk": "sk-value", "productos": "test data"}

    result = handler.process_item(mock_batch_writer, item)

    assert result is True
    mock_batch_writer.put_item.assert_called_once()

    # Verificar que se comprimió el item
    call_args = mock_batch_writer.put_item.call_args
    assert "Item" in call_args[1]
    processed_item = call_args[1]["Item"]
    assert isinstance(processed_item["productos"], Binary)


def test_process_item_too_large(handler, mock_batch_writer):
    # Crear un item que será muy grande después de la compresión
    # Usamos datos que no se comprimen bien (datos aleatorios)
    import random
    import string

    large_data = "".join(
        random.choices(string.ascii_letters + string.digits, k=1000000)
    )  # 1MB de datos aleatorios
    item = {"pk": "pk-value", "sk": "sk-value", "productos": large_data}

    result = handler.process_item(mock_batch_writer, item)

    # El item debería ser rechazado por ser muy grande
    assert result is False
    mock_batch_writer.put_item.assert_not_called()


def test_process_item_put_item_exception(handler, mock_batch_writer):
    mock_batch_writer.put_item.side_effect = Exception("DynamoDB error")

    item = {"pk": "pk-value", "sk": "sk-value", "productos": "test data"}

    result = handler.process_item(mock_batch_writer, item)

    assert result is False
    mock_batch_writer.put_item.assert_called_once()


def test_process_item_without_productos(handler, mock_batch_writer):
    item = {"pk": "pk-value", "sk": "sk-value"}

    result = handler.process_item(mock_batch_writer, item)

    assert result is True
    mock_batch_writer.put_item.assert_called_once()

    # Verificar que el item no fue modificado
    call_args = mock_batch_writer.put_item.call_args
    processed_item = call_args[1]["Item"]
    assert processed_item == item


def test_process_item_compression_preserves_other_fields(handler, mock_batch_writer):
    item = {
        "pk": "pk-value",
        "sk": "sk-value",
        "productos": "test data",
        "other_field": "other_value",
    }

    result = handler.process_item(mock_batch_writer, item)

    assert result is True

    call_args = mock_batch_writer.put_item.call_args
    processed_item = call_args[1]["Item"]

    assert processed_item["pk"] == "pk-value"
    assert processed_item["sk"] == "sk-value"
    assert processed_item["other_field"] == "other_value"
    assert isinstance(processed_item["productos"], Binary)


def test_process_item_size_check_uses_compressed_item(handler, mock_batch_writer):
    # Test que el tamaño se calcula después de la compresión
    item = {"pk": "pk-value", "productos": "test data"}

    result = handler.process_item(mock_batch_writer, item)

    # Verificar que se procesó correctamente
    assert result is True
    mock_batch_writer.put_item.assert_called_once()

    # Verificar que el item fue comprimido
    call_args = mock_batch_writer.put_item.call_args
    processed_item = call_args[1]["Item"]
    assert isinstance(processed_item["productos"], Binary)


def test_inheritance(handler):
    # Verificar que hereda correctamente de la clase base
    assert hasattr(handler, "job_id")
    assert hasattr(handler, "region")
    assert hasattr(handler, "table_name")
    assert hasattr(handler, "item_size_limit")
    assert hasattr(handler, "_get_item_keys")
    assert hasattr(handler, "create_partition_handler")
    assert hasattr(handler, "process_item")


def test_compression_level(handler):
    # Test que usa el nivel de compresión correcto
    item = {"productos": "test data"}

    with patch(
        "template_project.libs.aws.dynamodb.loader.handlers.portfolio_write_handler.gzip.compress"
    ) as mock_compress:
        mock_compress.return_value = b"compressed"

        handler._compress_productos(item)

        mock_compress.assert_called_once()
        call_args = mock_compress.call_args
        assert call_args[1]["compresslevel"] == 9
