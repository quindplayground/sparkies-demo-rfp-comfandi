import os
import shutil
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rollback import RollbackManager


logger = logging.getLogger(__name__)


def replace_in_file(file_path: str, old_str: str, new_str: str, dry_run: bool = False,
                   logger_instance: Optional[logging.Logger] = None,
                   rollback_manager: Optional['RollbackManager'] = None) -> None:
    """Replaces text in a file.

    Args:
        file_path: Path to the file.
        old_str: Text to replace.
        new_str: Replacement text.
        dry_run: If True, only shows what would be done.
        logger_instance: Logger instance. If None, uses module logger.
        rollback_manager: Rollback manager to track changes.
    """
    log = logger_instance or logger

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_str in content:
            if dry_run:
                log.debug(f"Would replace '{old_str}' with '{new_str}' in {file_path}")
            else:
                if rollback_manager:
                    rollback_manager.add_file_edit(file_path, content)
                new_content = content.replace(old_str, new_str)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                log.info(f"Updated {file_path}")
    except UnicodeDecodeError:
        log.warning(f"Skipping binary file: {file_path}")
    except Exception as e:
        log.error(f"Error processing {file_path}: {e}")


def rename_directory(old_path: str, new_path: str, dry_run: bool = False,
                    logger_instance: Optional[logging.Logger] = None,
                    rollback_manager: Optional['RollbackManager'] = None) -> None:
    """Renames a directory.

    Args:
        old_path: Old directory path.
        new_path: New directory path.
        dry_run: If True, only shows what would be done.
        logger_instance: Logger instance. If None, uses module logger.
        rollback_manager: Rollback manager to track changes.
    """
    log = logger_instance or logger

    if dry_run:
        log.debug(f"Would rename directory {old_path} to {new_path}")
    else:
        if os.path.exists(old_path):
            if rollback_manager:
                rollback_manager.add_rename(old_path, new_path)
            shutil.move(old_path, new_path)
            log.info(f"Renamed directory {old_path} to {new_path}")
        else:
            log.warning(f"Directory {old_path} not found, skipping rename.")
