import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    """Fixture global para crear una única instancia de SparkSession para todos los tests."""
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    yield spark
    spark.stop() 