import pytest
from unittest.mock import Mock, patch
from pyspark.sql import SparkSession

from template_project.libs.error_handler import handle_errors


def test_handle_errors_success_logs(spark: SparkSession):
    @handle_errors
    def good_fn(x: int) -> int:
        return x + 1

    with patch(
        "template_project.libs.error_handler.decorator.get_logger"
    ) as mock_logger:
        result = good_fn(
            1, error_args={"spark": spark, "error_path": "/tmp", "source": "src"}
        )
        assert result == 2
        # El decorador no llama info en éxito, solo en error
        mock_logger.return_value.info.assert_not_called()


def test_handle_errors_without_error_args_propagates():
    @handle_errors
    def bad_fn():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        bad_fn()


def test_handle_errors_with_error_args_fail_fast_false(spark: SparkSession):
    @handle_errors
    def bad_fn2():
        raise RuntimeError("boom2")

    with patch(
        "template_project.libs.error_handler.decorator.get_error_handler"
    ) as mock_get_handler, patch(
        "template_project.libs.error_handler.decorator.get_logger"
    ) as mock_logger:
        mock_handler = Mock()
        mock_get_handler.return_value = mock_handler
        result = bad_fn2(
            error_args={
                "spark": spark,
                "error_path": "/tmp",
                "source": "src",
                "fail_fast": False,
            }
        )
        assert result is None
        mock_handler.handle_error.assert_called()
        # El decorador no llama error directamente, el handler lo hace
        mock_logger.return_value.error.assert_not_called()


def test_handle_errors_with_error_args_fail_fast_true(spark: SparkSession):
    @handle_errors
    def bad_fn3():
        raise RuntimeError("boom3")

    with patch(
        "template_project.libs.error_handler.decorator.get_error_handler"
    ) as mock_get_handler, patch(
        "template_project.libs.error_handler.decorator.get_logger"
    ) as mock_logger:
        mock_handler = Mock()
        mock_get_handler.return_value = mock_handler
        with pytest.raises(RuntimeError):
            bad_fn3(
                error_args={
                    "spark": spark,
                    "error_path": "/tmp",
                    "source": "src",
                    "fail_fast": True,
                }
            )
        mock_handler.handle_error.assert_called()
        # El decorador no llama error directamente, el handler lo hace
        mock_logger.return_value.error.assert_not_called()
