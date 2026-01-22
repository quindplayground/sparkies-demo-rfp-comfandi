"""Utility functions for DynamoDB operations."""

from botocore.exceptions import ClientError

import threading


import boto3
from botocore.config import Config
from mypy_boto3_dynamodb.service_resource import Table


_table_singleton = {}
_table_lock = threading.Lock()


def get_table(region: str, table_name: str) -> Table:
    """Get a DynamoDB table instance using singleton pattern.

    Args:
        region: AWS region where the table is located.
        table_name: Name of the DynamoDB table.

    Returns:
        DynamoDB table instance.
    """
    key = (region, table_name)
    if key not in _table_singleton:
        with _table_lock:
            if key not in _table_singleton:
                cfg = Config(max_pool_connections=64, retries={'max_attempts': 12, 'mode': 'adaptive'})
                dynamodb_client = boto3.resource(
                    "dynamodb",
                    region_name=region,
                    config=cfg
                )
                _table_singleton[key] = dynamodb_client.Table(table_name)
    return _table_singleton[key]


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable in DynamoDB.

    Args:
        error: Error to check.

    Returns:
        True if the error is retryable, False otherwise.
    """
    if isinstance(error, ClientError):
        error_code = error.response.get("Error", {}).get("Code", "")
        if error_code == "ThrottlingException":
            return True
    return False