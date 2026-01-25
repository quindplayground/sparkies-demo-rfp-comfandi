import pytest
from unittest.mock import Mock, patch, create_autospec
from pyspark.sql import SparkSession
from pyspark import SparkConf

from template_project.libs.resources.spark_resource import SparkResource


@pytest.fixture
def mock_spark_session():
    """Create a mock SparkSession."""
    mock_spark = create_autospec(SparkSession, instance=True)
    return mock_spark


@pytest.fixture
def mock_builder(mock_spark_session):
    """Create a mock SparkSession.Builder."""
    mock_builder = Mock()
    mock_builder.enableHiveSupport.return_value = mock_builder
    mock_builder.config.return_value = mock_builder
    mock_builder.getOrCreate.return_value = mock_spark_session
    return mock_builder


def test_spark_resource_first_instance(mock_builder, mock_spark_session):
    """Test creating first instance of SparkResource."""
    with patch("pyspark.sql.SparkSession.builder", mock_builder):
        SparkResource._instance = None
        spark = SparkResource()

        mock_builder.enableHiveSupport.assert_called_once()
        mock_builder.config.assert_called_once()
        mock_builder.getOrCreate.assert_called_once()
        assert spark == mock_spark_session


def test_spark_resource_subsequent_instance(mock_builder, mock_spark_session):
    """Test getting subsequent instance of SparkResource."""
    with patch("pyspark.sql.SparkSession.builder", mock_builder):
        SparkResource._instance = mock_spark_session
        spark = SparkResource()

        mock_builder.enableHiveSupport.assert_not_called()
        mock_builder.config.assert_not_called()
        mock_builder.getOrCreate.assert_not_called()
        assert spark == mock_spark_session


def test_spark_resource_new_session(mock_builder, mock_spark_session):
    """Test creating new session."""
    new_session = create_autospec(SparkSession, instance=True)
    mock_spark_session.newSession.return_value = new_session

    with patch("pyspark.sql.SparkSession.builder", mock_builder):
        SparkResource._instance = mock_spark_session
        spark = SparkResource(new_session=True)

        mock_spark_session.newSession.assert_called_once()
        assert spark == new_session


def test_spark_resource_with_custom_conf(mock_builder, mock_spark_session):
    """Test creating SparkResource with custom configuration."""
    custom_conf = SparkConf().set("spark.app.name", "test_app")

    with patch("pyspark.sql.SparkSession.builder", mock_builder):
        SparkResource._instance = None
        SparkResource(conf=custom_conf)

        mock_builder.config.assert_called_once_with(conf=custom_conf)


def test_spark_resource_without_hive_support(mock_builder, mock_spark_session):
    """Test creating SparkResource without Hive support."""
    with patch("pyspark.sql.SparkSession.builder", mock_builder):
        SparkResource._instance = None
        SparkResource(enable_hive_support=False)

        mock_builder.enableHiveSupport.assert_not_called()
        mock_builder.config.assert_called_once()
        mock_builder.getOrCreate.assert_called_once()
