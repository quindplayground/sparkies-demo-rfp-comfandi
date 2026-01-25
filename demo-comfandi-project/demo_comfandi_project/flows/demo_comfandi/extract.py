"""Extract module for demo_comfandi data flow.

This module handles data extraction from datos.gov.co API (SODA v3).
The extraction implements pagination, retries with exponential backoff,
and consolidates all pages into a single Spark DataFrame.
"""

import os
import time
from typing import Any

import requests
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from demo_comfandi_project.libs.error_handler import handle_errors
from demo_comfandi_project.libs.logging import get_logger
from demo_comfandi_project.libs.resources import VarsResource

logger = get_logger(__name__)

# API endpoint configuration
API_ENDPOINT = "https://www.datos.gov.co/api/v3/views/ese3-e6sh/query.json"
DEFAULT_PAGE_SIZE = 5000
DEFAULT_TIMEOUT = 60
MAX_RETRIES = 5
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

# Schema for the API response data
API_SCHEMA = StructType(
    [
        StructField("a_o", IntegerType(), True),
        StructField("mes", IntegerType(), True),
        StructField("ccf", StringType(), True),
        StructField("empresas_afiliadas", IntegerType(), True),
        StructField("total_afiliados_cajas", IntegerType(), True),
        StructField("trabajadores_afiliados", IntegerType(), True),
        StructField("afiliados_facultativos", IntegerType(), True),
        StructField("afiliados_pensionados", IntegerType(), True),
        StructField("afiliados_fidelidad", IntegerType(), True),
        StructField("no_afiliados_con_derecho", IntegerType(), True),
        StructField("personas_cargo_2", IntegerType(), True),
        StructField("total_poblaci_n_cubierta", IntegerType(), True),
    ]
)


def _get_app_token() -> str:
    """Get App Token from environment variable.

    Returns:
        App Token string.

    Raises:
        ValueError: If APP_TOKEN environment variable is not set.
    """
    app_token = os.getenv("APP_TOKEN")
    if not app_token:
        raise ValueError(
            "APP_TOKEN environment variable is required for API authentication. "
            "Set it as an environment variable or secret."
        )
    return app_token


def _make_api_request(
    page_number: int,
    page_size: int,
    app_token: str,
    soql_query: str | None = None,
    max_retries: int = MAX_RETRIES,
) -> dict[str, Any]:
    """Make a POST request to the API with retry logic.

    Args:
        page_number: Page number to request (starts at 1).
        page_size: Number of records per page.
        app_token: App Token for authentication.
        soql_query: Optional SoQL query string. If None, uses default SELECT.
        max_retries: Maximum number of retry attempts.

    Returns:
        JSON response from the API.

    Raises:
        requests.RequestException: If request fails after all retries.
    """
    if soql_query is None:
        soql_query = (
            "SELECT a_o, mes, ccf, empresas_afiliadas, total_afiliados_cajas, "
            "trabajadores_afiliados, afiliados_facultativos, afiliados_pensionados, "
            "afiliados_fidelidad, no_afiliados_con_derecho, personas_cargo_2, "
            "total_poblaci_n_cubierta"
        )

    payload = {
        "query": soql_query,
        "page": {"pageNumber": page_number, "pageSize": page_size},
        "includeSynthetic": False,
        "orderingSpecifier": "discard",
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-App-Token": app_token,
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                API_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=DEFAULT_TIMEOUT,
            )

            if response.status_code == 200:
                return response.json()

            if response.status_code in RETRY_STATUS_CODES:
                retry_after = response.headers.get("Retry-After")
                wait_time = (
                    int(retry_after) if retry_after else min(1.5 ** attempt, 60)
                )

                logger.warning(
                    f"API returned status {response.status_code} for page {page_number}. "
                    f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})",
                    extra={
                        "attributes": {
                            "page_number": page_number,
                            "status_code": response.status_code,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                        }
                    },
                )

                time.sleep(wait_time)
                continue

            if 400 <= response.status_code < 500 and response.status_code != 429:
                response.raise_for_status()

            response.raise_for_status()

        except requests.Timeout:
            wait_time = min(1.5 ** attempt, 60)
            logger.warning(
                f"Request timeout for page {page_number}. "
                f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})",
                extra={
                    "attributes": {
                        "page_number": page_number,
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                    }
                },
            )
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                continue
            raise

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = min(1.5 ** attempt, 60)
                logger.warning(
                    f"Request error for page {page_number}: {str(e)}. "
                    f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})",
                    extra={
                        "attributes": {
                            "page_number": page_number,
                            "error": str(e),
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                        }
                    },
                )
                time.sleep(wait_time)
                continue
            raise

    raise requests.RequestException(
        f"Failed to fetch page {page_number} after {max_retries} attempts"
    )


def _extract_all_pages(
    spark: SparkSession,
    app_token: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    soql_query: str | None = None,
    max_pages: int | None = None,
) -> list[dict[str, Any]]:
    """Extract all pages from the API with pagination.

    Args:
        spark: SparkSession instance.
        app_token: App Token for authentication.
        page_size: Number of records per page.
        soql_query: Optional SoQL query string.
        max_pages: Optional maximum number of pages to fetch (for testing).

    Returns:
        List of all records from all pages.
    """
    all_records = []
    page_number = 1
    total_pages = 0

    logger.info(
        "Starting API extraction with pagination",
        extra={
            "attributes": {
                "endpoint": API_ENDPOINT,
                "page_size": page_size,
                "max_pages": max_pages,
            }
        },
    )

    while True:
        if max_pages and page_number > max_pages:
            logger.info(
                f"Reached max_pages limit ({max_pages})",
                extra={"attributes": {"page_number": page_number}},
            )
            break

        start_time = time.time()
        response_data = _make_api_request(
            page_number=page_number,
            page_size=page_size,
            app_token=app_token,
            soql_query=soql_query,
        )

        records = response_data.get("data", [])
        rows_received = len(records)

        all_records.extend(records)
        total_pages += 1
        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Fetched page {page_number}",
            extra={
                "attributes": {
                    "page_number": page_number,
                    "rows_received": rows_received,
                    "total_rows_accumulated": len(all_records),
                    "latency_ms": latency_ms,
                }
            },
        )

        if rows_received == 0 or rows_received < page_size:
            logger.info(
                f"Pagination complete. Last page had {rows_received} rows",
                extra={
                    "attributes": {
                        "page_number": page_number,
                        "rows_received": rows_received,
                        "total_pages": total_pages,
                        "total_rows": len(all_records),
                    }
                },
            )
            break

        page_number += 1

    return all_records


@handle_errors
def extract(
    spark: SparkSession,
    vars_instance: VarsResource,
    **kwargs,
) -> DataFrame:
    """Extract data from datos.gov.co API (SODA v3).

    This function implements extraction from the datos.gov.co API with:
    - POST requests with App Token authentication
    - Pagination support (fetches all pages)
    - Retry logic with exponential backoff for 429 and 5xx errors
    - Consolidation of all pages into a single DataFrame

    Args:
        spark: SparkSession for data processing.
        vars_instance: VarsResource instance with configuration.
            - vars_instance.vars.input.table_id: Source identifier (for logging)
        **kwargs: Optional parameters:
            - page_size: Number of records per page (default: 5000)
            - soql_query: Custom SoQL query string (optional)
            - max_pages: Maximum number of pages to fetch (for testing, optional)

    Returns:
        DataFrame containing extracted data from the API.

    Raises:
        ValueError: If APP_TOKEN environment variable is not set.
        requests.RequestException: If API requests fail after retries.
    """
    source_id = vars_instance.vars.input.table_id

    logger.info(
        "Extracting data from datos.gov.co API",
        extra={
            "attributes": {
                "source": source_id,
                "endpoint": API_ENDPOINT,
            }
        },
    )

    app_token = _get_app_token()
    page_size = kwargs.get("page_size", DEFAULT_PAGE_SIZE)
    soql_query = kwargs.get("soql_query", None)
    max_pages = kwargs.get("max_pages", None)

    all_records = _extract_all_pages(
        spark=spark,
        app_token=app_token,
        page_size=page_size,
        soql_query=soql_query,
        max_pages=max_pages,
    )

    if not all_records:
        logger.warning(
            "No records extracted from API",
            extra={"attributes": {"source": source_id}},
        )
        return spark.createDataFrame([], schema=API_SCHEMA)

    logger.info(
        f"Extracted {len(all_records)} records from API",
        extra={
            "attributes": {
                "source": source_id,
                "total_records": len(all_records),
            }
        },
    )

    df = spark.createDataFrame(all_records, schema=API_SCHEMA)

    logger.info(
        "Data extraction completed successfully",
        extra={
            "attributes": {
                "source": source_id,
                "rows": df.count(),
                "columns": len(df.columns),
            }
        },
    )

    return df
