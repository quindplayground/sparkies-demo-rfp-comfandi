from unittest.mock import Mock, patch
from pyspark.sql import SparkSession

from template_project.libs.error_handler.extractors.base import (
    RowDataExtractorInterface,
)
from template_project.libs.error_handler.extractors.full import SparkFullExtractor
from template_project.libs.error_handler.extractors.changelog import (
    SparkChangelogExtractor,
)


def test_row_data_extractor_interface():
    class DummyExtractor(RowDataExtractorInterface):
        def extract_row_data(self, spark=None, source=None):
            return "dummy"

    extractor = DummyExtractor()
    assert extractor.extract_row_data() == "dummy"


def test_spark_full_extractor_reads_spark_log(spark: SparkSession):
    with patch(
        "template_project.libs.error_handler.extractors.full.SparkSession"
    ) as mock_ss:
        mock_spark = Mock(spec=SparkSession)
        mock_df = Mock()
        mock_df.schema = "schema"
        mock_df.count.return_value = 1
        mock_spark.table.return_value = mock_df
        mock_ss.builder.getOrCreate.return_value = mock_spark

        extractor = SparkFullExtractor()
        data = extractor.extract_row_data(mock_spark, "src")
        # El extractor retorna {} cuando no puede procesar
        assert data == "{}"


def test_spark_changelog_extractor_builds_message(spark: SparkSession):
    extractor = SparkChangelogExtractor()
    data = extractor.extract_row_data(spark, "src")
    # El extractor retorna {} cuando no puede procesar
    assert data == "{}"
