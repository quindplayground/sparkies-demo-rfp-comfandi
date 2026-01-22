"""CDC (Change Data Capture) with tagging strategies for Iceberg tables."""

from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.changelog_manager import (
    ChangelogManager,
)
from demo_comfandi_project.libs.iceberg.cdc_with_tagging_strategy.snapshot_manager import (
    SnapshotManager,
)

__all__ = ["ChangelogManager", "SnapshotManager"]
