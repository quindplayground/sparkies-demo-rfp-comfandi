import os
import tempfile
import zipfile
import pytest
from unittest.mock import Mock, patch, create_autospec
from pathlib import Path

from pyspark.sql import SparkSession
from demo_comfandi_project.libs.resources.vars.zip_handler import ZipHandler


@pytest.fixture
def mock_spark():
    """Create a mock SparkSession."""
    return create_autospec(SparkSession, instance=True)


@pytest.fixture
def zip_handler(mock_spark):
    """Create a ZipHandler instance."""
    return ZipHandler(mock_spark)


@pytest.fixture
def temp_zip_file():
    """Create a temporary zip file with test content."""
    with tempfile.NamedTemporaryFile(
        suffix=".zip", delete=False
    ) as tmp_zip, zipfile.ZipFile(tmp_zip.name, "w") as zf:
        zf.writestr("test.txt", "test content")
        zf.writestr("subdir/test2.txt", "test content 2")
    yield tmp_zip.name
    os.unlink(tmp_zip.name)


def test_extract_zip_success(zip_handler, temp_zip_file):
    """Test successful zip extraction."""
    extracted_path = zip_handler._extract_zip(temp_zip_file)
    assert os.path.exists(extracted_path)
    assert os.path.exists(os.path.join(extracted_path, "test.txt"))
    assert os.path.exists(os.path.join(extracted_path, "subdir", "test2.txt"))


def test_extract_zip_file_not_found(zip_handler):
    """Test extracting non-existent zip file."""
    with pytest.raises(FileNotFoundError):
        zip_handler._extract_zip("nonexistent.zip")


def test_extract_zip_cache(zip_handler, temp_zip_file):
    """Test zip extraction caching."""
    path1 = zip_handler._extract_zip(temp_zip_file)
    path2 = zip_handler._extract_zip(temp_zip_file)
    assert path1 == path2


def test_extract_zip_with_existing_files(zip_handler, temp_zip_file):
    """Test extracting zip when files already exist."""
    extracted_path = zip_handler._extract_zip(temp_zip_file)
    path2 = zip_handler._extract_zip(temp_zip_file)
    assert extracted_path == path2


def test_locate_file_in_spark_success(zip_handler):
    """Test locating file in Spark context."""
    with patch(
        "demo_comfandi_project.libs.resources.vars.zip_handler.SparkFiles.get"
    ) as mock_get:
        mock_get.return_value = "/spark/path/file.txt"
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            path = zip_handler._locate_file_in_spark("file.txt")
            assert path == "/spark/path/file.txt"


def test_locate_file_in_spark_fallback_to_cwd(zip_handler):
    """Test fallback to current working directory."""
    with patch(
        "demo_comfandi_project.libs.resources.vars.zip_handler.SparkFiles.get"
    ) as mock_get:
        mock_get.return_value = "/spark/path/file.txt"
        with patch("os.path.exists") as mock_exists:

            def exists_side_effect(path):
                return path == os.path.join(os.getcwd(), "file.txt")

            mock_exists.side_effect = exists_side_effect
            path = zip_handler._locate_file_in_spark("file.txt")
            assert path == os.path.join(os.getcwd(), "file.txt")


def test_locate_file_in_spark_not_found(zip_handler):
    """Test file not found in any location."""
    with patch(
        "demo_comfandi_project.libs.resources.vars.zip_handler.SparkFiles.get"
    ) as mock_get:
        mock_get.return_value = "/spark/path/file.txt"
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            with pytest.raises(FileNotFoundError):
                zip_handler._locate_file_in_spark("file.txt")


def test_get_working_path_module(zip_handler):
    """Test getting working path from module."""
    mock_module = Mock()
    path = "/path/to/module"
    mock_module.__path__ = [path]

    with patch("os.path.exists") as mock_exists, patch(
        "zipfile.is_zipfile"
    ) as mock_is_zipfile, patch("inspect.ismodule") as mock_ismodule:
        mock_exists.return_value = True
        mock_is_zipfile.return_value = False
        mock_ismodule.return_value = True
        result = zip_handler.get_working_path(mock_module, False)
        assert result == path


def test_get_working_path_partial_zip_path(zip_handler, temp_zip_file):
    """Test getting working path from zip with remaining path."""
    test_path = f"{temp_zip_file}/subdir/test2.txt"
    with patch("zipfile.is_zipfile") as mock_is_zipfile:

        def is_zipfile_side_effect(path):
            return path == temp_zip_file

        mock_is_zipfile.side_effect = is_zipfile_side_effect
        extracted_path = zip_handler.get_working_path(test_path, False)
        assert extracted_path.endswith("subdir/test2.txt")


def test_get_working_path_zip_not_found(zip_handler):
    """Test getting working path from non-existent zip."""
    with patch("zipfile.is_zipfile") as mock_is_zipfile:
        mock_is_zipfile.return_value = True
        with pytest.raises(FileNotFoundError):
            zip_handler.get_working_path("/nonexistent/path.zip/file.txt", False)


def test_get_working_path_zip_file(zip_handler, temp_zip_file):
    """Test getting working path from zip file."""
    test_path = f"{temp_zip_file}/subdir/test2.txt"
    extracted_path = zip_handler.get_working_path(test_path, False)
    assert os.path.exists(os.path.dirname(extracted_path))


def test_get_working_path_normal_path(zip_handler):
    """Test getting working path from normal path."""
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = zip_handler.get_working_path(temp_dir, False)
            assert path == temp_dir


def test_get_working_path_spark_cluster(zip_handler):
    """Test getting working path in Spark cluster."""
    with patch.object(zip_handler, "_locate_file_in_spark") as mock_locate:
        mock_locate.return_value = "/spark/path/file.txt"
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            path = zip_handler.get_working_path("file.txt", True)
            assert path == "/spark/path/file.txt"


def test_get_working_path_path_object(zip_handler):
    """Test getting working path from Path object."""
    path_obj = Path("/test/path")
    with patch("os.path.exists") as mock_exists, patch(
        "zipfile.is_zipfile"
    ) as mock_is_zipfile:
        mock_exists.return_value = True
        mock_is_zipfile.return_value = False
        result = zip_handler.get_working_path(path_obj, False)
        assert result == str(path_obj)


def test_get_working_path_helper():
    """Test the get_working_path helper function."""
    mock_spark = create_autospec(SparkSession, instance=True)

    with patch(
        "demo_comfandi_project.libs.resources.vars.zip_handler.SparkResource"
    ) as mock_spark_resource:
        mock_spark_resource.return_value = mock_spark
        with patch.object(ZipHandler, "get_working_path") as mock_get_working_path:
            mock_get_working_path.return_value = "/test/path"
            from demo_comfandi_project.libs.resources.vars.zip_handler import (
                get_working_path,
            )

            result = get_working_path("test_path", False)

            assert result == "/test/path"
            mock_spark_resource.assert_called_once_with(new_session=True)
            mock_get_working_path.assert_called_once_with("test_path", False)
