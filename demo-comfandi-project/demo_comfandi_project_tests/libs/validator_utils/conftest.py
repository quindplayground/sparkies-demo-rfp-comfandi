import pytest
from unittest.mock import MagicMock
from demo_comfandi_project.libs.validator_utils.validators import (
    create_version_validator,
    create_filters_structure_validator,
)


@pytest.fixture
def mock_vars_resource():
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
    return mock_vars


@pytest.fixture
def mock_vars_resource_minimal():
    mock_vars = MagicMock()
    mock_vars.vars.as_dict.return_value = {"version": "1.0.0", "filters": {"isin": {}}}
    return mock_vars


@pytest.fixture
def custom_validators():
    from dynaconf import Validator

    return [
        Validator("custom_field", must_exist=True, is_type_of=str),
        Validator("number_field", must_exist=True, is_type_of=int),
    ]


@pytest.fixture
def default_validators():
    return [
        create_version_validator(required=True),
        create_filters_structure_validator(required=True),
    ]


@pytest.fixture
def sample_config_paths():
    return ["/custom/config/path", "/another/config/path"]


@pytest.fixture
def sample_environments():
    return ["dev", "prod", "test", "staging"]


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marca tests que tardan mucho en ejecutarse"
    )
    config.addinivalue_line("markers", "integration: marca tests de integración")
    config.addinivalue_line("markers", "unit: marca tests unitarios")


def pytest_collection_modifyitems(config, items):
    _ = config

    for item in items:
        if "integration" in item.name or "Integration" in item.name:
            item.add_marker(pytest.mark.integration)

        if "test_" in item.name and "integration" not in item.name.lower():
            item.add_marker(pytest.mark.unit)

        if "performance" in item.name:
            item.add_marker(pytest.mark.slow)
