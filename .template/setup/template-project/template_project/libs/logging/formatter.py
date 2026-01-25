"""OpenTelemetry JSON-style log formatter."""

import json
import logging
import os

from datetime import datetime, timezone
from typing import Any

from template_project.libs.logging.defaults import LoggingDefaults
from template_project.libs.context import Context


OTEL_LEVEL_MAP: dict[int, int] = {
    logging.DEBUG: 5,
    logging.INFO: 9,
    logging.WARNING: 13,
    logging.ERROR: 17,
    logging.CRITICAL: 21,
}

LOG_RECORD_FLAGS = {
    "TRACE_FLAGS_MASK": 0xFF,
    "TRACE_FLAGS_SAMPLED": 0x01,
    "TRACE_FLAGS_DEFAULT": 0x01,
}


class OtelStyleJsonFormatter(logging.Formatter):
    """OpenTelemetry JSON-style log formatter."""

    def __init__(
        self,
        default_attributes: dict[str, Any] | None = None,
        context: Context | None = None,
        service_name: str | None = None,
        service_version: str | None = None,
        schema_url: str | None = None,
        add_spark_prefix: bool = True,
    ) -> None:
        """Initialize the OtelStyleJsonFormatter.

        Args:
            default_attributes: Default attributes (optional).
            context: Context for Opel data (optional).
            service_name: Service name for OpenTelemetry (optional).
            service_version: Service version for OpenTelemetry (optional).
            schema_url: Schema URL for OpenTelemetry (optional).
            add_spark_prefix: Whether to add Spark prefix. Defaults to True.
        """
        super().__init__()
        self.default_attributes = default_attributes or {}
        self.context = context or Context()
        self.service_name = service_name or LoggingDefaults.DEFAULT_SERVICE_NAME.value
        self.service_version = (
            service_version or LoggingDefaults.DEFAULT_SERVICE_VERSION.value
        )
        self.schema_url = schema_url or LoggingDefaults.DEFAULT_SCHEMA_URL.value
        self.add_spark_prefix = add_spark_prefix

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record into OpenTelemetry JSON format.

        Args:
            record: Log record to format.

        Returns:
            Formatted log record as JSON string.
        """
        now_utc = datetime.now(timezone.utc)
        now_local = datetime.now()
        severity_number = OTEL_LEVEL_MAP.get(record.levelno, 11)
        severity_text = record.levelname

        attributes = self._build_attributes(record)
        resource_attributes = self._build_resource_attributes()
        instrumentation_scope = self._build_instrumentation_scope()

        log_obj = {
            "timestamp": now_utc.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
            "observed_timestamp": now_utc.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
            "severity_text": severity_text,
            "severity_number": severity_number,
            "body": record.getMessage(),
            "attributes": attributes,
            "dropped_attributes_count": 0,
            "trace_id": self.context.get("opel/trace_id") if self.context else None,
            "span_id": self.context.get("opel/span_id") if self.context else None,
            "trace_flags": (
                self.context.get("opel/trace_flags") if self.context else None
            )
            or LOG_RECORD_FLAGS["TRACE_FLAGS_SAMPLED"],
            "flags": LOG_RECORD_FLAGS["TRACE_FLAGS_SAMPLED"],
            "resource": {
                "attributes": resource_attributes,
                "dropped_attributes_count": 0,
            },
            "instrumentation_scope": instrumentation_scope,
        }

        json_output = json.dumps(log_obj, ensure_ascii=False, default=str)

        if self.add_spark_prefix:
            spark_prefix = f"{now_local.strftime('%d/%m/%y %H:%M:%S')} {severity_text} {record.name}: "
            return f"{spark_prefix}{json_output}"
        else:
            return json_output

    def _build_attributes(self, record: logging.LogRecord) -> dict[str, Any]:
        """Build log attributes from the record.

        Args:
            record: Log record.

        Returns:
            Dictionary with log attributes.
        """
        attributes = dict(self.default_attributes)

        extra_attrs = getattr(record, "attributes", None)
        if isinstance(extra_attrs, dict):
            attributes.update(extra_attrs)

        extra_attrs_alt = getattr(record, "extra_attributes", None)
        if isinstance(extra_attrs_alt, dict):
            attributes.update(extra_attrs_alt)

        if hasattr(record, "funcName") and record.funcName:
            attributes["code.function"] = record.funcName
        if hasattr(record, "pathname") and record.pathname:
            attributes["code.filepath"] = record.pathname
        if hasattr(record, "lineno") and record.lineno:
            attributes["code.lineno"] = record.lineno

        self._add_exception_info(record, attributes)

        return attributes

    @staticmethod
    def _add_exception_info(
        record: logging.LogRecord, attributes: dict[str, Any]
    ) -> None:
        """Add exception information to attributes.

        Args:
            record: Log record.
            attributes: Attributes dictionary to modify.
        """
        if not record.exc_info:
            return

        try:
            import traceback

            ex_type = record.exc_info[0].__name__
            ex_msg = str(record.exc_info[1])
            ex_traceback = "".join(traceback.format_tb(record.exc_info[2]))

            attributes["exception.type"] = ex_type
            attributes["exception.message"] = ex_msg
            attributes["exception.stacktrace"] = ex_traceback
        except Exception:
            pass

    def _build_resource_attributes(self) -> dict[str, Any]:
        """Build resource attributes for OpenTelemetry.

        Returns:
            Dictionary with resource attributes.
        """
        resource_attributes = {
            "service.name": self.service_name,
            "service.version": self.service_version,
        }

        hostname = os.environ.get("HOSTNAME") or os.uname().nodename
        if hostname:
            resource_attributes["host.name"] = hostname

        resource_attributes["process.pid"] = os.getpid()

        if "AWS_REGION" in os.environ:
            resource_attributes["cloud.region"] = os.environ["AWS_REGION"]
            resource_attributes["cloud.provider"] = "aws"

        opel_resource = self.context.get("opel/resource") if self.context else None
        if isinstance(opel_resource, dict):
            resource_attributes.update(opel_resource)

        return resource_attributes

    def _build_instrumentation_scope(self) -> dict[str, Any]:
        """Build instrumentation scope for OpenTelemetry.

        Returns:
            Dictionary with instrumentation scope.
        """
        return {
            "name": self.service_name,
            "version": (self.context.get("opel/version") if self.context else None)
            or self.service_version,
            "schema_url": self.schema_url,
            "attributes": (
                self.context.get("opel/instrumentation_attributes")
                if self.context
                else None
            )
            or {},
            "dropped_attributes_count": 0,
        }
