"""Types module for the job runner system."""

from collections.abc import Callable
from typing import Generic, Any, Literal

from pydantic import BaseModel, computed_field
from typing_extensions import ParamSpec


P = ParamSpec('P')


class Status(BaseModel):
    """Represents the status of a process with message and HTTP-like status code.

    Attributes:
        status_value: The status value as a string literal.
        message: The status message.
        code: Computed HTTP-like status code based on status_value.
    """

    status_value: Literal[
        "OK", "CREATED", "ACCEPTED", "BAD REQUEST", "UNAUTHORIZED", "FORBIDDEN",
        "NOT FOUND", "ERROR", "UNPROCESSABLE ENTITY", "CONFLICT", "NOT CONTENT"
    ]
    message: str

    @computed_field
    def code(self) -> int:
        """Automatically sets the status code based on the status string.

        Returns:
            The HTTP-like status code corresponding to the status_value.
        """
        status_code_mapping = {
            "OK": 200,
            "CREATED": 201,
            "ACCEPTED": 202,
            "NOT CONTENT": 204,
            "BAD REQUEST": 400,
            "UNAUTHORIZED": 401,
            "FORBIDDEN": 403,
            "NOT FOUND": 404,
            "UNPROCESSABLE ENTITY": 422,
            "CONFLICT": 409,
            "ERROR": 500
        }
        return status_code_mapping[self.status_value]


class JobDefinition(BaseModel, Generic[P]):
    """Defines a job with a name, a callable, and its arguments.

    Attributes:
        name: Name of the job.
        job: Callable that executes the job and returns a Status.
        args: Dictionary of arguments to pass to the job callable.
        depends_on: List of job names that this job depends on.
    """
    name: str
    job: Callable[P, Status]
    args: dict[str, Any]
    depends_on: list[str] = []


class JobResult(BaseModel):
    """Stores the result or error of a job execution.

    Attributes:
        job_name: Name of the job that was executed.
        status: Status object representing the execution result.
    """

    job_name: str
    status: Status
