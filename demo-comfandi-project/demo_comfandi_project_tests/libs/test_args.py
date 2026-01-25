import pytest
from unittest.mock import patch
from demo_comfandi_project.libs.args import get_args


def test_get_args_success():
    """Test successful parsing of arguments."""
    test_args = ["--env", "dev", "--jobs", "job1,job2,job3"]
    with patch("sys.argv", ["script.py"] + test_args):
        args = get_args()
        assert args.env == "dev"
        assert args.jobs == ["job1", "job2", "job3"]


def test_get_args_missing_required():
    """Test that missing required arguments raise an error."""
    test_cases = [
        ["--env", "dev"],  # missing jobs
        ["--jobs", "job1,job2"],  # missing env
        [],  # missing both
    ]

    for test_args in test_cases:
        with patch("sys.argv", ["script.py"] + test_args), pytest.raises(SystemExit):
            get_args()


def test_get_args_jobs_parsing():
    """Test different job list formats."""
    test_cases = [
        ("job1", ["job1"]),
        ("job1,job2", ["job1", "job2"]),
        ("job1,job2,job3", ["job1", "job2", "job3"]),
        ("", [""]),
    ]

    for jobs_input, expected in test_cases:
        test_args = ["--env", "dev", "--jobs", jobs_input]
        with patch("sys.argv", ["script.py"] + test_args):
            args = get_args()
            assert args.jobs == expected
