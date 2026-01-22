"""Resources module for Spark and configuration management."""

from template_project.libs.resources.vars.resource import (
    VarsResource,
    get_vars_resource,
)
from template_project.libs.resources.spark_resource import SparkResource

__all__ = ["VarsResource", "SparkResource", "get_vars_resource"]
