import pytest
from unittest.mock import Mock, patch
from boto3.dynamodb.types import Binary

from template_project.libs.aws.dynamodb.loader.handlers.comercial_write_handler import (
    ComercialDynamoDBWriteHandler,
)


@pytest.fixture
def handler():
    return ComercialDynamoDBWriteHandler("test-job", "us-east-1", "test-table", 400000)


@pytest.fixture
def mock_batch_writer():
    return Mock()


def test_compress_material_with_material(handler):
    item = {"pk": "pk-value", "sk": "sk-value", "material": "test-material-data"}

    result = handler._compress_productos(item)

    assert "material" in result
    assert isinstance(result["material"], Binary)
    assert result["pk"] == "pk-value"
    assert result["sk"] == "sk-value"


def test_compress_material_without_material(handler):
    item = {"pk": "pk-value", "sk": "sk-value", "other_field": "other-value"}

    result = handler._compress_productos(item)

    assert result == item


def test_compress_material_empty_string(handler):
    item = {"pk": "pk-value", "sk": "sk-value", "material": ""}

    result = handler._compress_productos(item)

    assert "material" in result
    assert isinstance(result["material"], Binary)


def test_process_item_success(handler, mock_batch_writer):
    item = {"pk": "pk-value", "sk": "sk-value", "material": "test-material-data"}

    result = handler.process_item(mock_batch_writer, item)

    assert result is True
    mock_batch_writer.put_item.assert_called_once()
    put_item_call = mock_batch_writer.put_item.call_args[1]["Item"]
    assert "material" in put_item_call
    assert isinstance(put_item_call["material"], Binary)


def test_process_item_too_large(handler, mock_batch_writer):
    # Mockear _get_item_size para simular un item muy grande
    with patch.object(handler, "_get_item_size", return_value=500000):
        item = {"pk": "pk-value", "sk": "sk-value", "material": "test-material-data"}

        result = handler.process_item(mock_batch_writer, item)

        # Debería retornar False por item muy grande
        assert result is False
        mock_batch_writer.put_item.assert_not_called()


def test_process_item_put_item_exception(handler, mock_batch_writer):
    item = {"pk": "pk-value", "sk": "sk-value", "material": "test-material-data"}

    mock_batch_writer.put_item.side_effect = Exception("DynamoDB Error")

    result = handler.process_item(mock_batch_writer, item)

    # Debería retornar False por excepción
    assert result is False
    mock_batch_writer.put_item.assert_called_once()


def test_process_item_without_material(handler, mock_batch_writer):
    item = {"pk": "pk-value", "sk": "sk-value", "other_field": "other-value"}

    # Mockear _get_item_size para evitar el KeyError
    with patch.object(handler, "_get_item_size", return_value=100):
        result = handler.process_item(mock_batch_writer, item)

    assert result is True
    mock_batch_writer.put_item.assert_called_once_with(Item=item)


def test_process_item_compression_preserves_other_fields(handler):
    item = {
        "pk": "pk-value",
        "sk": "sk-value",
        "material": "test-material-data",
        "other_field": "other-value",
        "another_field": 123,
    }

    result = handler._compress_productos(item)

    assert result["pk"] == "pk-value"
    assert result["sk"] == "sk-value"
    assert result["other_field"] == "other-value"
    assert result["another_field"] == 123
    assert isinstance(result["material"], Binary)


def test_process_item_size_check_uses_compressed_item(handler, mock_batch_writer):
    item = {"pk": "pk-value", "sk": "sk-value", "material": "test-material-data"}

    result = handler.process_item(mock_batch_writer, item)

    # Verificar que se llamó put_item con el item comprimido
    assert result is True
    mock_batch_writer.put_item.assert_called_once()
    put_item_call = mock_batch_writer.put_item.call_args[1]["Item"]
    assert isinstance(put_item_call["material"], Binary)


def test_inheritance():
    """Test que ComercialDynamoDBWriteHandler hereda de DynamoDBOperationHandler."""
    from template_project.libs.aws.dynamodb.loader.handlers.base import (
        DynamoDBOperationHandler,
    )

    handler = ComercialDynamoDBWriteHandler(
        "test-job", "us-east-1", "test-table", 400000
    )
    assert isinstance(handler, DynamoDBOperationHandler)


def test_compression_level():
    """Test que la compresión usa el nivel correcto."""
    handler = ComercialDynamoDBWriteHandler(
        "test-job", "us-east-1", "test-table", 400000
    )

    item = {"pk": "pk-value", "sk": "sk-value", "material": "test-material-data"}

    result = handler._compress_productos(item)

    # Verificar que el material está comprimido
    assert isinstance(result["material"], Binary)

    # Verificar que se puede descomprimir correctamente
    import gzip

    decompressed = gzip.decompress(result["material"].value).decode("utf-8")
    assert decompressed == "test-material-data"
