"""Batch delete operations for DynamoDB."""

from botocore.exceptions import ClientError
from mypy_boto3_dynamodb.service_resource import Table

from demo_comfandi_project.libs.logging import get_logger


def truncate_table(dynamodb_table: Table) -> bool:
    """Truncate a DynamoDB table by deleting all items.

    Args:
        dynamodb_table: DynamoDB table resource.

    Returns:
        True if the operation was successful, False otherwise.
    """
    logger = get_logger(__name__)

    key_names = [key["AttributeName"] for key in dynamodb_table.key_schema]

    projection = ", ".join(f"#{k}" for k in key_names)
    expr_attr_names = {f"#{k}": k for k in key_names}

    page = dynamodb_table.scan(
        ProjectionExpression=projection, ExpressionAttributeNames=expr_attr_names
    )

    deleted_count = 0

    try:
        with dynamodb_table.batch_writer() as batch:
            while True:
                for item in page.get("Items", []):
                    batch.delete_item(Key={k: item[k] for k in key_names})
                deleted_count += page.get("Count", 0)

                if "LastEvaluatedKey" in page:
                    page = dynamodb_table.scan(
                        ProjectionExpression=projection,
                        ExpressionAttributeNames=expr_attr_names,
                        ExclusiveStartKey=page["LastEvaluatedKey"],
                    )
                else:
                    break

        logger.info(
            "Items deleted", extra={"attributes": {"deleted_count": deleted_count}}
        )
        return True

    except ClientError as e:
        logger.error(
            "Error deleting items", extra={"attributes": {"error": e}}, exc_info=e
        )

        return False
