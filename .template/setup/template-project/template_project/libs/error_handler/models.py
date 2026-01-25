"""Error data models."""

import traceback
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, computed_field, field_validator
from pyspark.sql import DataFrame, SparkSession


class ErrorData(BaseModel):
    """Model representing structured error data.

    Attributes:
        source: Source of the error.
        step: Step where the error occurred.
        error: The error that occurred.
        row_data: Row data associated with the error.
        timestamp: Timestamp when the error occurred.
    """

    source: str | DataFrame | None = None
    step: str | None = None
    error: Any
    row_data: str
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {"arbitrary_types_allowed": True}

    @computed_field
    def error_message(self) -> str:
        """Generate a formatted error message including traceback.

        Returns:
            The formatted error message with traceback information.
        """
        msg = f"{str(self.error)} \n Traceback: {''.join(traceback.format_tb(self.error.__traceback__))}"
        return msg.replace("\n", "\\n")

    @field_validator("source", mode="after")
    @classmethod
    def inpute_source(cls, value: Any) -> str:
        """Validate and convert source to string.

        Args:
            value: The source value to validate.

        Returns:
            String representation of the source.
        """
        if isinstance(value, DataFrame):
            return value.__str__()

        if isinstance(value, str):
            return value

        return "UNKNOWN"

    @field_validator("step", mode="after")
    @classmethod
    def inpute_step(cls, value: Any) -> str:
        """Validate and convert step to string.

        Args:
            value: The step value to validate.

        Returns:
            String representation of the step.
        """
        if not isinstance(value, str):
            return "UNKNOWN"
        else:
            return value


class ErrorArgs(BaseModel):
    """Model representing error handler arguments.

    Attributes:
        spark: Spark session.
        error_path: Path where errors should be written.
        extractor: Extractor type to use.
        writer: Writer type to use.
        fail_fast: Whether to fail fast on errors.
        step: Step where the error occurred.
        source: Source of the error.
    """

    spark: SparkSession
    error_path: str
    extractor: str = "full"
    writer: str = "spark_csv"
    fail_fast: bool = True
    step: str | None = None
    source: str | DataFrame | None = None

    model_config = {"arbitrary_types_allowed": True}
