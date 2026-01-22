import os
import sys
import logging
import shutil
from pathlib import Path
from typing import Optional
from common import replace_in_file
from logger_config import setup_logger
from rollback import RollbackManager

script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def setup_all_files(new_project_path: str, root_dir: str, old_package_name: str,
                    new_package_name: str, old_project_dir_name: str,
                    new_project_dir_name: str, old_test_dir_name: str,
                    new_test_dir_name: str, dry_run: bool = False,
                    logger: Optional[logging.Logger] = None,
                    rollback_manager: Optional[RollbackManager] = None) -> bool:
    """Updates all project files with new names.

    Args:
        new_project_path: Path to renamed project directory.
        root_dir: Root directory.
        old_package_name: Old package name.
        new_package_name: New package name.
        old_project_dir_name: Old project directory name.
        new_project_dir_name: New project directory name.
        old_test_dir_name: Old test directory name.
        new_test_dir_name: New test directory name.
        dry_run: If True, only shows what would be done.
        logger: Logger instance. If None, creates a new logger.
        rollback_manager: Rollback manager to track changes.

    Returns:
        True if successful.
    """
    log = logger or setup_logger("setup_files", dry_run=dry_run)

    log.info(f"\n{'='*60}")
    log.info("STEP 3: Updating all files with new names")
    log.info(f"{'='*60}")

    files_updated = 0
    for dirpath, dirnames, filenames in os.walk(new_project_path):
        if ".git" in dirpath or any(d.startswith(".") for d in dirpath.split(os.sep)):
            continue

        for filename in filenames:
            if filename in ["pyproject.toml", "REFERENCE.md", "LICENSE", "setup_project.py"]:
                continue

            file_path = os.path.join(dirpath, filename)

            replace_in_file(file_path, old_package_name, new_package_name, dry_run,
                          logger_instance=log, rollback_manager=rollback_manager)
            replace_in_file(file_path, old_project_dir_name, new_project_dir_name, dry_run,
                          logger_instance=log, rollback_manager=rollback_manager)
            replace_in_file(file_path, old_test_dir_name, new_test_dir_name, dry_run,
                          logger_instance=log, rollback_manager=rollback_manager)
            files_updated += 1

    log.info(f"  Processed {files_updated} files in project directory")

    # Determine template source: if in cloned repo, use repo template; otherwise use local
    is_cloned_repo = (
        os.path.exists(os.path.join(root_dir, ".git"))
        or os.path.exists(os.path.join(os.path.dirname(root_dir), ".git"))
    )
    template_base = (
        os.path.join(root_dir, ".template", "setup")
        if is_cloned_repo and os.path.exists(os.path.join(root_dir, ".template", "setup"))
        else os.path.join(root_dir, ".template", "setup")
    )

    # Copy spark_script.py to root
    template_spark_script = os.path.join(template_base, "spark_script.py")
    root_spark_script = os.path.join(root_dir, "spark_script.py")
    if os.path.exists(template_spark_script):
        if dry_run:
            log.info(f"[DRY RUN] Would copy '{template_spark_script}' -> '{root_spark_script}'")
        else:
            if rollback_manager:
                if os.path.exists(root_spark_script):
                    with open(root_spark_script, 'r', encoding='utf-8') as f:
                        rollback_manager.add_file_edit(root_spark_script, f.read())
            shutil.copy2(template_spark_script, root_spark_script)
            log.info(f"Copied spark_script template from {template_spark_script} to {root_spark_script}")

    # Copy docs/ directory to workspace root (from .template/setup/docs)
    # IMPORTANT: Copy to root_dir/docs/ (workspace root), NOT inside {project-name}-project/
    template_docs = os.path.join(template_base, "docs")
    new_docs = os.path.join(root_dir, "docs")
    if os.path.exists(template_docs):
        if dry_run:
            log.info(f"[DRY RUN] Would copy '{template_docs}' -> '{new_docs}'")
        else:
            if os.path.exists(new_docs):
                log.warning(f"Target docs directory {new_docs} already exists, skipping copy.")
            else:
                shutil.copytree(template_docs, new_docs)
                log.info(f"Copied docs from {template_docs} to {new_docs}")
    else:
        log.warning(f"Template docs directory not found at {template_docs}")

    # Copy iac-refs/ directory to workspace root (from .template/setup/iac-refs)
    # IMPORTANT: Copy to root_dir/iac-refs/ (workspace root), NOT inside {project-name}-project/
    template_iac = os.path.join(template_base, "iac-refs")
    new_iac = os.path.join(root_dir, "iac-refs")
    if os.path.exists(template_iac):
        if dry_run:
            log.info(f"[DRY RUN] Would copy '{template_iac}' -> '{new_iac}'")
        else:
            if os.path.exists(new_iac):
                log.warning(f"Target iac-refs directory {new_iac} already exists, skipping copy.")
            else:
                shutil.copytree(template_iac, new_iac)
                log.info(f"Copied iac-refs from {template_iac} to {new_iac}")
    else:
        log.warning(f"Template iac-refs directory not found at {template_iac}")

    # Copy README.md.template to workspace root (from .template/setup/README.md.template)
    # IMPORTANT: Copy to root_dir/README.md.template (workspace root), NOT inside {project-name}-project/
    template_readme = os.path.join(template_base, "README.md.template")
    new_readme_template = os.path.join(root_dir, "README.md.template")
    if os.path.exists(template_readme):
        if dry_run:
            log.info(f"[DRY RUN] Would copy '{template_readme}' -> '{new_readme_template}'")
        else:
            shutil.copy2(template_readme, new_readme_template)
            log.info(f"Copied README.md.template from {template_readme} to {new_readme_template}")
    else:
        log.warning(f"Template README.md.template not found at {template_readme}")
    
    template_gitignore = os.path.join(template_base, ".gitignore")
    new_gitignore = os.path.join(root_dir, ".gitignore")
    if os.path.exists(template_gitignore):
        if dry_run:
            log.info(f"[DRY RUN] Would copy '{template_gitignore}' -> '{new_gitignore}'")
        else:
            shutil.copy2(template_gitignore, new_gitignore)
            log.info(f"Copied .gitignore from {template_gitignore} to {new_gitignore}")
    else:
        log.warning(f"Template .gitignore not found at {template_gitignore}")

    root_files_to_update = ["spark_script.py", "README.md"]
    for filename in root_files_to_update:
        file_path = os.path.join(root_dir, filename)
        if os.path.exists(file_path):
            log.info(f"  Updating {filename}...")
            replace_in_file(file_path, old_package_name, new_package_name, dry_run,
                          logger_instance=log, rollback_manager=rollback_manager)
            replace_in_file(file_path, old_project_dir_name, new_project_dir_name, dry_run,
                          logger_instance=log, rollback_manager=rollback_manager)
            replace_in_file(file_path, old_test_dir_name, new_test_dir_name, dry_run,
                          logger_instance=log, rollback_manager=rollback_manager)

    return True
