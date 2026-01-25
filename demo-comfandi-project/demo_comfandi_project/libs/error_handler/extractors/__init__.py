"""Error data extractors."""

from demo_comfandi_project.libs.error_handler.extractors.base import (
    RowDataExtractorInterface,
)
from demo_comfandi_project.libs.error_handler.extractors.changelog import (
    SparkChangelogExtractor,
)
from demo_comfandi_project.libs.error_handler.extractors.full import SparkFullExtractor


MAP_EXTRACTORS = {"changelog": SparkChangelogExtractor, "full": SparkFullExtractor}

__all__ = [
    "RowDataExtractorInterface",
    "SparkChangelogExtractor",
    "SparkFullExtractor",
    "MAP_EXTRACTORS",
]
