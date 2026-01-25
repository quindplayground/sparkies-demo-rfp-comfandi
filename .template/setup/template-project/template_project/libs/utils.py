"""General utilities module for resource and configuration management."""

import shutil
import tempfile
from importlib.resources import as_file, files
from pathlib import Path

from dynaconf.utils.boxing import DynaBox


def get_package_resource_path(
    package_name: str,
    resource_path: str | None = None,
    string: bool = False,
) -> Path | str:
    """Copies a package resource to a temporary directory and returns its path.

    Args:
        package_name: Name of the package containing the resource.
        resource_path: Path to the resource within the package. If None and the resource is a file, ValueError is raised.
        string: If True, the returned path is converted to string.

    Returns:
        Path to the resource copied in the temporary directory. The type depends on the string parameter.

    Raises:
        ValueError: If resource_path is not provided when copying a file.
    """
    resource = files(package_name)
    if resource_path:
        for segment in resource_path.split("/"):
            resource = resource / segment

    with as_file(resource) as src:
        tmp_root = Path(tempfile.gettempdir()) / package_name
        tmp_root.mkdir(parents=True, exist_ok=True)

        if src.is_dir():
            dest = tmp_root / resource_path if resource_path else tmp_root
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            if not resource_path:
                raise ValueError("resource_path must be provided when copying a file")
            dest = tmp_root / resource_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    if string:
        return str(dest)

    return dest


def get_key_by_value(box: DynaBox, target_value: str) -> str | None:
    """Retrieves the key associated with a given value in a DynaBox.

    Args:
        box: The DynaBox to search in.
        target_value: The value to find in the box.

    Returns:
        The key corresponding to the target value, or None if not found.
    """
    for key, value in box.items():
        if value == target_value:
            return key
    return None
