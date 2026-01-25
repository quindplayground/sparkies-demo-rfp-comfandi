"""Job executor module with dependency resolution."""

from typing import Generic, Any, Sequence

from pydantic import ValidationError

from template_project.libs.exceptions import MissingJobDependencyError
from template_project.libs.runner.executors.factory import ExecutorFactory
from template_project.libs.runner.types import P, JobDefinition, Status


class JobRunner(Generic[P]):
    """Executes a list of jobs using specified execution strategies (parallel or sequential)."""

    def __init__(
        self,
        job_definitions: Sequence[JobDefinition | dict[str, Any]],
        executor_factory: ExecutorFactory | None = None,
    ):
        """Initializes the JobRunner with job definitions.

        Args:
            job_definitions: List of job definitions as JobDefinition objects or dictionaries.
            executor_factory: Executor factory instance. If None, a default factory is created.

        Raises:
            ValueError: If job names are not unique.
        """
        self.jobs = self._parse_job_definitions(job_definitions)
        self.executor_factory = executor_factory or ExecutorFactory()

        names = [job.name for job in self.jobs]
        if len(names) != len(set(names)):
            raise ValueError("Job names must be unique")

        self._job_map = {task.name: task for task in self.jobs}

    @staticmethod
    def _parse_job_definitions(
        raw_defs: Sequence[JobDefinition | dict[str, Any]],
    ) -> list[JobDefinition]:
        """Parses raw job definitions into JobDefinition objects.

        Args:
            raw_defs: List of job definitions as JobDefinition objects or dictionaries.

        Returns:
            List of parsed JobDefinition objects.

        Raises:
            ValueError: If a job definition is invalid.
            TypeError: If a job definition is not a dict or JobDefinition.
        """
        parsed: list[JobDefinition] = []

        for idx, d in enumerate(raw_defs):
            if isinstance(d, JobDefinition):
                parsed.append(d)
            elif isinstance(d, dict):
                try:
                    parsed.append(JobDefinition[P](**d))
                except ValidationError as e:
                    raise ValueError(
                        f"Invalid job definition at index {idx}: {e}"
                    ) from e
            else:
                raise TypeError(
                    f"Job definition at index {idx} must be dict or JobDefinition, not {type(d)}"
                )
        return parsed

    def _is_job_ready(self, job_name: str, completed_jobs: set[str]) -> bool:
        """Checks if a job is ready to be executed.

        Args:
            job_name: Name of the job to check.
            completed_jobs: Set of jobs that have been completed.

        Returns:
            True if the job is ready to be executed, False otherwise.
        """
        return all(dep in completed_jobs for dep in self._job_map[job_name].depends_on)

    def _resolve_dependencies(self, job_names: list[str]) -> list[str]:
        """Resolves job dependencies and returns an ordered list of job names.

        Args:
            job_names: List of job names to resolve dependencies for.

        Returns:
            Ordered list of job names with dependencies resolved.

        Raises:
            MissingJobDependencyError: If a dependency is not found in the job map.
            ValueError: If a circular dependency is detected.
        """
        expanded_jobs = set(job_names)
        jobs_to_process = list(job_names)

        while jobs_to_process:
            current_job = jobs_to_process.pop(0)
            job = self._job_map[current_job]

            for dependency in job.depends_on:
                if dependency not in self._job_map:
                    raise MissingJobDependencyError(current_job, dependency)
                if dependency not in expanded_jobs:
                    expanded_jobs.add(dependency)
                    jobs_to_process.append(dependency)

        dependency_graph = {
            name: set(self._job_map[name].depends_on) for name in expanded_jobs
        }

        result = []
        visited = set()
        temp_visited = set()

        def _visit(job_name):
            if job_name in temp_visited:
                raise ValueError(
                    f"Circular dependency detected involving job '{job_name}'"
                )
            if job_name not in visited:
                temp_visited.add(job_name)
                for dependency in dependency_graph[job_name]:
                    _visit(dependency)
                temp_visited.remove(job_name)
                visited.add(job_name)
                result.append(job_name)

        for name in job_names:
            if name not in visited:
                _visit(name)

        return result

    def _get_execution_order(self, jobs: list[str] | str) -> list[str]:
        """Gets the execution order of jobs without executing them.

        Args:
            jobs: List of job names or a single job name.

        Returns:
            Ordered list of job names.

        Raises:
            ValueError: If any of the specified jobs are not found.
        """
        if isinstance(jobs, str):
            jobs = [jobs]

        missing = set(jobs) - self._job_map.keys()

        if missing:
            raise ValueError(f"Jobs not found: {missing}")

        return self._resolve_dependencies(jobs)

    def run(
        self, jobs: list[str] | str, *args, executor: str = "parallel", **kwargs
    ) -> Status:
        """Executes a list of jobs using the specified executor.

        Args:
            jobs: List of job names or a single job name to execute.
            *args: Positional arguments to pass to the executor.
            executor: Type of executor to use ('parallel' or 'sequential'). Defaults to 'parallel'.
            **kwargs: Keyword arguments to pass to the executor.

        Returns:
            Status object representing the result after executing the jobs.

        Raises:
            ValueError: If any of the specified jobs are not found.
        """
        if isinstance(jobs, str):
            jobs = [jobs]

        missing = set(jobs) - self._job_map.keys()

        if missing:
            raise ValueError(f"Jobs not found: {missing}")

        ordered_job_names = self._resolve_dependencies(jobs)
        subset = [self._job_map[name] for name in ordered_job_names]

        executor_instance = self.executor_factory[executor](*args, **kwargs)

        result = executor_instance.execute(subset)

        return result
