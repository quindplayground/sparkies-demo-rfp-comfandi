"""Validator utilities module for creating and using parameter validators.

This module provides utilities to create validators and validate configuration
parameters. Projects must implement their own validators using the helper functions.

To implement project-specific validators:

1. Import the helper functions:

    ```python
    from demo_comfandi_project.libs.validator_utils.validators import (
        create_filter_validator,
        create_string_list_validator,
        create_dict_validator,
        create_version_validator,
        create_filters_structure_validator,
    )
    ```

2. Create your project-specific validators:

    ```python
    PROJECT_VALIDATORS = [
        # Common validators
        create_version_validator(required=True),
        create_filters_structure_validator(required=True),
        
        # Filter validators (for filters.isin.field_name, filters.eq.field_name, etc.)
        create_filter_validator("filters.isin.codigo_organizacion", required=True),
        create_filter_validator("filters.isin.funcion_interlocutor", required=True, uppercase=True),
        
        # String list validators (for any list of strings)
        create_string_list_validator("my_list_field", required=True, uppercase=False),
        
        # Dictionary validators (for dictionaries with specific value types)
        create_dict_validator("num_partitions", value_type=int),
        create_dict_validator("restart", value_type=bool, required_keys=["restart_iceberg"]),
    ]
    ```

3. Use in validation:

    ```python
    from demo_comfandi_project.libs.validator_utils import validate_json_parameters

    success, message = validate_json_parameters(
        config_paths=["config/parameters.json"],
        env="dev",
        validators=PROJECT_VALIDATORS
    )
    ```

For more examples and detailed documentation, see the docstrings in:
- `validators.py`: Helper functions for creating validators
- `parameters_validation.py`: Validation execution logic
"""

from demo_comfandi_project.libs.validator_utils.parameters_validation import (
    validate_json_parameters,
)
from demo_comfandi_project.libs.validator_utils.validators import (
    create_filter_validator,
    create_string_list_validator,
    create_dict_validator,
    create_version_validator,
    create_filters_structure_validator,
    is_uppercase_strings_list,
    is_strings_list,
    has_valid_filter_keys,
    is_dict_of_ints,
    is_dict_of_bools,
)

__all__ = [
    "validate_json_parameters",
    "create_filter_validator",
    "create_string_list_validator",
    "create_dict_validator",
    "create_version_validator",
    "create_filters_structure_validator",
    "is_uppercase_strings_list",
    "is_strings_list",
    "has_valid_filter_keys",
    "is_dict_of_ints",
    "is_dict_of_bools",
]
