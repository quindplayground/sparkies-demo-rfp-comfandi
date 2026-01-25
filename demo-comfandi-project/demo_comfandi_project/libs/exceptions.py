"""Custom exceptions module for the Tech Eval Project."""


class BaseProjectException(Exception):
    """Base class for all project exceptions."""

    pass


class TableNotFoundError(BaseProjectException):
    """Exception raised when a specified table is not found.

    Args:
        table_name: Name of the table not found.
    """

    def __init__(self, table_name: str):
        super().__init__(f"Table '{table_name}' not found.")
        self.table_name = table_name


class ColumnsNotMatchedError(BaseProjectException):
    """Exception raised when expected columns do not match actual columns.

    Args:
        expected: Set of expected columns.
        actual: Set of actual columns.
    """

    def __init__(self, expected: set, actual: set):
        super().__init__(f"Expected columns {expected} do not match actual columns {actual}.")
        self.expected = expected
        self.actual = actual


class UpdateControlTableError(BaseProjectException):
    """Exception raised when there's an error updating the control table.

    Args:
        message: Error message.
    """

    def __init__(self, message: str):
        super().__init__(f"Error updating control table: {message}")
        self.message = message


class MissingJobDependencyError(BaseProjectException):
    """Exception raised when a job dependency is not found in the provided job list.

    Args:
        job_name: Name of the job.
        missing_dependency: Missing dependency.
    """

    def __init__(self, job_name: str, missing_dependency: str):
        super().__init__(
            f"Job '{job_name}' depends on '{missing_dependency}', but the dependency was not found in the provided job list."
        )
        self.job_name = job_name
        self.missing_dependency = missing_dependency


class ValidationError(BaseProjectException):
    """Exception raised when a validation error occurs.

    Args:
        message: Validation error message.
    """

    def __init__(self, message: str):
        super().__init__(f"Validation error: {message}")
        self.message = message
