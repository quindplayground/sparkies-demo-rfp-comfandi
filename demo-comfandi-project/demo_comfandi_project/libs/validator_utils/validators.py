"""Validator utilities module for creating parameter validators.

This module provides helper functions to create validators for configuration
parameters. Projects must implement their own validators using these utilities.

Example:
    To create project-specific validators:

    ```python
    from demo_comfandi_project.libs.validator_utils.validators import (
        create_filter_validator,
        create_string_list_validator,
        create_dict_validator,
    )

    PROJECT_VALIDATORS = [
        # Filter validators
        create_filter_validator("filters.isin.my_field", required=True),
        create_filter_validator("filters.isin.another_field", required=True, uppercase=True),
        
        # String list validators
        create_string_list_validator("my_list_field", required=True),
        
        # Dictionary validators
        create_dict_validator("num_partitions", value_type=int),
        create_dict_validator("restart", value_type=bool, required_keys=["restart_iceberg"]),
    ]
    ```
"""

import re
from dynaconf import Validator


# Generic error messages
FILTERS_REQUIRED_MESSAGE = (
    "'{name}' is required and must be a dictionary with the following keys: "
    "isin, eq, noteq, notin, lt, lte, gt, gte, isnull, isnotnull"
)
VERSION_REQUIRED_MESSAGE = (
    "'{name}' is required and must be a string following the semantic versioning format"
)
UPPERCASE_STRINGS_LIST_MESSAGE = (
    "'{name}' must be a list of strings in uppercase, but got '{value}'"
)
STRINGS_LIST_MESSAGE = (
    "'{name}' must be a list of strings, but got '{value}'"
)
FILTERS_KEYS_MESSAGE = (
    "'{name}' must contain only the following keys: "
    "isin, eq, noteq, notin, lt, lte, gt, gte, isnull, isnotnull, but got '{value}'"
)


def is_uppercase_strings_list(value) -> bool:
    """Validates that the value is a list of uppercase strings.

    Args:
        value: The value to validate.

    Returns:
        True if the value is a list of uppercase strings, False otherwise.
    """
    return isinstance(value, list) and all(
        isinstance(item, str) and item.isupper() for item in value
    )


def is_strings_list(value) -> bool:
    """Validates that the value is a list of strings.

    Args:
        value: The value to validate.

    Returns:
        True if the value is a list of strings, False otherwise.
    """
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def has_valid_filter_keys(value) -> bool:
    """Validates that the filter dictionary has only valid keys.

    Args:
        value: The value to validate.

    Returns:
        True if the value is a dictionary with only valid filter keys, False otherwise.
    """
    valid_keys = {
        "isin",
        "eq",
        "noteq",
        "notin",
        "lt",
        "lte",
        "gt",
        "gte",
        "isnull",
        "isnotnull",
    }
    return isinstance(value, dict) and set(value.keys()).issubset(valid_keys)


def is_dict_of_ints(value) -> bool:
    """Validates that the value is a dictionary of integers.

    Args:
        value: The value to validate.

    Returns:
        True if the value is a dictionary of integers, False otherwise.
    """
    return isinstance(value, dict) and all(
        isinstance(item, int) for item in value.values()
    )


def is_dict_of_bools(value) -> bool:
    """Validates that the value is a dictionary of booleans.

    Args:
        value: The value to validate.

    Returns:
        True if the value is a dictionary of booleans, False otherwise.
    """
    return isinstance(value, dict) and all(
        isinstance(item, bool) for item in value.values()
    )


def create_version_validator(required: bool = True) -> Validator:
    """Creates a validator for semantic versioning format.

    Args:
        required: Whether the field is required. Defaults to True.

    Returns:
        A Validator instance for version validation.

    Example:
        ```python
        validator = create_version_validator(required=True)
        ```
    """
    return Validator(
        "version",
        must_exist=required,
        messages={"must_exist_true": VERSION_REQUIRED_MESSAGE},
        is_type_of=str,
        condition=lambda v: re.fullmatch(
            r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", v
        )
        is not None,
    )


def create_filters_structure_validator(required: bool = True) -> Validator:
    """Creates a validator for the filters structure.

    Args:
        required: Whether the field is required. Defaults to True.

    Returns:
        A Validator instance for filters structure validation.

    Example:
        ```python
        validator = create_filters_structure_validator(required=True)
        ```
    """
    return Validator(
        "filters",
        must_exist=required,
        messages={
            "must_exist_true": FILTERS_REQUIRED_MESSAGE,
            "condition": FILTERS_KEYS_MESSAGE,
        },
        is_type_of=dict,
        condition=has_valid_filter_keys,
    )


def create_filter_validator(
    field_path: str,
    required: bool = True,
    uppercase: bool = True,
) -> Validator:
    """Creates a validator for filter fields.

    This is a helper function to create validators for filter fields (e.g., filters.isin.field_name).

    Args:
        field_path: Dot-separated path to the field (e.g., "filters.isin.my_field").
        required: Whether the field is required. Defaults to True.
        uppercase: Whether the list values must be uppercase. Defaults to True.

    Returns:
        A Validator instance configured for the specified field.

    Example:
        ```python
        validator = create_filter_validator("filters.isin.codigo_organizacion", required=True)
        ```
    """
    condition = is_uppercase_strings_list if uppercase else is_strings_list
    message = UPPERCASE_STRINGS_LIST_MESSAGE if uppercase else STRINGS_LIST_MESSAGE

    return Validator(
        field_path,
        must_exist=required,
        messages={
            "must_exist_true": "{name} is required",
            "condition": message,
        },
        is_type_of=list,
        condition=condition,
    )


def create_string_list_validator(
    field_path: str,
    required: bool = True,
    uppercase: bool = False,
) -> Validator:
    """Creates a validator for string list fields.

    Args:
        field_path: Dot-separated path to the field.
        required: Whether the field is required. Defaults to True.
        uppercase: Whether the list values must be uppercase. Defaults to False.

    Returns:
        A Validator instance configured for the specified field.

    Example:
        ```python
        validator = create_string_list_validator("my_list_field", required=True)
        ```
    """
    condition = is_uppercase_strings_list if uppercase else is_strings_list
    message = UPPERCASE_STRINGS_LIST_MESSAGE if uppercase else STRINGS_LIST_MESSAGE

    return Validator(
        field_path,
        must_exist=required,
        messages={
            "must_exist_true": "{name} is required",
            "condition": message,
        },
        is_type_of=list,
        condition=condition,
    )


def create_dict_validator(
    field_path: str,
    required: bool = True,
    value_type: type = int,
    required_keys: list[str] | None = None,
) -> Validator:
    """Creates a validator for dictionary fields.

    Args:
        field_path: Dot-separated path to the field.
        required: Whether the field is required. Defaults to True.
        value_type: Expected type for dictionary values (int, bool, str, etc.).
            Defaults to int.
        required_keys: List of required keys in the dictionary. If None, no keys
            are required. Defaults to None.

    Returns:
        A Validator instance configured for the specified field.

    Example:
        ```python
        # Dictionary of integers
        validator = create_dict_validator("num_partitions", value_type=int)

        # Dictionary of booleans with required keys
        validator = create_dict_validator(
            "restart",
            value_type=bool,
            required_keys=["restart_iceberg", "restart_dynamodb"]
        )
        ```
    """
    if value_type == int:
        condition = is_dict_of_ints
    elif value_type == bool:
        condition = is_dict_of_bools
    else:
        condition = lambda v: isinstance(v, dict) and all(
            isinstance(item, value_type) for item in v.values()
        )

    messages = {"must_exist_true": f"'{field_path}' is required"}

    if required_keys:
        messages["condition"] = (
            f"'{field_path}' must contain the following keys: {', '.join(required_keys)}"
        )

    return Validator(
        field_path,
        must_exist=required,
        messages=messages,
        is_type_of=dict,
        condition=condition,
    )
