import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from dynaconf import Dynaconf

from template_project.libs.resources.vars.resource import (
    VarsResource,
    _VarsStore,
    get_vars_resource,
)


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory with config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create TOML file
        with open(os.path.join(temp_dir, "config.toml"), "w") as f:
            f.write('[default]\nkey = "value"\n')

        # Create YAML file in subdirectory
        os.makedirs(os.path.join(temp_dir, "subdir"))
        with open(os.path.join(temp_dir, "subdir", "config.yaml"), "w") as f:
            f.write('default:\n  other_key: "other_value"\n')

        yield temp_dir


def test_vars_store_get_base_path(temp_config_dir):
    """Test _VarsStore._get_base_path method."""
    with patch(
        "template_project.libs.resources.vars.resource.get_working_path"
    ) as mock_get_path:
        mock_get_path.return_value = temp_config_dir

        # Test with config_path
        path = _VarsStore._get_base_path(temp_config_dir, "subdir")
        assert path == Path(temp_config_dir) / "subdir"

        # Test without config_path
        path = _VarsStore._get_base_path(temp_config_dir, None)
        assert path == Path(temp_config_dir)


def test_vars_store_get_base_path_errors():
    """Test _VarsStore._get_base_path error cases."""
    with patch(
        "template_project.libs.resources.vars.resource.get_working_path"
    ) as mock_get_path:
        # Test non-existent path
        mock_get_path.return_value = "/nonexistent/path"
        with pytest.raises(ValueError, match="does not exist"):
            _VarsStore._get_base_path("/nonexistent/path", None)

        # Test file instead of directory
        with tempfile.NamedTemporaryFile() as temp_file:
            mock_get_path.return_value = temp_file.name
            with pytest.raises(ValueError, match="must be a directory"):
                _VarsStore._get_base_path(temp_file.name, None)


def test_vars_store_get_conf_paths(temp_config_dir):
    """Test _VarsStore._get_conf_paths method."""
    paths = _VarsStore._get_conf_paths(Path(temp_config_dir))
    assert len(paths) == 2
    assert any("config.toml" in path for path in paths)
    assert any("config.yaml" in path for path in paths)


def test_vars_store_get_conf_paths_no_files():
    """Test _VarsStore._get_conf_paths with no config files."""
    with tempfile.TemporaryDirectory() as temp_dir, pytest.raises(FileNotFoundError):
        _VarsStore._get_conf_paths(Path(temp_dir))


def test_vars_store_get_conf_instance(temp_config_dir):
    """Test _VarsStore._get_conf_instance method."""
    with patch(
        "template_project.libs.resources.vars.resource.get_working_path"
    ) as mock_get_path:
        mock_get_path.return_value = temp_config_dir

        # Test with single config path
        conf = _VarsStore._get_conf_instance(temp_config_dir, "default", "subdir")
        assert isinstance(conf, Dynaconf)

        # Test with multiple config paths
        conf = _VarsStore._get_conf_instance(
            temp_config_dir, "default", ["subdir", "."]
        )
        assert isinstance(conf, Dynaconf)

        # Test with no config paths
        conf = _VarsStore._get_conf_instance(temp_config_dir, "default", None)
        assert isinstance(conf, Dynaconf)


def test_vars_store_get_conf_instance_error():
    """Test _VarsStore._get_conf_instance error case."""
    with patch(
        "template_project.libs.resources.vars.resource.get_working_path"
    ) as mock_get_path, patch(
        "template_project.libs.resources.vars.resource._VarsStore._get_conf_paths"
    ) as mock_get_paths, patch(
        "template_project.libs.resources.vars.resource.Dynaconf", autospec=True
    ) as mock_dynaconf_cls:
        mock_get_path.return_value = "/nonexistent"
        mock_get_paths.return_value = ["/nonexistent/config.toml"]
        mock_dynaconf_cls.side_effect = Exception("Test error")
        with pytest.raises(RuntimeError, match="Error setting up configuration"):
            _VarsStore._get_conf_instance("/nonexistent", "default", None)


def test_vars_store_add(temp_config_dir):
    """Test _VarsStore.add method."""
    with patch(
        "template_project.libs.resources.vars.resource.get_working_path"
    ) as mock_get_path:
        mock_get_path.return_value = temp_config_dir

        vars_id = 12345
        _VarsStore.add(vars_id, temp_config_dir, "default", None)
        assert vars_id in _VarsStore._store
        assert isinstance(_VarsStore._store[vars_id], Dynaconf)


def test_vars_store_get():
    """Test _VarsStore.get method."""
    mock_conf = Mock()
    _VarsStore._store[12345] = mock_conf

    # Test successful get
    conf = _VarsStore.get(12345)
    assert conf == mock_conf

    # Test get with non-existent id
    with pytest.raises(RuntimeError):
        _VarsStore.get(99999)


def test_vars_store_pop():
    """Test _VarsStore.pop method."""
    _VarsStore._store.clear()

    mock_conf = Mock()
    _VarsStore._store[12345] = mock_conf

    conf = _VarsStore.pop(12345)
    assert conf == mock_conf
    assert 12345 not in _VarsStore._store

    with pytest.raises(RuntimeError):
        _VarsStore.pop(99999)


def test_vars_resource_init(temp_config_dir):
    """Test VarsResource initialization."""
    with patch(
        "template_project.libs.resources.vars.resource.get_working_path"
    ) as mock_get_path:
        mock_get_path.return_value = temp_config_dir

        # Test with default parameters
        resource = VarsResource(temp_config_dir, "default")
        assert isinstance(resource.vars, Dynaconf)

        # Test with config_paths
        resource = VarsResource(temp_config_dir, "default", ["subdir"])
        assert isinstance(resource.vars, Dynaconf)

        # Test with string config_path
        resource = VarsResource(temp_config_dir, "default", "subdir")
        assert isinstance(resource.vars, Dynaconf)


def test_get_vars_resource_basic():
    """Test for basic VarsResource creation (unit, not integration)"""
    env = "test"
    config_paths = "flows/stage/maestra_portafolio/config"
    with patch(
        "template_project.libs.resources.vars.resource.get_package_resource_path",
        return_value="/fake/root",
    ), patch(
        "template_project.libs.resources.vars.resource.Path.exists",
        return_value=True,
    ), patch(
        "template_project.libs.resources.vars.resource.Path.glob",
        return_value=["dummy.yaml"],
    ), patch(
        "template_project.libs.resources.vars.resource.VarsResource"
    ) as mock_vars_resource:
        instance = mock_vars_resource.return_value
        result = get_vars_resource(env=env, config_paths=config_paths)
        assert result is instance
        mock_vars_resource.assert_called_once_with(
            "/fake/root", env, config_paths, None
        )


def test_get_vars_resource_with_string_config_path():
    """Test for VarsResource creation with string config path (unit, not integration)"""
    env = "test"
    config_path = "flows/stage/maestra_portafolio/config"
    with patch(
        "template_project.libs.resources.vars.resource.get_package_resource_path",
        return_value="/fake/root",
    ), patch(
        "template_project.libs.resources.vars.resource.Path.exists",
        return_value=True,
    ), patch(
        "template_project.libs.resources.vars.resource.Path.glob",
        return_value=["dummy.yaml"],
    ), patch(
        "template_project.libs.resources.vars.resource.VarsResource"
    ) as mock_vars_resource:
        instance = mock_vars_resource.return_value
        result = get_vars_resource(env=env, config_paths=config_path)
        assert result is instance
        mock_vars_resource.assert_called_once_with("/fake/root", env, config_path, None)


def test_get_vars_resource_package_not_found(monkeypatch):
    """Test for handling package not found error"""

    def mock_get_package_resource_path(*args, **kwargs):
        raise Exception("Package not found")

    monkeypatch.setattr(
        "template_project.libs.resources.vars.resource.get_package_resource_path",
        mock_get_package_resource_path,
    )

    with pytest.raises(ModuleNotFoundError, match="template_project package not found"):
        get_vars_resource(env="test", config_paths="flows/stage/test/config")
