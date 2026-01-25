from typing import Generic
import traceback

from demo_comfandi_project.libs.runner.executors.base import IExecutor
from demo_comfandi_project.libs.runner.types import P, JobDefinition, Status, JobResult
from demo_comfandi_project.libs.logging import get_logger


class SequentialExecutor(Generic[P], IExecutor):
    """Executes jobs sequentially in the order they are provided.

    Respects job dependencies and skips jobs if their dependencies failed.
    """

    def __init__(self):
        """Initializes the sequential executor."""
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)

    def execute(self, jobs: list[JobDefinition]) -> Status:
        """Executes a list of jobs one after another in sequence.

        Args:
            jobs: List of job definitions to execute.

        Returns:
            Aggregated execution status. Returns 'ERROR' if any job fails.
        """
        exceptions: list[JobResult] = []
        completed_jobs: set[str] = set()

        self.logger.info(
            "Starting sequential executor with jobs",
            extra={
                "attributes": {
                    "operation": "SEQUENTIAL_EXECUTOR",
                    "executor": "sequential",
                    "status": "IN_PROGRESS",
                    "job_names": [job.name for job in jobs],
                }
            },
        )

        for job in jobs:
            if not self._are_dependencies_successful(job, completed_jobs):
                error_message = (
                    f"Job '{job.name}' cannot execute because some dependencies failed"
                )
                job_result = JobResult(
                    job_name=job.name,
                    status=Status(status_value="ERROR", message=error_message),
                )
                self.logger.error(
                    "Skipping job due to failed dependencies",
                    extra={
                        "attributes": {
                            "operation": "SEQUENTIAL_EXECUTOR",
                            "job_name": job.name,
                            "status": "ERROR",
                            "result": job_result.model_dump_json(),
                        }
                    },
                )
                exceptions.append(job_result)
                continue

            try:
                self.logger.info(
                    "Starting job",
                    extra={
                        "attributes": {
                            "operation": "SEQUENTIAL_EXECUTOR",
                            "job_name": job.name,
                            "status": "STARTED",
                            "args": job.args,
                        }
                    },
                )
                result = job.job(**job.args)
                job_result = JobResult(job_name=job.name, status=result)

                self.logger.info(
                    "Job completed successfully",
                    extra={
                        "attributes": {
                            "operation": "SEQUENTIAL_EXECUTOR",
                            "job_name": job.name,
                            "status": "DONE",
                            "result": job_result.model_dump_json(),
                        }
                    },
                )

                completed_jobs.add(job.name)
            except Exception as e:
                error_message = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                job_result = JobResult(
                    job_name=job.name,
                    status=Status(status_value="ERROR", message=error_message),
                )

                self.logger.error(
                    "Error in job",
                    extra={
                        "attributes": {
                            "operation": "SEQUENTIAL_EXECUTOR",
                            "job_name": job.name,
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
                        "operation": "SEQUENTIAL_EXECUTOR",
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

        self.logger.info(
            "All jobs completed successfully",
            extra={
                "attributes": {
                    "operation": "SEQUENTIAL_EXECUTOR",
                    "executor": "sequential",
                    "status": "DONE",
                    "job_names": [job.name for job in jobs],
                }
            },
        )

        return Status(status_value="OK", message="All jobs completed successfully.")

    @staticmethod
    def _are_dependencies_successful(
        job: JobDefinition, completed_jobs: set[str]
    ) -> bool:
        """Checks if all dependencies of a job have been successful.

        Args:
            job: The job definition to check.
            completed_jobs: Set of completed jobs.

        Returns:
            True if all dependencies have been successful, False otherwise.
        """
        return all(dep in completed_jobs for dep in job.depends_on)
