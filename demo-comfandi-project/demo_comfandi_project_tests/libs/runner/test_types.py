import pytest
from pydantic import ValidationError

from demo_comfandi_project.libs.runner.types import JobDefinition, Status, JobResult


def test_job_simple():
    """Test para una definición de job simple"""

    def dummy_job(x: int) -> str:
        return str(x)

    job_def = JobDefinition(name="test_job", job=dummy_job, args={"x": 1})
    assert job_def.name == "test_job"
    assert job_def.job is dummy_job
    assert job_def.args == {"x": 1}
    assert job_def.depends_on == []


def test_job_with_dependencies():
    """Test para una definición de job con dependencias"""

    def dummy_job(x: int) -> str:
        return str(x)

    job_def = JobDefinition(
        name="test_job", job=dummy_job, args={"x": 1}, depends_on=["job1", "job2"]
    )
    assert job_def.name == "test_job"
    assert job_def.job is dummy_job
    assert job_def.args == {"x": 1}
    assert job_def.depends_on == ["job1", "job2"]


def test_status_code_mapping():
    """Test para verificar el mapeo correcto de códigos de estado"""
    status = Status(status_value="OK", message="Success")
    assert status.code == 200  # skipcq: PYL-W0143
    assert status.status_value == "OK"
    assert status.message == "Success"

    error_status = Status(status_value="ERROR", message="Internal error")
    assert error_status.code == 500  # skipcq: PYL-W0143
    assert error_status.status_value == "ERROR"
    assert error_status.message == "Internal error"


def test_invalid_status():
    """Test para verificar que estados inválidos son rechazados"""
    with pytest.raises(ValidationError):
        Status(status_value="INVALID_STATUS", message="This should fail")


def test_job_result_default_values():
    """Test para verificar valores por defecto en JobResult"""
    result = JobResult(
        job_name="test", status=Status(status_value="OK", message="Success")
    )
    assert result.job_name == "test"
    assert result.status.status_value == "OK"
    assert result.status.message == "Success"


def test_job_result_with_data():
    """Test para verificar JobResult con datos"""
    result = JobResult(
        job_name="test", status=Status(status_value="ERROR", message="test_error")
    )
    assert result.job_name == "test"
    assert result.status.status_value == "ERROR"
    assert result.status.message == "test_error"
