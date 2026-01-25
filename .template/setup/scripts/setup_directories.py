import os
import sys
import logging
import shutil
from pathlib import Path
from typing import Optional
from common import rename_directory
from logger_config import setup_logger
from rollback import RollbackManager

script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def setup_directories(project_name: str, root_dir: str, dry_run: bool = False,
                     logger: Optional[logging.Logger] = None,
                     rollback_manager: Optional[RollbackManager] = None) -> dict:
    """Renames main project directories.

    Args:
        project_name: Project name (e.g., 'nutresa-compras').
        root_dir: Root directory of the project.
        dry_run: If True, only shows what would be done.
        logger: Logger instance. If None, creates a new logger.
        rollback_manager: Rollback manager to track changes.

    Returns:
        Dictionary with old and new directory names and paths.
    """
    log = logger or setup_logger("setup_directories", dry_run=dry_run)

    old_project_dir_name = "template-project"
    # Project directory should use hyphens (kebab-case) regardless of whether
    # the provided project name contains hyphens or underscores.
    # Example:
    #   project_name = "nutresa-compras"  -> "nutresa-compras-project"
    #   project_name = "quind_project"    -> "quind-project-project"
    project_dir_slug = project_name.replace("_", "-")
    new_project_dir_name = f"{project_dir_slug}-project"

    # Python package and tests keep snake_case (underscores).
    old_package_name = "template_project"
    new_package_name = project_name.replace("-", "_") + "_project"
    old_test_dir_name = "template_project_tests"
    new_test_dir_name = f"{new_package_name}_tests"

    log.info(f"\n{'='*60}")
    log.info("STEP 1: Renaming directories")
    log.info(f"{'='*60}")
    log.info(f"Renaming '{old_project_dir_name}' -> '{new_project_dir_name}'")
    log.info(f"Renaming package '{old_package_name}' -> '{new_package_name}'")
    log.info(f"Renaming test dir '{old_test_dir_name}' -> '{new_test_dir_name}'")

    # Priority order for template source:
    # 1. If we're in a cloned repo (detected by .git in root_dir), use template from repo
    # 2. Use .template/setup/template-project (local template)
    # 3. Use .template/template-project (fallback)
    # 4. Use root template-project (backward compatibility)
    candidate_template_paths = []
    
    # Detect if we're in a cloned repository (check for .git in root_dir or parent)
    is_cloned_repo = (
        os.path.exists(os.path.join(root_dir, ".git"))
        or os.path.exists(os.path.join(os.path.dirname(root_dir), ".git"))
    )
    
    if is_cloned_repo:
        repo_template = os.path.join(root_dir, ".template", "setup", old_project_dir_name)
        if os.path.exists(repo_template):
            candidate_template_paths.append(repo_template)
            log.info(f"Detected cloned repository, using template from: {repo_template}")
    
    candidate_template_paths.extend([
        os.path.join(root_dir, ".template", "setup", old_project_dir_name),
        os.path.join(root_dir, ".template", old_project_dir_name),
    ])

    source_project_path = ""
    use_copy = False
    for candidate in candidate_template_paths:
        if os.path.exists(candidate):
            source_project_path = candidate
            use_copy = True
            break

    if not source_project_path:
        # Backward-compatible behavior: use the project directory at root.
        source_project_path = os.path.join(root_dir, old_project_dir_name)
        use_copy = False

    new_project_path = os.path.join(root_dir, new_project_dir_name)

    if use_copy:
        if dry_run:
            log.info(f"[DRY RUN] Would copy '{source_project_path}' -> '{new_project_path}'")
        else:
            if os.path.exists(new_project_path):
                log.warning(f"Target project directory {new_project_path} already exists, skipping copy.")
            else:
                shutil.copytree(source_project_path, new_project_path)
                log.info(f"Copied template project from {source_project_path} to {new_project_path}")
    else:
        # Fallback: rename/move existing root template-project (original behavior).
        old_project_path = source_project_path
        rename_directory(
            old_project_path,
            new_project_path,
            dry_run,
            logger_instance=log,
            rollback_manager=rollback_manager,
        )

    old_package_path = os.path.join(new_project_path, old_package_name)
    new_package_path = os.path.join(new_project_path, new_package_name)

    rename_directory(old_package_path, new_package_path, dry_run,
                    logger_instance=log, rollback_manager=rollback_manager)

    old_test_path = os.path.join(new_project_path, old_test_dir_name)
    new_test_path = os.path.join(new_project_path, new_test_dir_name)

    rename_directory(old_test_path, new_test_path, dry_run,
                    logger_instance=log, rollback_manager=rollback_manager)

    return {
        "old_project_dir_name": old_project_dir_name,
        "new_project_dir_name": new_project_dir_name,
        "old_package_name": old_package_name,
        "new_package_name": new_package_name,
        "old_test_dir_name": old_test_dir_name,
        "new_test_dir_name": new_test_dir_name,
        "new_project_path": new_project_path,
    }
