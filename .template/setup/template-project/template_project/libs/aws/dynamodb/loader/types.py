"""Type definitions for DynamoDB loader."""

from typing_extensions import TypedDict
from pyspark.sql import DataFrame
from pydantic import ConfigDict


class InputDynamoDBLoaderDataFrame(TypedDict):
    """Type definition for input DataFrames dictionary for DynamoDB loader.

    Attributes:
        data_to_write: DataFrame containing data to write.
        data_to_delete: DataFrame containing data to delete.
    """

    __pydantic_config__ = ConfigDict(arbitrary_types_allowed=True)

    data_to_write: DataFrame
    data_to_delete: DataFrame
