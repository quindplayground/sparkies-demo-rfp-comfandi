import pytest
from unittest.mock import Mock, patch
from pyspark.sql import DataFrame

from template_project.libs.aws.dynamodb.loader.loader import DynamoDBLoader
from template_project.libs.aws.dynamodb.loader.handlers.factory import (
    HandlerFactory,
)


@pytest.fixture
def mock_vars_instance():
    mock_vars = Mock()
    mock_vars.vars.output.region = "us-east-1"
    mock_vars.vars.output.table_name = "test-table"
    mock_vars.vars.output.item_size_limit = 400000
    return mock_vars


@pytest.fixture
def mock_dataframes():
    mock_df_write = Mock(spec=DataFrame)
    mock_df_write.rdd.foreachPartition = Mock()
    mock_df_delete = Mock(spec=DataFrame)
    mock_df_delete.rdd.foreachPartition = Mock()
    return {"data_to_write": mock_df_write, "data_to_delete": mock_df_delete}


@pytest.fixture
def mock_handler_factory():
    factory = Mock()
    mock_handler = Mock()
    mock_handler.create_partition_handler.return_value = Mock()
    factory.__getitem__ = Mock(return_value=Mock(return_value=mock_handler))
    return factory


def test_init_with_default_factory(mock_vars_instance):
    loader = DynamoDBLoader("test-job", mock_vars_instance)

    assert loader.job_id == "test-job"
    assert loader.region == "us-east-1"
    assert loader.table_name == "test-table"
    assert loader.item_size_limit == 400000
    assert isinstance(loader.handler_factory, HandlerFactory)


def test_init_with_custom_factory(mock_vars_instance, mock_handler_factory):
    loader = DynamoDBLoader("test-job", mock_vars_instance, mock_handler_factory)

    assert loader.job_id == "test-job"
    assert loader.handler_factory == mock_handler_factory


@patch("template_project.libs.aws.dynamodb.loader.loader.get_logger")
def test_load_first_run(
    mock_get_logger, mock_vars_instance, mock_dataframes, mock_handler_factory
):
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    loader = DynamoDBLoader("test-job", mock_vars_instance, mock_handler_factory)
    loader.load(mock_dataframes, first_run=True)

    # Verificar que se creó el handler de escritura
    mock_handler_factory.__getitem__.assert_called_once_with("portfolio_writer")

    # Verificar que se llamó foreachPartition para escritura
    mock_dataframes["data_to_write"].rdd.foreachPartition.assert_called_once()

    # Verificar que NO se llamó para eliminación
    mock_dataframes["data_to_delete"].rdd.foreachPartition.assert_not_called()

    # Verificar logs - ahora son 4 llamadas: validación inicio, validación fin, carga inicio, carga fin
    assert mock_logger.info.call_count == 4


@patch("template_project.libs.aws.dynamodb.loader.loader.get_logger")
def test_load_not_first_run(
    mock_get_logger, mock_vars_instance, mock_dataframes, mock_handler_factory
):
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    loader = DynamoDBLoader("test-job", mock_vars_instance, mock_handler_factory)
    loader.load(mock_dataframes, first_run=False)

    # Verificar que se crearon ambos handlers
    assert mock_handler_factory.__getitem__.call_count == 2
    mock_handler_factory.__getitem__.assert_any_call("portfolio_writer")
    mock_handler_factory.__getitem__.assert_any_call("delete")

    # Verificar que se llamó foreachPartition para ambos
    mock_dataframes["data_to_write"].rdd.foreachPartition.assert_called_once()
    mock_dataframes["data_to_delete"].rdd.foreachPartition.assert_called_once()

    # Verificar logs - ahora son 4 llamadas: validación inicio, validación fin, carga inicio, carga fin
    assert mock_logger.info.call_count == 4


@patch("template_project.libs.aws.dynamodb.loader.loader.get_logger")
def test_load_logging_attributes(
    mock_get_logger, mock_vars_instance, mock_dataframes, mock_handler_factory
):
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    loader = DynamoDBLoader("test-job", mock_vars_instance, mock_handler_factory)
    loader.load(mock_dataframes, first_run=True)

    # Verificar primer log (validación inicio)
    first_call = mock_logger.info.call_args_list[0]
    assert first_call[0][0] == "Validating dataframes"
    assert first_call[1]["extra"]["attributes"]["job_id"] == "test-job"
    assert first_call[1]["extra"]["attributes"]["table_name"] == "test-table"

    # Verificar segundo log (validación fin)
    second_call = mock_logger.info.call_args_list[1]
    assert second_call[0][0] == "Dataframes validated"

    # Verificar tercer log (carga inicio)
    third_call = mock_logger.info.call_args_list[2]
    assert third_call[0][0] == "Loading items to DynamoDB"
    assert third_call[1]["extra"]["attributes"]["job_id"] == "test-job"
    assert third_call[1]["extra"]["attributes"]["table_name"] == "test-table"
    assert third_call[1]["extra"]["attributes"]["item_size_limit"] == 400000

    # Verificar cuarto log (carga fin)
    fourth_call = mock_logger.info.call_args_list[3]
    assert fourth_call[0][0] == "Items loaded to DynamoDB"
    assert fourth_call[1]["extra"]["attributes"]["first_run"] is True


def test_handler_factory_integration(mock_vars_instance, mock_dataframes):
    # Test con factory real
    loader = DynamoDBLoader("test-job", mock_vars_instance)

    # Verificar que se puede crear handlers
    write_handler_class = loader.handler_factory["portfolio_writer"]
    delete_handler_class = loader.handler_factory["delete"]

    assert write_handler_class is not None
    assert delete_handler_class is not None

    # Verificar que se pueden instanciar
    write_handler = write_handler_class("test-job", "us-east-1", "test-table", 400000)
    delete_handler = delete_handler_class("test-job", "us-east-1", "test-table", 400000)

    assert write_handler is not None
    assert delete_handler is not None
