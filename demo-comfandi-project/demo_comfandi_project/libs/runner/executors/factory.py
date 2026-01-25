"""Factory module for executor creation."""

from demo_comfandi_project.libs.runner.executors.sequential import SequentialExecutor
from demo_comfandi_project.libs.runner.executors.multithread import MultithreadExecutor
from demo_comfandi_project.libs.runner.executors.base import IExecutor


class ExecutorFactory:
    """Factory class for creating executor classes.

    Attributes:
        map_executor: Dictionary mapping executor names to executor classes.
    """

    map_executor: dict[str, type[IExecutor]] = {
        "sequential": SequentialExecutor,
        "parallel": MultithreadExecutor,
    }

    @classmethod
    def get_executor(cls, executor_name: str) -> type[IExecutor]:
        """Gets an executor class by executor name.

        Args:
            executor_name: Name of the executor to create ('sequential' or 'parallel').

        Returns:
            The requested executor class.

        Raises:
            ValueError: If the executor name is invalid.
        """
        if executor_name not in cls.map_executor:
            raise ValueError(f"Invalid executor name: {executor_name}")
        return cls.map_executor[executor_name]

    def __getitem__(self, executor_name: str) -> type[IExecutor]:
        """Gets an executor class by executor name.

        Args:
            executor_name: Name of the executor to create.

        Returns:
            The requested executor class.

        Raises:
            ValueError: If the executor name is invalid.
        """
        return self.get_executor(executor_name)

    def __contains__(self, executor_name: str) -> bool:
        """Checks if an executor name is in the map.

        Args:
            executor_name: Name of the executor to check.

        Returns:
            True if the executor name is in the map, False otherwise.
        """
        return executor_name in self.map_executor
