"""DynamoDB data loader using Spark."""

from demo_comfandi_project.libs.resources import VarsResource
from demo_comfandi_project.libs.aws.dynamodb.loader.handlers.factory import (
    HandlerFactory,
)
from demo_comfandi_project.libs.logging.logger import get_logger
from demo_comfandi_project.libs.aws.dynamodb.loader.types import (
    InputDynamoDBLoaderDataFrame,
)
from pydantic import TypeAdapter, ValidationError


class DynamoDBLoader:
    """Loader class for loading data to DynamoDB using Spark."""

    def __init__(
        self,
        job_id: str,
        vars_instance: VarsResource,
        handler_factory: HandlerFactory | None = None,
    ):
        """Initialize the DynamoDBLoader.

        Args:
            job_id: Job identifier.
            vars_instance: Configuration variables instance.
            handler_factory: Handler factory instance (optional).
        """
        self.logger = get_logger(__name__, capture_spark_logs=False)
        self.handler_factory = handler_factory or HandlerFactory()
        self.job_id = job_id
        self.vars = vars_instance
        self.region = vars_instance.vars.output.region
        self.table_name = vars_instance.vars.output.table_name
        self.item_size_limit = vars_instance.vars.output.item_size_limit

    def _validate_dataframes(self, dataframes: InputDynamoDBLoaderDataFrame) -> None:
        """Validate input DataFrames.

        Args:
            dataframes: Input DataFrames to validate.

        Raises:
            ValidationError: If the schema is invalid.
        """
        dict_validator = TypeAdapter(InputDynamoDBLoaderDataFrame)

        self.logger.info(
            "Validating dataframes",
            extra={
                "attributes": {
                    "job_id": self.job_id,
                    "operation": "VALIDATING_DATAFRAMES",
                    "state": "IN_PROGRESS",
                    "table_name": self.table_name,
                    "dataframes": dataframes,
                }
            },
        )

        try:
            _ = dict_validator.validate_python(dataframes)
        except ValidationError as exc:
            self.logger.error(
                "Invalid schema",
                extra={
                    "attributes": {
                        "job_id": self.job_id,
                        "table_name": self.table_name,
                        "operation": "VALIDATING_DATAFRAMES",
                        "state": "ERROR",
                        "error": exc,
                    }
                },
                exc_info=exc,
            )
            raise exc

        self.logger.info(
            "Dataframes validated",
            extra={
                "attributes": {
                    "job_id": self.job_id,
                    "operation": "VALIDATING_DATAFRAMES",
                    "state": "SUCCESS",
                    "table_name": self.table_name,
                    "dataframes": dataframes,
                }
            },
        )

    def load(
        self,
        dataframes: InputDynamoDBLoaderDataFrame,
        first_run: bool,
        write_handler: str = "portfolio_writer",
        delete_handler: str = "delete",
    ) -> None:
        """Load data to DynamoDB using the specified handlers.

        Args:
            dataframes: Dictionary with DataFrames of data to write and delete.
            first_run: Whether this is the first execution.
            write_handler: Name of the handler for write operations.
            delete_handler: Name of the handler for delete operations.
        """
        self._validate_dataframes(dataframes)

        self.logger.info(
            "Loading items to DynamoDB",
            extra={
                "attributes": {
                    "job_id": self.job_id,
                    "operation": "LOADING_ITEMS_TO_DYNAMODB",
                    "state": "IN_PROGRESS",
                    "table_name": self.table_name,
                    "item_size_limit": self.item_size_limit,
                }
            },
        )

        write_handler_instance = self.handler_factory[write_handler](
            self.job_id, self.region, self.table_name, self.item_size_limit
        )

        dataframes["data_to_write"].rdd.foreachPartition(
            write_handler_instance.create_partition_handler()
        )

        if not first_run:
            delete_handler_instance = self.handler_factory[delete_handler](
                self.job_id, self.region, self.table_name, self.item_size_limit
            )

            dataframes["data_to_delete"].rdd.foreachPartition(
                delete_handler_instance.create_partition_handler()
            )

        self.logger.info(
            "Items loaded to DynamoDB",
            extra={
                "attributes": {
                    "job_id": self.job_id,
                    "operation": "LOADING_ITEMS_TO_DYNAMODB",
                    "state": "SUCCESS",
                    "table_name": self.table_name,
                    "item_size_limit": self.item_size_limit,
                    "first_run": first_run,
                }
            },
        )
