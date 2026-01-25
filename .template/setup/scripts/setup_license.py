import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from logger_config import setup_logger
from rollback import RollbackManager

script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def setup_license(file_path: str, project_name: str,
                 copyright_holder: Optional[str] = None,
                 year: Optional[str] = None, dry_run: bool = False,
                 logger: Optional[logging.Logger] = None,
                 rollback_manager: Optional[RollbackManager] = None) -> bool:
    """Updates LICENSE file with new project information.

    Replaces placeholders:
    - {YEAR} -> current year or specified year
    - {COPYRIGHT_HOLDER} -> copyright holder or formatted project name
    - template-project -> project name

    Args:
        file_path: Path to LICENSE file.
        project_name: Project name.
        copyright_holder: Copyright holder name. If None, uses formatted project name.
        year: Copyright year. If None, uses current year.
        dry_run: If True, only shows what would be done.
        logger: Logger instance. If None, creates a new logger.
        rollback_manager: Rollback manager to track changes.

    Returns:
        True if successful, False otherwise.
    """
    log = logger or setup_logger("setup_license", dry_run=dry_run)

    if not os.path.exists(file_path):
        log.warning(f"LICENSE not found at {file_path}")
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = content = f.read()

        if dry_run:
            log.debug(f"Would update LICENSE: {file_path}")
            return True

        if year is None:
            year = str(datetime.now().year)

        if copyright_holder is None:
            copyright_holder = project_name.replace("-", " ").title()

        replacements = [
            ("{YEAR}", year),
            ("{COPYRIGHT_HOLDER}", copyright_holder),
            ("template-project", f"{project_name}-project"),
        ]

        updated = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                log.info(f"  ✓ Replaced: {old} -> {new}")
                updated = True

        if updated:
            if rollback_manager:
                rollback_manager.add_file_edit(file_path, original_content)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            log.info(f"✓ Updated LICENSE: {file_path}")
        else:
            log.info(f"  No changes needed in LICENSE")

        return True
    except Exception as e:
        log.error(f"Error updating LICENSE {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False
