from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from demo_comfandi_project.libs.aws.dynamodb.truncate_table import truncate_table


def _make_table_mock(pages):
    table = Mock()
    # key_schema para construir Key
    table.key_schema = [{"AttributeName": "pk"}, {"AttributeName": "sk"}]
    # Simular paginación
    scans = []
    for idx, page in enumerate(pages):
        page_dict = {
            "Items": page.get("Items", []),
            "Count": len(page.get("Items", [])),
        }
        if idx < len(pages) - 1:
            page_dict["LastEvaluatedKey"] = {"pk": f"k{idx}", "sk": f"s{idx}"}
        scans.append(page_dict)
    table.scan.side_effect = scans
    # batch_writer como context manager
    batch_ctx = Mock()
    batch_ctx.__enter__ = Mock(return_value=batch_ctx)
    batch_ctx.__exit__ = Mock(return_value=None)
    table.batch_writer.return_value = batch_ctx
    return table, batch_ctx


def test_truncate_table_success_multiple_pages():
    pages = [
        {"Items": [{"pk": "a", "sk": "1"}, {"pk": "b", "sk": "2"}]},
        {"Items": [{"pk": "c", "sk": "3"}]},
    ]
    table, batch_ctx = _make_table_mock(pages)

    ok = truncate_table(table)

    assert ok is True
    # Se llamó scan para primera página y para la siguiente al detectar LastEvaluatedKey
    assert table.scan.call_count == 2
    # Se llamaron delete_item por cada item total
    assert batch_ctx.delete_item.call_count == 3
    # Verificar que se construyeron las keys correctamente
    calls = [call.kwargs["Key"] for call in batch_ctx.delete_item.call_args_list]
    assert {"pk": "a", "sk": "1"} in calls
    assert {"pk": "b", "sk": "2"} in calls
    assert {"pk": "c", "sk": "3"} in calls


def test_truncate_table_client_error_logs_and_returns_false():
    # Preparar tabla que lanza ClientError al borrar
    table, batch_ctx = _make_table_mock([{"Items": [{"pk": "a", "sk": "1"}]}])

    def raise_client_error(*args, **kwargs):
        raise ClientError(
            {"Error": {"Code": "400", "Message": "BadRequest"}}, "DeleteItem"
        )

    batch_ctx.delete_item.side_effect = raise_client_error

    with patch(
        "demo_comfandi_project.libs.aws.dynamodb.truncate_table.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        ok = truncate_table(table)
        assert ok is False
        mock_logger.error.assert_called()
