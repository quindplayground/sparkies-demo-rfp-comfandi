"""JSON parameters validation module.

This module provides functionality to validate configuration parameters
using dynaconf validators. Validators must be provided by the project.

Example:
    Using custom validators:

    ```python
    from demo_comfandi_project.libs.validator_utils import validate_json_parameters
    from demo_comfandi_project.libs.validator_utils.validators import (
        create_filter_validator,
        create_version_validator,
    )

    # Create project-specific validators
    validators = [
        create_version_validator(required=True),
        create_filter_validator("filters.isin.my_field", required=True),
    ]

    success, message = validate_json_parameters(
        config_paths=["config/parameters.json"],
        env="dev",
        validators=validators
    )
    ```
"""

from typing import Literal
from json import JSONDecodeError

from dynaconf import Validator, ValidationError

from demo_comfandi_project.libs.resources import get_vars_resource


def validate_json_parameters(
    config_paths: list[str] | str,
    validators: list[Validator],
    env: Literal["dev", "test", "prod"] = "dev",
) -> tuple[bool, str]:
    """Validates parameters using the provided validators.

    Args:
        config_paths: Custom configuration paths. Can be a single path or a list of paths.
        validators: List of validators to use for validation. Must be provided.
        env: Environment to use for validation. Defaults to 'dev'.

    Returns:
        A tuple containing (success, message) where success is True if validation
        is successful, False if there is an error.

    Example:
        ```python
        from demo_comfandi_project.libs.validator_utils.validators import (
            create_version_validator,
            create_filter_validator,
        )

        validators = [
            create_version_validator(required=True),
            create_filter_validator("filters.isin.my_field", required=True),
        ]

        success, message = validate_json_parameters(
            config_paths=["config/parameters.json"],
            env="dev",
            validators=validators
        )

        if not success:
            print(f"Validation failed: {message}")
        ```
    """
    from demo_comfandi_project.libs.logging import get_logger

    logger = get_logger(__name__, capture_spark_logs=False)

    logger.info(
        "Validating parameters",
        extra={
            "attributes": {
                "operation": "VALIDATE_PARAMETERS",
                "state": "IN_PROGRESS",
                "env": env,
                "config_paths": config_paths,
            }
        },
    )

    try:
        vars_resource = get_vars_resource(env=env, config_paths=config_paths)

        vars_resource.vars.validators.register(*validators)

        vars_resource.vars.validators.validate_all()

        logger.info(
            "Parameters validated successfully",
            extra={
                "attributes": {
                    "operation": "VALIDATE_PARAMETERS",
                    "state": "SUCCESS",
                    "env": env,
                    "config_paths": config_paths,
                    "validated_data": vars_resource.vars.as_dict(),
                }
            },
        )

        return True, "Parameters validated successfully"

    except JSONDecodeError as e:
        logger.error(
            "Error parsing JSON",
            extra={
                "attributes": {
                    "operation": "VALIDATE_PARAMETERS",
                    "state": "ERROR",
                    "env": env,
                    "config_paths": config_paths,
                }
            },
            exc_info=e,
        )
        return False, f"Error parsing JSON: {str(e)}"
    except ValidationError as e:
        accumulative_errors = e.details
        logger.error(
            "Validation errors found",
            extra={
                "attributes": {
                    "operation": "VALIDATE_PARAMETERS",
                    "state": "ERROR",
                    "env": env,
                    "config_paths": config_paths,
                    "accumulative_errors": accumulative_errors,
                }
            },
            exc_info=e,
        )
        return (
            False,
            f"Validation errors found: {[item[1] for item in accumulative_errors]}",
        )
    except Exception as e:
        logger.error(
            "Unexpected error during validation",
            extra={
                "attributes": {
                    "operation": "VALIDATE_PARAMETERS",
                    "state": "ERROR",
                    "env": env,
                    "config_paths": config_paths,
                }
            },
            exc_info=e,
        )
        return False, f"Unexpected error during validation: {str(e)}"
