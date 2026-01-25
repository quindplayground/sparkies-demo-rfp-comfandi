"""Factory for DynamoDB operation handlers."""

from demo_comfandi_project.libs.aws.dynamodb.loader.handlers.base import (
    DynamoDBOperationHandler,
)


class HandlerFactory:
    """Factory class for creating handler instances."""

    map_handler: dict[str, type[DynamoDBOperationHandler]] = {
    }

    @classmethod
    def get_handler(cls, handler_name: str) -> type[DynamoDBOperationHandler]:
        """Get a handler class by handler name.

        Args:
            handler_name: Name of the handler to retrieve.

        Returns:
            The requested handler class.

        Raises:
            ValueError: If the handler name is invalid.
        """
        if handler_name not in cls.map_handler:
            raise ValueError(f"Invalid handler name: {handler_name}")
        return cls.map_handler[handler_name]

    def __getitem__(self, handler_name: str) -> type[DynamoDBOperationHandler]:
        """Get a handler class by handler name using bracket notation.

        Args:
            handler_name: Name of the handler to retrieve.

        Returns:
            The requested handler class.
        """
        return self.get_handler(handler_name)

    def __contains__(self, handler_name: str) -> bool:
        """Check if a handler name exists in the map.

        Args:
            handler_name: Name of the handler to check.

        Returns:
            True if the handler name exists, False otherwise.
        """
        return handler_name in self.map_handler
