import pytest
from template_project.libs.validator_utils.validators import (
    is_uppercase_strings_list,
    is_strings_list,
    has_valid_filter_keys,
    create_version_validator,
    create_filters_structure_validator,
    create_filter_validator,
)


def test_is_uppercase_strings_list_valid_cases():
    """Test casos válidos para is_uppercase_strings_list."""
    assert is_uppercase_strings_list(["CO10", "NN10", "ML10"]) is True
    assert is_uppercase_strings_list(["SAPERP", "AMOVIL", "ECOM"]) is True
    assert is_uppercase_strings_list(["A"]) is True
    assert is_uppercase_strings_list([]) is True
    assert is_uppercase_strings_list(["ZCMU", "ZPR1"]) is True


def test_is_uppercase_strings_list_invalid_cases():
    """Test casos inválidos para is_uppercase_strings_list."""
    assert is_uppercase_strings_list(["co10", "nn10"]) is False  # minúsculas
    assert is_uppercase_strings_list(["CO10", "nn10"]) is False  # mixto
    assert is_uppercase_strings_list(["CO10", 123]) is False  # no string
    assert is_uppercase_strings_list([123, 456]) is False  # no strings
    assert is_uppercase_strings_list("not_a_list") is False  # no lista
    assert is_uppercase_strings_list(None) is False  # None
    assert is_uppercase_strings_list({"key": "value"}) is False  # dict


def test_is_strings_list_valid_cases():
    """Test casos válidos para is_strings_list."""
    assert is_strings_list(["01", "02", "03"]) is True
    assert is_strings_list(["test", "value"]) is True
    assert is_strings_list(["a", "b", "c"]) is True
    assert is_strings_list([]) is True
    assert is_strings_list(["01"]) is True


def test_is_strings_list_invalid_cases():
    """Test casos inválidos para is_strings_list."""
    assert is_strings_list([123, 456]) is False  # no strings
    assert is_strings_list(["01", 123]) is False  # mixto
    assert is_strings_list([None, "test"]) is False  # None
    assert is_strings_list("not_a_list") is False  # no lista
    assert is_strings_list(None) is False  # None
    assert is_strings_list({"key": "value"}) is False  # dict


def test_has_valid_filter_keys_valid_cases():
    """Test casos válidos para has_valid_filter_keys."""
    assert has_valid_filter_keys({"isin": {}}) is True
    assert has_valid_filter_keys({"eq": {}, "noteq": {}}) is True
    assert (
        has_valid_filter_keys(
            {
                "isin": {},
                "eq": {},
                "noteq": {},
                "notin": {},
                "lt": {},
                "lte": {},
                "gt": {},
                "gte": {},
                "isnull": {},
                "isnotnull": {},
            }
        )
        is True
    )
    assert has_valid_filter_keys({}) is True


def test_has_valid_filter_keys_invalid_cases():
    """Test casos inválidos para has_valid_filter_keys."""
    assert has_valid_filter_keys({"invalid_key": {}}) is False
    assert has_valid_filter_keys({"isin": {}, "invalid": {}}) is False
    assert has_valid_filter_keys({"custom_field": {}}) is False
    assert has_valid_filter_keys("not_a_dict") is False
    assert has_valid_filter_keys(None) is False
    assert has_valid_filter_keys([]) is False


def test_has_valid_filter_keys_edge_cases():
    """Test casos edge para has_valid_filter_keys."""
    # Claves válidas pero con valores no dict
    assert has_valid_filter_keys({"isin": "not_dict"}) is True  # Solo valida claves
    assert has_valid_filter_keys({"eq": None}) is True  # Solo valida claves


def test_create_version_validator():
    """Test creación de validador de version."""
    validator = create_version_validator(required=True)
    assert validator.names == ("version",)
    assert validator.must_exist is True
    assert validator.is_type_of == str
    assert "semantic version" in validator.messages["must_exist_true"]
    assert validator.condition("1.2.3") is True
    assert validator.condition("invalid") is False


def test_create_filters_structure_validator():
    """Test creación de validador de estructura de filters."""
    validator = create_filters_structure_validator(required=True)
    assert validator.names == ("filters",)
    assert validator.must_exist is True
    assert validator.is_type_of == dict
    assert callable(validator.condition)
    assert validator.condition is has_valid_filter_keys


def test_create_filter_validator():
    """Test creación de validador de filtro."""
    validator = create_filter_validator("filters.isin.test_field", required=True, uppercase=True)
    assert validator.names == ("filters.isin.test_field",)
        assert validator.must_exist is True
        assert validator.is_type_of == list
        assert callable(validator.condition)
        assert validator.condition is is_uppercase_strings_list
        assert "uppercase" in validator.messages["condition"]


def test_create_filter_validator_lowercase():
    """Test creación de validador de filtro sin mayúsculas."""
    validator = create_filter_validator("filters.isin.test_field", required=True, uppercase=False)
    assert validator.names == ("filters.isin.test_field",)
    assert validator.condition is is_strings_list
    assert "uppercase" not in validator.messages["condition"]


def test_filters_validator_with_valid_keys():
    """Test validador de filters con claves válidas."""
    validator = create_filters_structure_validator()
    valid_filters = [
        {"isin": {}},
        {"eq": {}, "noteq": {}},
        {"isin": {}, "lt": {}, "gt": {}},
    ]

    for filters in valid_filters:
        assert validator.condition(filters) is True


def test_filters_validator_with_invalid_keys():
    """Test validador de filters con claves inválidas."""
    validator = create_filters_structure_validator()
    invalid_filters = [
        {"invalid_key": {}},
        {"isin": {}, "custom_field": {}},
        {"unknown": {}, "another_unknown": {}},
    ]

    for filters in invalid_filters:
        assert validator.condition(filters) is False


@pytest.mark.parametrize(
    "value,expected",
    [
        (["CO10", "NN10"], True),
        (["co10", "nn10"], False),
        (["CO10", "nn10"], False),
        (["CO10", 123], False),
        ([], True),
        (["A"], True),
    ],
)
def test_uppercase_validation_parametrized(value, expected):
    """Test parametrizado para validación de mayúsculas."""
    assert is_uppercase_strings_list(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (["01", "02"], True),
        (["test", "value"], True),
        ([123, 456], False),
        (["01", 123], False),
        ([], True),
        (["single"], True),
    ],
)
def test_strings_validation_parametrized(value, expected):
    """Test parametrizado para validación de strings."""
    assert is_strings_list(value) == expected
