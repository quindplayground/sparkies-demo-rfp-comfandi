"""Decorator for error handling."""

from functools import wraps
from typing import Callable, Any

from demo_comfandi_project.libs.error_handler.handler import get_error_handler
from demo_comfandi_project.libs.error_handler.models import ErrorArgs
from demo_comfandi_project.libs.logging.logger import get_logger


def handle_errors(func: Callable | None = None) -> Callable | Any:
    """Decorate a function with error handling and delegation to a custom error handler.

    Args:
        func: The function to decorate. If None, returns the decorator itself.

    Returns:
        The decorated function, or the decorator if used without arguments.
    """
    logger = get_logger(__name__)

    def decorator(func: Callable) -> Callable:
        """Wrap the original function with error handling.

        Args:
            func: The function to decorate.

        Returns:
            The decorated function with error handling.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Handle errors in the decorated function.

            Args:
                *args: Positional arguments for the function.
                **kwargs: Keyword arguments for the function.

            Returns:
                Result of the original function or None if it fails.
            """
            error_args = kwargs.pop("error_args", None)

            if error_args and isinstance(error_args, dict):
                error_args.setdefault("step", func.__name__)
                error_args = ErrorArgs(**error_args)

            try:
                result = func(*args, **kwargs)

                if error_args:
                    logger.info(
                        "Step completed successfully",
                        extra={
                            "attributes": {
                                "step": error_args.step,
                                "source": error_args.source,
                                "state": "SUCCESS",
                            }
                        },
                    )

                return result
            except Exception as err:
                if not error_args:
                    raise err

                handler = get_error_handler(
                    error_args.spark,
                    error_args.error_path,
                    error_args.extractor,
                    error_args.writer,
                )

                handler.handle_error(
                    spark=error_args.spark,
                    error=err,
                    source=error_args.source,
                    step=error_args.step,
                )

                logger.error(
                    "Step failed, writing error log to error path",
                    extra={
                        "attributes": {
                            "step": error_args.step,
                            "source": error_args.source,
                            "error_path": error_args.error_path,
                            "state": "ERROR",
                        }
                    },
                )

                if error_args.fail_fast:
                    raise err

                return None

        return wrapper

    if func is None:
        return decorator
    return decorator(func)
