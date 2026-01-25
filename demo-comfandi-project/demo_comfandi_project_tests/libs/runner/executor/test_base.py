from typing import List
from abc import ABC

from demo_comfandi_project.libs.runner.executors.base import IExecutor
from demo_comfandi_project.libs.runner.types import JobDefinition, Status


class DummyExecutor(IExecutor):
    """Implementación dummy del ejecutor para testing"""

    @staticmethod
    def execute(_: List[JobDefinition]) -> Status:
        return Status(status_value="OK", message="Dummy execution")


def test_executor_interface():
    """Test para verificar que la interfaz del ejecutor funciona correctamente"""
    executor = DummyExecutor()
    result = executor.execute([])
    assert isinstance(result, Status)
    assert result.status_value == "OK"
    assert result.message == "Dummy execution"
    assert result.code == 200  # skipcq: PYL-W0143


def test_executor_abstract():
    """Test para verificar que la clase base es abstracta"""
    assert issubclass(IExecutor, ABC)
    assert hasattr(IExecutor, "__abstractmethods__")
    assert "execute" in IExecutor.__abstractmethods__
