import os
import sys
import logging
from pathlib import Path
from typing import Optional
from logger_config import setup_logger
from rollback import RollbackManager

script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def setup_reference_md(file_path: str, old_project_dir_name: str,
                      new_project_dir_name: str, old_package_name: str,
                      new_package_name: str, old_test_dir_name: str,
                      new_test_dir_name: str, dry_run: bool = False,
                      logger: Optional[logging.Logger] = None,
                      rollback_manager: Optional[RollbackManager] = None) -> bool:
    """Updates REFERENCE.md with new project names.

    Args:
        file_path: Path to REFERENCE.md file.
        old_project_dir_name: Old project directory name.
        new_project_dir_name: New project directory name.
        old_package_name: Old package name.
        new_package_name: New package name.
        old_test_dir_name: Old test directory name.
        new_test_dir_name: New test directory name.
        dry_run: If True, only shows what would be done.
        logger: Logger instance. If None, creates a new logger.
        rollback_manager: Rollback manager to track changes.

    Returns:
        True if successful, False otherwise.
    """
    log = logger or setup_logger("setup_reference", dry_run=dry_run)

    if not os.path.exists(file_path):
        log.warning(f"REFERENCE.md not found at {file_path}")
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = content = f.read()

        if dry_run:
            log.debug(f"Would update REFERENCE.md: {file_path}")
            return True

        replacements = [
            (f"pip install -e {old_project_dir_name}",
             f"pip install -e {new_project_dir_name}"),
            (f"import {old_package_name}", f"import {new_package_name}"),
            (f"from {old_package_name}", f"from {new_package_name}"),
            (f"{old_project_dir_name}/", f"{new_project_dir_name}/"),
            (f"├── {old_package_name}/", f"├── {new_package_name}/"),
            (f"├── {old_test_dir_name}/", f"├── {new_test_dir_name}/"),
            (f"- **`{old_test_dir_name}/`**", f"- **`{new_test_dir_name}/`**"),
            (f"`{old_package_name}.", f"`{new_package_name}."),
            (f"**Nombre:** `{old_package_name}.", f"**Nombre:** `{new_package_name}."),
            (f"- Código: `{old_package_name}/", f"- Código: `{new_package_name}/"),
        ]

        updated = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                log.info(f"  ✓ Replaced: {old[:50]}...")
                updated = True

        if updated:
            if rollback_manager:
                rollback_manager.add_file_edit(file_path, original_content)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            log.info(f"✓ Updated REFERENCE.md: {file_path}")
        else:
            log.info(f"  No changes needed in REFERENCE.md")

        return True
    except Exception as e:
        log.error(f"Error updating REFERENCE.md {file_path}: {e}")
        return False
