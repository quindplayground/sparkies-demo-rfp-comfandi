#!/usr/bin/env python3

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

try:
    from setup_directories import setup_directories
    from setup_pyproject import setup_pyproject_toml
    from setup_reference import setup_reference_md
    from setup_license import setup_license
    from setup_files import setup_all_files
    from logger_config import setup_logger
    from rollback import RollbackManager
except ImportError as e:
    print(f"Error importing setup modules: {e}")
    print(f"Script directory: {script_dir}")
    print(f"Python path: {sys.path[:3]}")
    sys.exit(1)


def get_args() -> argparse.Namespace:
    """Parses command line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Setup a new project from the template.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_project.py --name mi-proyecto --dry-run
  python setup_project.py --name mi-proyecto
  python setup_project.py --name mi-proyecto \\
    --description "Mi proyecto" \\
    --author-name "Juan Pérez" \\
    --author-email "juan@example.com" \\
    --keywords "pyspark,data-processing" \\
    --copyright-holder "Mi Empresa S.A.S." \\
    --year 2025
        """
    )

    parser.add_argument("--name", required=True, help="The name of the new project.")
    parser.add_argument("--description", help="Description of the project for pyproject.toml")
    parser.add_argument("--author-name", help="Author name for pyproject.toml")
    parser.add_argument("--author-email", help="Author email for pyproject.toml")
    parser.add_argument("--keywords", help="Comma-separated list of keywords")
    parser.add_argument("--copyright-holder", help="Copyright holder name for LICENSE")
    parser.add_argument("--year", type=int, help="Copyright year for LICENSE")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes.")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt.")

    return parser.parse_args()


def confirm_changes(logger: logging.Logger) -> bool:
    """Prompts user to confirm changes.

    Args:
        logger: Logger instance.

    Returns:
        True if user confirms, False otherwise.
    """
    logger.info("\n" + "="*60)
    logger.info("Review the changes above.")
    response = input("Do you want to keep these changes? (yes/no): ").strip().lower()
    return response in ['yes', 'y', 'sí', 'si']


def main() -> int:
    """Main entry point for the setup script.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    args = get_args()
    project_name = args.name
    root_dir = os.getcwd()

    logger = setup_logger("setup_project", dry_run=args.dry_run)

    logger.info("="*60)
    logger.info(f"Setting up project: '{project_name}'")
    logger.info("="*60)
    logger.info(f"Root directory: {root_dir}")
    if args.dry_run:
        logger.warning("⚠️  DRY RUN MODE - No changes will be made")
    logger.info("")

    rollback_manager = RollbackManager(logger=logger) if not args.dry_run else None

    try:
        dir_info = setup_directories(project_name, root_dir, args.dry_run,
                                    logger=logger, rollback_manager=rollback_manager)

        if not args.dry_run and not os.path.exists(dir_info["new_project_path"]):
            logger.error("Project directory was not created. Aborting.")
            return 1

        logger.info(f"\n{'='*60}")
        logger.info("STEP 2: Updating specific configuration files")
        logger.info(f"{'='*60}")

        pyproject_path = os.path.join(dir_info["new_project_path"], "pyproject.toml")
        setup_pyproject_toml(
            pyproject_path,
            dir_info["old_project_dir_name"],
            dir_info["new_project_dir_name"],
            dir_info["old_package_name"],
            dir_info["new_package_name"],
            dir_info["old_test_dir_name"],
            dir_info["new_test_dir_name"],
            description=args.description,
            author_name=args.author_name,
            author_email=args.author_email,
            keywords=args.keywords,
            dry_run=args.dry_run,
            logger=logger,
            rollback_manager=rollback_manager
        )

        reference_md_path = os.path.join(dir_info["new_project_path"], "REFERENCE.md")
        setup_reference_md(
            reference_md_path,
            dir_info["old_project_dir_name"],
            dir_info["new_project_dir_name"],
            dir_info["old_package_name"],
            dir_info["new_package_name"],
            dir_info["old_test_dir_name"],
            dir_info["new_test_dir_name"],
            args.dry_run,
            logger=logger,
            rollback_manager=rollback_manager
        )

        license_path = os.path.join(dir_info["new_project_path"], "LICENSE")
        setup_license(
            license_path,
            project_name,
            copyright_holder=args.copyright_holder,
            year=args.year,
            dry_run=args.dry_run,
            logger=logger,
            rollback_manager=rollback_manager
        )

        setup_all_files(
            dir_info["new_project_path"],
            root_dir,
            dir_info["old_package_name"],
            dir_info["new_package_name"],
            dir_info["old_project_dir_name"],
            dir_info["new_project_dir_name"],
            dir_info["old_test_dir_name"],
            dir_info["new_test_dir_name"],
            args.dry_run,
            logger=logger,
            rollback_manager=rollback_manager
        )

        logger.info(f"\n{'='*60}")
        logger.info("✅ Project setup complete!")
        logger.info(f"{'='*60}")
        logger.info(f"\nSummary:")
        logger.info(f"  Project name: {project_name}")
        logger.info(f"  Project directory: {dir_info['new_project_dir_name']}")
        logger.info(f"  Package name: {dir_info['new_package_name']}")
        logger.info(f"  Test directory: {dir_info['new_test_dir_name']}")
        if args.description:
            logger.info(f"  Description: {args.description[:50]}...")
        if args.author_name:
            logger.info(f"  Author: {args.author_name} ({args.author_email or 'N/A'})")
        if args.copyright_holder:
            logger.info(f"  Copyright: {args.copyright_holder} ({args.year or 'current year'})")

        if args.dry_run:
            logger.warning(f"\n⚠️  This was a dry run. Use without --dry-run to apply changes.")
            return 0

        if args.yes or confirm_changes(logger):
            logger.info("\n✓ Changes confirmed.")
            logger.info(f"\nNext steps:")
            logger.info(f"  1. Review the changes in {dir_info['new_project_dir_name']}/")
            logger.info(f"  2. Update any project-specific information if needed")
            logger.info(f"  3. Install the package: cd {dir_info['new_project_dir_name']} && pip install -e .")
            return 0
        else:
            logger.warning("\n⚠️  Changes rejected. Rolling back...")
            if rollback_manager:
                rollback_manager.rollback()
            logger.info("✓ Rollback complete. All changes have been reverted.")
            return 1

    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Setup interrupted by user.")
        if rollback_manager:
            logger.info("Rolling back changes...")
            rollback_manager.rollback()
        return 1
    except Exception as e:
        logger.error(f"\n✗ Error during setup: {e}")
        if rollback_manager:
            logger.info("Rolling back changes...")
            rollback_manager.rollback()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
