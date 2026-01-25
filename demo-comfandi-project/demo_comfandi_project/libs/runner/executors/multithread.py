from typing import Generic
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

from demo_comfandi_project.libs.runner.executors.base import IExecutor
from demo_comfandi_project.libs.runner.executors.sequential import SequentialExecutor
from demo_comfandi_project.libs.runner.types import JobDefinition, P, Status, JobResult
from demo_comfandi_project.libs.logging import get_logger


class MultithreadExecutor(Generic[P], IExecutor):
    """Executes jobs in parallel using a thread pool.

    If jobs have dependencies, automatically switches to sequential execution
    to ensure proper dependency handling.
    """

    def __init__(self, max_workers: int | None = None):
        """Initializes the multithread executor.

        Args:
            max_workers: Maximum number of worker threads. If None, uses default.
        """
        super().__init__(max_workers=max_workers)
        self.max_workers = self.init_kwargs.get("max_workers")
        self.logger = get_logger(self.__class__.__name__)

    def execute(self, jobs: list[JobDefinition]) -> Status:
        """Executes a list of jobs concurrently using threads.

        Args:
            jobs: List of job definitions to execute.

        Returns:
            Aggregated execution status. Returns 'ERROR' if any job fails.
        """
        self.logger.info(
            "Starting multithread executor with jobs",
            extra={
                "attributes": {
                    "executor": "multithread",
                    "status": "IN_PROGRESS",
                    "job_names": [job.name for job in jobs],
                }
            },
        )

        has_dependencies = any(job.depends_on for job in jobs)

        if has_dependencies:
            self.logger.warning(
                "Multithread executor detected jobs with dependencies. Switching to sequential execution for proper dependency handling.",
                extra={
                    "attributes": {
                        "operation": "MULTITHREAD_EXECUTOR_WITH_DEPENDENCIES",
                        "executor": "sequential",
                        "status": "IN_PROGRESS",
                        "job_names": [job.name for job in jobs],
                    }
                },
            )

            sequential_executor = SequentialExecutor()
            return sequential_executor.execute(jobs)

        exceptions: list[JobResult] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_name = {
                executor.submit(self._run_job, job): job.name for job in jobs
            }

            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    result = future.result()
                    job_result = JobResult(job_name=name, status=result)
                    self.logger.info(
                        "Job completed successfully",
                        extra={
                            "attributes": {
                                "operation": "MULTITHREAD_EXECUTOR",
                                "job_name": name,
                                "status": "DONE",
                                "result": job_result.model_dump_json(),
                            }
                        },
                    )
                except Exception as e:
                    error_message = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                    job_result = JobResult(
                        job_name=name,
                        status=Status(status_value="ERROR", message=error_message),
                    )
                    self.logger.error(
                        "Error executing job",
                        extra={
                            "attributes": {
                                "operation": "MULTITHREAD_EXECUTOR",
                                "job_name": name,
                                "status": "ERROR",
                                "result": job_result.model_dump_json(),
                            }
                        },
                        exc_info=e,
                    )

                    exceptions.append(job_result)

        if exceptions:
            results = [model.model_dump_json() for model in exceptions]

            self.logger.error(
                "Errors occurred during job execution",
                extra={
                    "attributes": {
                        "operation": "MULTITHREAD_EXECUTOR",
                        "job_names": [model.job_name for model in exceptions],
                        "status": "ERROR",
                        "results": results,
                    }
                },
            )

            return Status(
                status_value="ERROR",
                message="Errors occurred during job execution:\n" + "\n".join(results),
            )

        return Status(status_value="OK", message="All jobs completed successfully.")

    def _run_job(self, job: JobDefinition) -> Status:
        """Executes a single job and logs its execution.

        Args:
            job: The job definition to execute.

        Returns:
            The result status of the executed job.
        """
        self.logger.info(
            "Starting job",
            extra={
                "attributes": {
                    "operation": "MULTITHREAD_EXECUTOR",
                    "job_name": job.name,
                    "status": "STARTED",
                    "args": job.args,
                }
            },
        )
        return job.job(**job.args)
