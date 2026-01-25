"""Error data extractors."""

from template_project.libs.error_handler.extractors.base import (
    RowDataExtractorInterface,
)
from template_project.libs.error_handler.extractors.changelog import (
    SparkChangelogExtractor,
)
from template_project.libs.error_handler.extractors.full import SparkFullExtractor


MAP_EXTRACTORS = {"changelog": SparkChangelogExtractor, "full": SparkFullExtractor}

__all__ = [
    "RowDataExtractorInterface",
    "SparkChangelogExtractor",
    "SparkFullExtractor",
    "MAP_EXTRACTORS",
]
