import os
import pytest
from unittest.mock import MagicMock, patch, Mock
from pyspark.sql import SparkSession
from pyspark.testing.utils import assertDataFrameEqual, assertSchemaEqual
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructType,
    StructField,
)

from demo_comfandi_project.flows.demo_comfandi.extract import (
    extract,
    _get_app_token,
    _make_api_request,
    _extract_all_pages,
    API_SCHEMA,
)


@pytest.fixture(scope="session")
def spark():
    """Create SparkSession for testing (shared across tests)."""
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    yield spark
    spark.stop()


@pytest.fixture
def mock_vars_resource():
    """Create mock VarsResource."""
    mock_vars = MagicMock()
    mock_vars.vars.input.table_id = "test.input.table"
    mock_vars.vars.output.table_id = "test.output.table"
    return mock_vars


def test_get_app_token_success():
    """Test successful retrieval of APP_TOKEN from environment."""
    with patch.dict(os.environ, {"APP_TOKEN": "test_token_123"}):
        result = _get_app_token()
        assert result == "test_token_123"


def test_get_app_token_missing():
    """Test that ValueError is raised when APP_TOKEN is not set."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="APP_TOKEN environment variable is required"):
            _get_app_token()


@patch("demo_comfandi_project.flows.demo_comfandi.extract.requests.post")
def test_make_api_request_success(mock_post):
    """Test successful API request."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"a_o": 2024, "mes": 1, "ccf": "TEST"}]}
    mock_post.return_value = mock_response

    result = _make_api_request(
        page_number=1,
        page_size=100,
        app_token="test_token",
    )

    assert result == {"data": [{"a_o": 2024, "mes": 1, "ccf": "TEST"}]}
    mock_post.assert_called_once()


@patch("demo_comfandi_project.flows.demo_comfandi.extract.requests.post")
@patch("demo_comfandi_project.flows.demo_comfandi.extract.time.sleep")
def test_make_api_request_retry_on_429(mock_sleep, mock_post):
    """Test retry logic on 429 status code."""
    mock_response_429 = Mock()
    mock_response_429.status_code = 429
    mock_response_429.headers.get.return_value = "2"

    mock_response_200 = Mock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"data": []}

    mock_post.side_effect = [mock_response_429, mock_response_200]

    result = _make_api_request(
        page_number=1,
        page_size=100,
        app_token="test_token",
        max_retries=2,
    )

    assert result == {"data": []}
    assert mock_post.call_count == 2
    mock_sleep.assert_called_once_with(2)


@patch("demo_comfandi_project.flows.demo_comfandi.extract._make_api_request")
def test_extract_all_pages_single_page(mock_api_request, spark):
    """Test extraction of single page."""
    mock_api_request.return_value = {
        "data": [
            {"a_o": 2024, "mes": 1, "ccf": "CCF001", "empresas_afiliadas": 10},
            {"a_o": 2024, "mes": 2, "ccf": "CCF002", "empresas_afiliadas": 20},
        ]
    }

    result = _extract_all_pages(
        spark=spark,
        app_token="test_token",
        page_size=100,
        max_pages=1,
    )

    assert len(result) == 2
    assert result[0]["a_o"] == 2024
    assert result[1]["ccf"] == "CCF002"


@patch("demo_comfandi_project.flows.demo_comfandi.extract._make_api_request")
def test_extract_all_pages_multiple_pages(mock_api_request, spark):
    """Test extraction of multiple pages."""
    mock_api_request.side_effect = [
        {"data": [{"a_o": 2024, "mes": 1, "ccf": "CCF001"}]},
        {"data": [{"a_o": 2024, "mes": 2, "ccf": "CCF002"}]},
        {"data": []},
    ]

    result = _extract_all_pages(
        spark=spark,
        app_token="test_token",
        page_size=1,
    )

    assert len(result) == 2
    assert mock_api_request.call_count == 3


@patch("demo_comfandi_project.flows.demo_comfandi.extract._extract_all_pages")
@patch("demo_comfandi_project.flows.demo_comfandi.extract._get_app_token")
def test_extract_success(mock_get_token, mock_extract_pages, spark, mock_vars_resource):
    """Test successful extraction with data."""
    mock_get_token.return_value = "test_token"
    mock_extract_pages.return_value = [
        {
            "a_o": 2024,
            "mes": 1,
            "ccf": "CCF001",
            "empresas_afiliadas": 10,
            "total_afiliados_cajas": 100,
            "trabajadores_afiliados": 80,
            "afiliados_facultativos": 5,
            "afiliados_pensionados": 10,
            "afiliados_fidelidad": 5,
            "no_afiliados_con_derecho": 0,
            "personas_cargo_2": 20,
            "total_poblaci_n_cubierta": 120,
        },
        {
            "a_o": 2024,
            "mes": 2,
            "ccf": "CCF002",
            "empresas_afiliadas": 20,
            "total_afiliados_cajas": 200,
            "trabajadores_afiliados": 160,
            "afiliados_facultativos": 10,
            "afiliados_pensionados": 20,
            "afiliados_fidelidad": 10,
            "no_afiliados_con_derecho": 0,
            "personas_cargo_2": 40,
            "total_poblaci_n_cubierta": 240,
        },
    ]

    expected_data = [
        (
            2024,
            1,
            "CCF001",
            10,
            100,
            80,
            5,
            10,
            5,
            0,
            20,
            120,
        ),
        (
            2024,
            2,
            "CCF002",
            20,
            200,
            160,
            10,
            20,
            10,
            0,
            40,
            240,
        ),
    ]
    expected_df = spark.createDataFrame(expected_data, schema=API_SCHEMA)

    result = extract(spark, mock_vars_resource)

    assertDataFrameEqual(result, expected_df)
    assertSchemaEqual(result.schema, expected_df.schema)


@patch("demo_comfandi_project.flows.demo_comfandi.extract._extract_all_pages")
@patch("demo_comfandi_project.flows.demo_comfandi.extract._get_app_token")
def test_extract_empty_result(mock_get_token, mock_extract_pages, spark, mock_vars_resource):
    """Test extraction when API returns no data."""
    mock_get_token.return_value = "test_token"
    mock_extract_pages.return_value = []

    result = extract(spark, mock_vars_resource)

    assert result.count() == 0
    assertSchemaEqual(result.schema, API_SCHEMA)


@patch("demo_comfandi_project.flows.demo_comfandi.extract._extract_all_pages")
@patch("demo_comfandi_project.flows.demo_comfandi.extract._get_app_token")
def test_extract_with_custom_page_size(mock_get_token, mock_extract_pages, spark, mock_vars_resource):
    """Test extraction with custom page size."""
    mock_get_token.return_value = "test_token"
    mock_extract_pages.return_value = [
        {"a_o": 2024, "mes": 1, "ccf": "CCF001", "empresas_afiliadas": 10}
    ]

    extract(spark, mock_vars_resource, page_size=1000)

    mock_extract_pages.assert_called_once()
    call_kwargs = mock_extract_pages.call_args[1]
    assert call_kwargs["page_size"] == 1000


@patch("demo_comfandi_project.flows.demo_comfandi.extract._extract_all_pages")
@patch("demo_comfandi_project.flows.demo_comfandi.extract._get_app_token")
def test_extract_with_max_pages(mock_get_token, mock_extract_pages, spark, mock_vars_resource):
    """Test extraction with max_pages limit."""
    mock_get_token.return_value = "test_token"
    mock_extract_pages.return_value = [
        {"a_o": 2024, "mes": 1, "ccf": "CCF001", "empresas_afiliadas": 10}
    ]

    extract(spark, mock_vars_resource, max_pages=5)

    mock_extract_pages.assert_called_once()
    call_kwargs = mock_extract_pages.call_args[1]
    assert call_kwargs["max_pages"] == 5
