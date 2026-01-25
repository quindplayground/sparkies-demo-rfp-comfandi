import pytest
from unittest.mock import patch, MagicMock
from template_project.libs.validator_utils.parameters_validation import (
    validate_json_parameters,
)
from template_project.libs.validator_utils.validators import (
    create_version_validator,
    create_filters_structure_validator,
)
from json import JSONDecodeError
from dynaconf import ValidationError, Validator


def test_valid_parameters_with_default_validators():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_vars = MagicMock()
        mock_vars.vars.as_dict.return_value = {
            "version": "1.0.0",
            "filters": {
                "isin": {
                    "codigo_organizacion_ventas": ["CO10", "NN10", "ML10"],
                    "sistema_origen": ["SAPERP", "AMOVIL", "ECOM"],
                    "funcion_interlocutor": ["ZA", "ZB"],
                    "codigo_tipo_material": ["Z090", "Z091"],
                    "clase_de_condicion_zcmu": ["ZCMU"],
                    "clase_de_condicion_zpr1": ["A930"],
                    "tabla_zpr1": ["ZPR1"],
                    "tabla_zcmu": ["ZCMU"],
                    "codigo_grupo_de_cuentas": ["ZDNA"],
                    "codigo_modelo_de_atencion": ["01", "02"],
                }
            },
        }
        mock_get_vars.return_value = mock_vars

        validators = [create_version_validator(), create_filters_structure_validator()]
        success, message = validate_json_parameters(config_paths=None, validators=validators)

        assert success is True
        assert message == "Parameters validated successfully"
        mock_get_vars.assert_called_once_with(env="dev", config_paths=None)


def test_valid_parameters_with_custom_env():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_vars = MagicMock()
        mock_vars.vars.as_dict.return_value = {"version": "2.0.0"}
        mock_get_vars.return_value = mock_vars

        validators = [create_version_validator()]
        success, message = validate_json_parameters(config_paths=None, validators=validators, env="prod")

        assert success is True
        assert message == "Parameters validated successfully"
        mock_get_vars.assert_called_once_with(env="prod", config_paths=None)


def test_valid_parameters_with_custom_config_paths():
    custom_paths = ["/custom/config/path"]

    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_vars = MagicMock()
        mock_vars.vars.as_dict.return_value = {"version": "1.0.0"}
        mock_get_vars.return_value = mock_vars

        validators = [create_version_validator()]
        success, message = validate_json_parameters(config_paths=custom_paths, validators=validators)

        assert success is True
        assert message == "Parameters validated successfully"
        mock_get_vars.assert_called_once_with(env="dev", config_paths=custom_paths)


def test_valid_parameters_with_custom_validators():
    custom_validators = [Validator("custom_field", must_exist=True, is_type_of=str)]

    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_vars = MagicMock()
        mock_vars.vars.as_dict.return_value = {"custom_field": "test"}
        mock_get_vars.return_value = mock_vars

        success, message = validate_json_parameters(
            config_paths=None, validators=custom_validators
        )

        assert success is True
        assert message == "Parameters validated successfully"
        mock_get_vars.assert_called_once_with(env="dev", config_paths=None)


def test_json_decode_error():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_get_vars.side_effect = JSONDecodeError("Invalid JSON", "doc", 0)

        validators = [create_version_validator(), create_filters_structure_validator()]
        success, message = validate_json_parameters(config_paths=None, validators=validators)

        assert success is False
        assert "Error parsing JSON" in message
        assert "Invalid JSON" in message


def test_validation_error():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_vars = MagicMock()
        mock_vars.vars.validators.validate_all.side_effect = ValidationError(
            "Validation failed"
        )
        mock_get_vars.return_value = mock_vars

        validators = [create_version_validator(), create_filters_structure_validator()]
        success, message = validate_json_parameters(config_paths=None, validators=validators)

        assert success is False
        assert "Validation errors found" in message


def test_unexpected_error():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_get_vars.side_effect = Exception("Unexpected error")

        validators = [create_version_validator(), create_filters_structure_validator()]
        success, message = validate_json_parameters(config_paths=None, validators=validators)

        assert success is False
        assert "Unexpected error during validation" in message
        assert "Unexpected error" in message


def test_logging_on_success():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars, patch(
        "template_project.libs.logging.get_logger"
    ) as mock_get_logger:

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_vars = MagicMock()
        mock_vars.vars.as_dict.return_value = {"version": "1.0.0"}
        mock_get_vars.return_value = mock_vars

        validators = [create_version_validator()]
        validate_json_parameters(config_paths=["/test/path"], validators=validators, env="test")

        # Verificar que se llamó info dos veces: una para "Validating parameters" y otra para "Parameters validated successfully"
        assert mock_logger.info.call_count == 2

        # Verificar la primera llamada (Validating parameters)
        first_call = mock_logger.info.call_args_list[0]
        assert "Validating parameters" in first_call[0][0]

        # Verificar la segunda llamada (Parameters validated successfully)
        second_call = mock_logger.info.call_args_list[1]
        assert "Parameters validated successfully" in second_call[0][0]


def test_logging_on_json_error():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars, patch(
        "template_project.libs.logging.get_logger"
    ) as mock_get_logger:

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_get_vars.side_effect = JSONDecodeError("Invalid JSON", "doc", 0)

        validators = [create_version_validator()]
        validate_json_parameters(config_paths=None, validators=validators)

        mock_logger.error.assert_called_once()
        # Verificar el template string y los argumentos por separado
        call_args = mock_logger.error.call_args
        template = call_args[0][0]

        assert "Error parsing JSON" in template


def test_logging_on_validation_error():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars, patch(
        "template_project.libs.logging.get_logger"
    ) as mock_get_logger:

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_vars = MagicMock()
        mock_vars.vars.validators.validate_all.side_effect = ValidationError(
            "Validation failed"
        )
        mock_get_vars.return_value = mock_vars

        validators = [create_version_validator()]
        validate_json_parameters(config_paths=None, validators=validators)

        mock_logger.error.assert_called_once()
        # Verificar el template string y los argumentos por separado
        call_args = mock_logger.error.call_args
        template = call_args[0][0]

        assert "Validation errors found" in template


def test_logging_on_unexpected_error():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars, patch(
        "template_project.libs.logging.get_logger"
    ) as mock_get_logger:

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_get_vars.side_effect = Exception("Unexpected error")

        validators = [create_version_validator()]
        validate_json_parameters(config_paths=None, validators=validators)

        mock_logger.error.assert_called_once()
        # Verificar el template string y los argumentos por separado
        call_args = mock_logger.error.call_args
        template = call_args[0][0]

        assert "Unexpected error during validation" in template


def test_error_message_format():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_get_vars.side_effect = ValueError("Test error")

        validators = [create_version_validator(), create_filters_structure_validator()]
        success, message = validate_json_parameters(config_paths=None, validators=validators)

        assert success is False
        assert "Unexpected error during validation: Test error" in message


def test_validators_structure():
    version_validator = create_version_validator()
    assert version_validator.names == ("version",)
    assert version_validator.must_exist is True
    assert version_validator.is_type_of == str

    filters_validator = create_filters_structure_validator()
    assert filters_validator.names == ("filters",)
    assert filters_validator.must_exist is True
    assert filters_validator.is_type_of == dict
    assert callable(filters_validator.condition)


def test_validators_messages():
    version_validator = create_version_validator()
    assert "semantic version" in version_validator.messages["must_exist_true"]

    filters_validator = create_filters_structure_validator()
    assert "dictionary" in filters_validator.messages["must_exist_true"]
    assert "keys" in filters_validator.messages["condition"]


def test_full_validation_flow():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_vars = MagicMock()
        expected_data = {
            "version": "1.0.0",
            "filters": {
                "isin": {
                    "codigo_organizacion_ventas": ["CO10", "NN10", "ML10"],
                    "sistema_origen": ["SAPERP", "AMOVIL", "ECOM"],
                    "funcion_interlocutor": ["ZA", "ZB"],
                    "codigo_tipo_material": ["Z090", "Z091"],
                    "clase_de_condicion_zcmu": ["ZCMU"],
                    "clase_de_condicion_zpr1": ["A930"],
                    "tabla_zpr1": ["ZPR1"],
                    "tabla_zcmu": ["ZCMU"],
                    "codigo_grupo_de_cuentas": ["ZDNA"],
                    "codigo_modelo_de_atencion": ["01", "02"],
                }
            },
        }
        mock_vars.vars.as_dict.return_value = expected_data
        mock_get_vars.return_value = mock_vars

        validators = [create_version_validator(), create_filters_structure_validator()]
        success, message = validate_json_parameters(
            config_paths=["/prod/config"], validators=validators, env="prod"
        )

        assert success is True
        assert message == "Parameters validated successfully"
        mock_get_vars.assert_called_once_with(env="prod", config_paths=["/prod/config"])


def test_default_parameters():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_vars = MagicMock()
        mock_vars.vars.as_dict.return_value = {"version": "1.0.0"}
        mock_get_vars.return_value = mock_vars

        validators = [create_version_validator(), create_filters_structure_validator()]
        success, message = validate_json_parameters(config_paths=None, validators=validators)

        assert success is True
        assert message == "Parameters validated successfully"
        mock_get_vars.assert_called_once_with(env="dev", config_paths=None)


def test_error_handling_integration():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_get_vars.side_effect = RuntimeError("Integration test error")

        validators = [create_version_validator(), create_filters_structure_validator()]
        success, message = validate_json_parameters(config_paths=None, validators=validators)

        assert success is False
        assert "Unexpected error during validation" in message
        assert "Integration test error" in message


@pytest.mark.parametrize(
    "env,expected_env",
    [
        ("dev", "dev"),
        ("prod", "prod"),
        ("test", "test"),
    ],
)
def test_validate_json_parameters_with_different_environments(env, expected_env):
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_vars = MagicMock()
        mock_vars.vars.as_dict.return_value = {"version": "1.0.0"}
        mock_get_vars.return_value = mock_vars

        validators = [create_version_validator()]
        success, _ = validate_json_parameters(config_paths=None, validators=validators, env=env)

        assert success is True
        mock_get_vars.assert_called_once_with(env=env, config_paths=None)


@pytest.mark.parametrize(
    "error_class,error_message",
    [
        (ValueError, "Value error test"),
        (RuntimeError, "Runtime error test"),
        (TypeError, "Type error test"),
    ],
)
def test_validate_json_parameters_with_different_errors(error_class, error_message):
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_get_vars.side_effect = error_class(error_message)

        validators = [create_version_validator(), create_filters_structure_validator()]
        success, message = validate_json_parameters(config_paths=None, validators=validators)

        assert success is False
        assert "Unexpected error during validation" in message
        assert error_message in message


@pytest.fixture
def mock_vars_resource():
    mock_vars = MagicMock()
    mock_vars.vars.as_dict.return_value = {"version": "1.0.0", "filters": {"isin": {}}}
    return mock_vars


def test_validate_json_parameters_with_fixture(mock_vars_resource):
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_get_vars.return_value = mock_vars_resource

        validators = [create_version_validator(), create_filters_structure_validator()]
        success, message = validate_json_parameters(config_paths=None, validators=validators)

        assert success is True
        assert message == "Parameters validated successfully"


@pytest.mark.slow
def test_validate_json_parameters_performance():
    with patch(
        "template_project.libs.validator_utils.parameters_validation.get_vars_resource"
    ) as mock_get_vars:
        mock_vars = MagicMock()
        mock_vars.vars.as_dict.return_value = {"version": "1.0.0"}
        mock_get_vars.return_value = mock_vars

        for _ in range(100):
            validators = [create_version_validator()]
            success, _ = validate_json_parameters(config_paths=None, validators=validators)
            assert success is True
