import os
import re
import logging
import sys
from pathlib import Path
from typing import Optional
from logger_config import setup_logger
from rollback import RollbackManager

script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def setup_pyproject_toml(file_path: str, old_project_dir_name: str,
                         new_project_dir_name: str, old_package_name: str,
                         new_package_name: str, old_test_dir_name: str,
                         new_test_dir_name: str, description: Optional[str] = None,
                         author_name: Optional[str] = None,
                         author_email: Optional[str] = None,
                         keywords: Optional[str] = None, dry_run: bool = False,
                         logger: Optional[logging.Logger] = None,
                         rollback_manager: Optional[RollbackManager] = None) -> bool:
    """Updates pyproject.toml with new project names.

    Automatically updates:
    - Project name
    - Package includes
    - Version attribute
    - Package data
    - Test paths
    - Coverage omit paths
    - Description (if provided)
    - Authors (if provided)
    - Keywords (if provided)

    Args:
        file_path: Path to pyproject.toml file.
        old_project_dir_name: Old project directory name.
        new_project_dir_name: New project directory name.
        old_package_name: Old package name.
        new_package_name: New package name.
        old_test_dir_name: Old test directory name.
        new_test_dir_name: New test directory name.
        description: Project description.
        author_name: Author name.
        author_email: Author email.
        keywords: Comma-separated keywords.
        dry_run: If True, only shows what would be done.
        logger: Logger instance. If None, creates a new logger.
        rollback_manager: Rollback manager to track changes.

    Returns:
        True if successful, False otherwise.
    """
    log = logger or setup_logger("setup_pyproject", dry_run=dry_run)

    if not os.path.exists(file_path):
        log.warning(f"pyproject.toml not found at {file_path}")
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = content = f.read()

        if dry_run:
            log.debug(f"Would update pyproject.toml: {file_path}")
            return True

        replacements = [
            (f'name = "{old_project_dir_name}"',
             f'name = "{new_project_dir_name}"'),
            (f'include = ["{old_package_name}", "{old_package_name}.*"]',
             f'include = ["{new_package_name}", "{new_package_name}.*"]'),
            (f'attr = "{old_package_name}.__version__"',
             f'attr = "{new_package_name}.__version__"'),
            (f'"{old_package_name}" = ["*.toml", "**/*.toml"]',
             f'"{new_package_name}" = ["*.toml", "**/*.toml"]'),
            (f'testpaths = ["{old_test_dir_name}"]',
             f'testpaths = ["{new_test_dir_name}"]'),
            (f'*/{old_test_dir_name}/*',
             f'*/{new_test_dir_name}/*'),
        ]

        updated = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                log.info(f"  ✓ Replaced: {old[:60]}...")
                updated = True

        if description:
            escaped_description = description.replace('"', '\\"')
            desc_pattern = r'description = ["\'].*?["\']'
            if re.search(desc_pattern, content):
                content = re.sub(desc_pattern, f'description = "{escaped_description}"', content)
                log.info(f"  ✓ Updated description")
                updated = True

        if author_name and author_email:
            authors_pattern = r'authors = \[.*?\]'
            new_authors = f'authors = [\n    {{ name = "{author_name}", email = "{author_email}" }},\n]'
            if re.search(authors_pattern, content, re.DOTALL):
                content = re.sub(authors_pattern, new_authors, content, flags=re.DOTALL)
                log.info(f"  ✓ Updated authors: {author_name} <{author_email}>")
                updated = True

        if keywords:
            if isinstance(keywords, str):
                keywords_list = [k.strip() for k in keywords.split(",")]
            else:
                keywords_list = keywords

            keywords_str = ", ".join([f'"{k}"' for k in keywords_list])
            keywords_pattern = r'keywords = \[.*?\]'
            if re.search(keywords_pattern, content, re.DOTALL):
                content = re.sub(keywords_pattern, f'keywords = [{keywords_str}]', content, flags=re.DOTALL)
                log.info(f"  ✓ Updated keywords")
                updated = True

        if updated:
            if rollback_manager:
                rollback_manager.add_file_edit(file_path, original_content)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            log.info(f"✓ Updated pyproject.toml: {file_path}")
            if not (description and author_name and author_email and keywords):
                missing = []
                if not description:
                    missing.append("description")
                if not (author_name and author_email):
                    missing.append("authors")
                if not keywords:
                    missing.append("keywords")
                if missing:
                    log.warning(f"  ⚠️  Remember to update manually: {', '.join(missing)}")
        else:
            log.info(f"  No changes needed in pyproject.toml")

        return True
    except Exception as e:
        log.error(f"Error updating pyproject.toml {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False
