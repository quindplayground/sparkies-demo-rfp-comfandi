"""Variables resource module for configuration management with Dynaconf."""

from functools import reduce
from pathlib import Path
from typing import MutableMapping, Literal

from dynaconf import Dynaconf, Validator

from template_project.libs.resources.vars.zip_handler import get_working_path
from template_project.libs.utils import get_package_resource_path


class _VarsStore:
    """Internal configuration store that manages multiple Dynaconf instances identified by a unique ID."""

    _store: MutableMapping[int, Dynaconf] = {}
    _allowed_formats: list[str] = ["*.toml", "*.yaml", "*.yml", "*.json", "*.ini"]

    @staticmethod
    def _get_base_path(root: str, config_path: str | None) -> Path:
        """Build and validate the base path for configuration files.

        Args:
            root: The root directory.
            config_path: Optional subdirectory path for configurations.

        Returns:
            The validated base path.

        Raises:
            ValueError: If the path doesn't exist or is not a directory.
        """
        root = get_working_path(root)
        base_path = Path(root) / Path(config_path) if config_path else Path(root)

        if not base_path.exists():
            raise ValueError(f"The path '{base_path}' does not exist.")
        if not base_path.is_dir():
            raise ValueError(f"The path '{base_path}' must be a directory.")

        return base_path

    @classmethod
    def _get_conf_paths(cls, base_path: Path) -> list[str]:
        """Recursively retrieve configuration file paths with allowed extensions.

        Args:
            base_path: The base directory to search.

        Returns:
            A list of configuration file paths.

        Raises:
            FileNotFoundError: If no configuration files are found.
        """
        conf_files = set()

        for ext in cls._allowed_formats:
            conf_files.update(base_path.rglob(ext))

        conf_files = [str(file) for file in conf_files]

        if not conf_files:
            raise FileNotFoundError(
                "No configuration files found for the specified configuration."
            )

        return conf_files

    @classmethod
    def _get_conf_instance(
        cls,
        root: str,
        env: str,
        config_paths: str | list[str] | None,
        validators: list[Validator] | None = None,
    ) -> Dynaconf:
        """Create a Dynaconf instance using the provided configuration paths.

        Args:
            root: The root directory for configuration.
            env: The environment name to load.
            config_paths: Specific configuration subpaths or files.
            validators: Configuration validators (optional).

        Returns:
            A configured Dynaconf instance.

        Raises:
            RuntimeError: If configuration setup fails.
        """
        if isinstance(config_paths, str):
            config_paths = [config_paths]
        base_paths = (
            [cls._get_base_path(root, path) for path in config_paths]
            if config_paths
            else [Path(root)]
        )
        conf_paths = reduce(
            lambda x, y: list(set(x) | set(y)),
            [cls._get_conf_paths(base_path) for base_path in base_paths],
        )

        dynaconf_args = {
            "environments": True,
            "env": env,
            "settings_files": conf_paths,
            "merge_enabled": True,
        }

        if validators:
            dynaconf_args["validators"] = validators

        try:
            return Dynaconf(**dynaconf_args)
        except Exception as e:
            raise RuntimeError(f"Error setting up configuration: {e}")

    @classmethod
    def add(
        cls,
        vars_resource_id: int,
        root: str,
        env: str,
        config_paths: str | list[str] | None = None,
        validators: list[Validator] | None = None,
    ):
        """Add a Dynaconf configuration instance to the store.

        Args:
            vars_resource_id: Unique identifier for the configuration.
            root: Root directory for configuration files.
            env: Environment to load.
            config_paths: Specific configuration paths (optional).
            validators: Validators to apply to the configuration (optional).
        """
        conf = cls._get_conf_instance(root, env, config_paths, validators)
        cls._store[vars_resource_id] = conf

    @classmethod
    def get(cls, vars_resource_id: int) -> Dynaconf:
        """Retrieve the Dynaconf instance for the given ID.

        Args:
            vars_resource_id: The unique ID associated with the configuration.

        Returns:
            The corresponding configuration instance.

        Raises:
            RuntimeError: If configuration is not found.
        """
        conf = cls._store.get(vars_resource_id)
        if conf is None:
            raise RuntimeError("Configuration not found.")
        return conf

    @classmethod
    def pop(cls, vars_resource_id: int):
        """Remove and return the configuration associated with the given ID.

        Args:
            vars_resource_id: The ID of the configuration to remove.

        Returns:
            The removed configuration instance.

        Raises:
            RuntimeError: If configuration is not found.
        """
        try:
            return cls._store.pop(vars_resource_id)
        except KeyError:
            raise RuntimeError("Configuration not found.")


class VarsResource:
    """Wrapper around _VarsStore that provides instance-based access to configuration."""

    store = _VarsStore

    def __init__(
        self,
        root: str,
        env: str,
        config_paths: str | None | list[str] = None,
        validators: list[Validator] | None = None,
    ):
        """Initialize a VarsResource with its associated configuration.

        Args:
            root: Root directory of configuration files.
            env: The environment name to load.
            config_paths: Paths to specific configuration files or directories (optional).
            validators: Validators to apply to the configuration (optional).
        """
        self.store.add(id(self), root, env, config_paths, validators)

    @property
    def vars(self) -> Dynaconf:
        """Return the configuration instance associated with this VarsResource.

        Returns:
            The configuration instance.
        """
        return self.store.get(id(self))


def get_vars_resource(
    env: Literal["dev", "test", "prod"],
    config_paths: str | list[str],
    validators: list[Validator] | None = None,
) -> VarsResource:
    """Factory function to create a VarsResource instance.

    Args:
        env: Environment name (e.g. 'dev', 'prod').
        config_paths: Path or list of paths to configuration files.
        validators: Validators to apply to the configuration (optional).

    Returns:
        Configured VarsResource instance.

    Raises:
        ModuleNotFoundError: If template_project package is not found.
    """
    try:
        root = get_package_resource_path("template_project")
    except Exception:
        raise ModuleNotFoundError("template_project package not found")

    return VarsResource(root, env, config_paths, validators)
