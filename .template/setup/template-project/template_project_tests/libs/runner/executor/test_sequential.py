from unittest.mock import Mock, patch

from template_project.libs.runner.executors.sequential import SequentialExecutor
from template_project.libs.runner.types import JobDefinition, Status


def test_sequential_executor_success(spark):
    """Test para verificar la ejecución secuencial exitosa de jobs"""

    def job1(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job1 completed with result: {x + 1}")

    def job2(y: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job2 completed with result: {y * 2}")

    jobs = [
        JobDefinition(name="job1", job=job1, args={"x": 1, "spark_session": spark}),
        JobDefinition(name="job2", job=job2, args={"y": 2, "spark_session": spark}),
    ]

    executor = SequentialExecutor()
    result = executor.execute(jobs)

    assert result.status_value == "OK"
    assert result.message == "All jobs completed successfully."
    assert result.code == 200  # skipcq: PYL-W0143


def test_sequential_executor_with_error(spark):
    """Test para verificar el manejo de errores en la ejecución secuencial"""

    def failing_job(spark_session=None, **kwargs):
        assert spark_session is not None
        raise ValueError("Job failed")

    def success_job(spark_session=None, **kwargs):
        assert spark_session is not None
        return Status(status_value="OK", message="Success")

    jobs = [
        JobDefinition(name="success", job=success_job, args={"spark_session": spark}),
        JobDefinition(name="fail", job=failing_job, args={"spark_session": spark}),
    ]

    executor = SequentialExecutor()
    result = executor.execute(jobs)

    assert result.status_value == "ERROR"
    assert "Job failed" in result.message
    assert result.code == 500  # skipcq: PYL-W0143


@patch("template_project.libs.runner.executors.sequential.get_logger")
def test_sequential_executor_logging(mock_get_logger, spark):
    """Test para verificar el logging en la ejecución secuencial"""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    def simple_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x}")

    jobs = [
        JobDefinition(
            name="test_job", job=simple_job, args={"x": 1, "spark_session": spark}
        )
    ]

    executor = SequentialExecutor()
    executor.execute(jobs)

    assert mock_logger.info.call_count >= 1
    assert mock_logger.error.call_count == 0
