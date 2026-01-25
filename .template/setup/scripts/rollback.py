import os
import shutil
import logging
from typing import Optional, Any


class RollbackManager:
    """Manages rollback operations for setup scripts."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initializes the rollback manager.

        Args:
            logger: Logger instance. If None, creates a new logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.operations: list[dict[str, Any]] = []

    def add_rename(self, old_path: str, new_path: str) -> None:
        """Adds a directory rename operation to track.

        Args:
            old_path: Original directory path.
            new_path: New directory path.
        """
        self.operations.append({
            'type': 'rename',
            'old_path': old_path,
            'new_path': new_path
        })

    def add_file_edit(self, file_path: str, original_content: str) -> None:
        """Adds a file edit operation to track.

        Args:
            file_path: Path to the edited file.
            original_content: Original file content before editing.
        """
        self.operations.append({
            'type': 'file_edit',
            'file_path': file_path,
            'original_content': original_content
        })

    def rollback(self) -> None:
        """Rolls back all tracked operations in reverse order."""
        self.logger.info("Starting rollback...")
        for op in reversed(self.operations):
            try:
                if op['type'] == 'rename':
                    if os.path.exists(op['new_path']):
                        shutil.move(op['new_path'], op['old_path'])
                        self.logger.info(f"Rolled back rename: {op['new_path']} -> {op['old_path']}")
                elif op['type'] == 'file_edit':
                    if os.path.exists(op['file_path']):
                        with open(op['file_path'], 'w', encoding='utf-8') as f:
                            f.write(op['original_content'])
                        self.logger.info(f"Rolled back file: {op['file_path']}")
            except Exception as e:
                self.logger.error(f"Error rolling back operation: {e}")
        self.operations.clear()
        self.logger.info("Rollback complete")
