import time
from unittest.mock import Mock, patch

from demo_comfandi_project.libs.runner.executors.multithread import MultithreadExecutor
from demo_comfandi_project.libs.runner.types import JobDefinition, Status


def test_multithread_executor_success(spark):
    """Test para verificar la ejecución paralela exitosa de jobs"""

    def slow_job(x: int, spark_session=None) -> Status:
        time.sleep(0.1)
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x + 1}")

    jobs = [
        JobDefinition(
            name=f"job_{i}", job=slow_job, args={"x": i, "spark_session": spark}
        )
        for i in range(3)
    ]

    executor = MultithreadExecutor(max_workers=2)
    start_time = time.time()
    result = executor.execute(jobs)
    end_time = time.time()

    assert 0.2 <= end_time - start_time <= 0.4
    assert result.status_value == "OK"
    assert result.message == "All jobs completed successfully."
    assert result.code == 200  # skipcq: PYL-W0143


def test_multithread_executor_with_error(spark):
    def failing_job(spark_session=None, **kwargs):
        assert spark_session is not None
        raise ValueError("Job failed")

    def success_job(spark_session=None, **kwargs):
        assert spark_session is not None
        return Status(status_value="OK", message="Success")

    jobs = [
        JobDefinition(name="success1", job=success_job, args={"spark_session": spark}),
        JobDefinition(name="fail", job=failing_job, args={"spark_session": spark}),
        JobDefinition(name="success2", job=success_job, args={"spark_session": spark}),
    ]

    executor = MultithreadExecutor()
    result = executor.execute(jobs)

    assert result.status_value == "ERROR"
    assert "Job failed" in result.message
    assert result.code == 500  # skipcq: PYL-W0143


@patch("demo_comfandi_project.libs.runner.executors.multithread.get_logger")
def test_multithread_executor_logging(mock_get_logger, spark):
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    def simple_job(x: int, spark_session=None) -> Status:
        assert spark_session is not None
        return Status(status_value="OK", message=f"Job completed with result: {x}")

    jobs = [
        JobDefinition(
            name="test_job_1", job=simple_job, args={"x": 1, "spark_session": spark}
        ),
        JobDefinition(
            name="test_job_2", job=simple_job, args={"x": 2, "spark_session": spark}
        ),
    ]

    executor = MultithreadExecutor(max_workers=2)
    executor.execute(jobs)

    assert mock_logger.info.call_count >= 2
    assert mock_logger.error.call_count == 0


def test_multithread_executor_max_workers(spark):
    """Test para verificar la configuración de max_workers"""
    executor = MultithreadExecutor(max_workers=5)
    assert executor.max_workers == 5

    executor_default = MultithreadExecutor()
    assert executor_default.max_workers is None
