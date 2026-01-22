"""Restart DynamoDB table by truncating all data."""

from demo_comfandi_project.libs.aws.dynamodb.loader.utils import get_table
from demo_comfandi_project.libs.aws.dynamodb.truncate_table import truncate_table


def restart_table(table_name: str, region: str) -> bool:
    """Restart the output table by truncating all data.

    Args:
        table_name: Name of the DynamoDB table.
        region: AWS region where the table is located.

    Returns:
        True if the table was restarted successfully, False otherwise.
    """
    dynamodb_table = get_table(region, table_name)

    dynamodb_result = truncate_table(dynamodb_table)

    if not dynamodb_result:
        return False

    return True
