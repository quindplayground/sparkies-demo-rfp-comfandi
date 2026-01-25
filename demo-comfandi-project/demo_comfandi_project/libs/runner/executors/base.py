"""Base executor module for job execution."""

from abc import ABC, abstractmethod
from typing import Any

from demo_comfandi_project.libs.runner.types import JobDefinition, Status


class IExecutor(ABC):
    """Interface for job executors that defines the contract for execution logic."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the executor with optional arguments.

        Args:
            *args: Variable positional arguments to store for subclasses.
            **kwargs: Variable keyword arguments to store for subclasses.
        """
        self.init_args: tuple = args
        self.init_kwargs: dict[str, Any] = kwargs

    @abstractmethod
    def execute(self, jobs: list[JobDefinition]) -> Status:
        """Executes a list of job definitions.

        Args:
            jobs: List of job definitions to execute.

        Returns:
            Aggregated status of the job execution.
        """
        pass
