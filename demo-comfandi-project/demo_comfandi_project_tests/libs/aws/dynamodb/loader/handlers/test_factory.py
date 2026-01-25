import pytest
from demo_comfandi_project.libs.aws.dynamodb.loader.handlers.factory import (
    HandlerFactory,
)
from demo_comfandi_project.libs.aws.dynamodb.loader.handlers.portfolio_write_handler import (
    PortfolioDynamoDBWriteHandler,
)
from demo_comfandi_project.libs.aws.dynamodb.loader.handlers.comercial_write_handler import (
    ComercialDynamoDBWriteHandler,
)
from demo_comfandi_project.libs.aws.dynamodb.loader.handlers.delete_handler import (
    DynamoDBDeleteHandler,
)


def test_map_handler_contains_correct_handlers():
    assert "portfolio_writer" in HandlerFactory.map_handler
    assert "comercial_writer" in HandlerFactory.map_handler
    assert "delete" in HandlerFactory.map_handler
    assert (
        HandlerFactory.map_handler["portfolio_writer"] == PortfolioDynamoDBWriteHandler
    )
    assert (
        HandlerFactory.map_handler["comercial_writer"] == ComercialDynamoDBWriteHandler
    )
    assert HandlerFactory.map_handler["delete"] == DynamoDBDeleteHandler


def test_get_handler_comercial_write():
    handler_class = HandlerFactory.get_handler("comercial_writer")
    assert handler_class == ComercialDynamoDBWriteHandler


def test_get_handler_write():
    handler_class = HandlerFactory.get_handler("portfolio_writer")
    assert handler_class == PortfolioDynamoDBWriteHandler


def test_get_handler_delete():
    handler_class = HandlerFactory.get_handler("delete")
    assert handler_class == DynamoDBDeleteHandler


def test_get_handler_invalid_name():
    with pytest.raises(ValueError, match="Invalid handler name: invalid"):
        HandlerFactory.get_handler("invalid")


def test_getitem_comercial_write():
    factory = HandlerFactory()
    handler_class = factory["comercial_writer"]
    assert handler_class == ComercialDynamoDBWriteHandler


def test_getitem_write():
    factory = HandlerFactory()
    handler_class = factory["portfolio_writer"]
    assert handler_class == PortfolioDynamoDBWriteHandler


def test_getitem_delete():
    factory = HandlerFactory()
    handler_class = factory["delete"]
    assert handler_class == DynamoDBDeleteHandler


def test_getitem_invalid_name():
    factory = HandlerFactory()
    with pytest.raises(ValueError, match="Invalid handler name: invalid"):
        factory["invalid"]


def test_contains_comercial_write():
    factory = HandlerFactory()
    assert "comercial_writer" in factory


def test_contains_write():
    factory = HandlerFactory()
    assert "portfolio_writer" in factory
    assert "delete" in factory
    assert "invalid" not in factory


def test_contains_delete():
    factory = HandlerFactory()
    assert "delete" in factory


def test_contains_invalid():
    factory = HandlerFactory()
    assert "invalid" not in factory


def test_factory_creates_instances():
    factory = HandlerFactory()

    # Test que se pueden crear instancias
    write_handler = factory["portfolio_writer"]("job-1", "us-east-1", "table-1", 400000)
    comercial_handler = factory["comercial_writer"](
        "job-1", "us-east-1", "table-1", 400000
    )
    delete_handler = factory["delete"]("job-1", "us-east-1", "table-1", 400000)

    assert isinstance(write_handler, PortfolioDynamoDBWriteHandler)
    assert isinstance(comercial_handler, ComercialDynamoDBWriteHandler)
    assert isinstance(delete_handler, DynamoDBDeleteHandler)


def test_factory_instances_have_correct_attributes():
    factory = HandlerFactory()

    write_handler = factory["portfolio_writer"]("job-1", "us-east-1", "table-1", 400000)
    comercial_handler = factory["comercial_writer"](
        "job-1", "us-east-1", "table-1", 400000
    )
    delete_handler = factory["delete"]("job-1", "us-east-1", "table-1", 400000)

    # Verificar atributos comunes
    assert write_handler.job_id == "job-1"
    assert write_handler.region == "us-east-1"
    assert write_handler.table_name == "table-1"
    assert write_handler.item_size_limit == 400000

    assert comercial_handler.job_id == "job-1"
    assert comercial_handler.region == "us-east-1"
    assert comercial_handler.table_name == "table-1"
    assert comercial_handler.item_size_limit == 400000

    assert delete_handler.job_id == "job-1"
    assert delete_handler.region == "us-east-1"
    assert delete_handler.table_name == "table-1"
    assert delete_handler.item_size_limit == 400000


def test_factory_with_custom_parameters():
    factory = HandlerFactory()

    write_handler = factory["portfolio_writer"](
        "job-1", "us-west-2", "custom-table", 200000, max_retries=3, base_wait=2.0
    )

    assert write_handler.job_id == "job-1"
    assert write_handler.region == "us-west-2"
    assert write_handler.table_name == "custom-table"
    assert write_handler.item_size_limit == 200000
    assert write_handler.max_retries == 3
    assert write_handler.base_wait == 2.0
