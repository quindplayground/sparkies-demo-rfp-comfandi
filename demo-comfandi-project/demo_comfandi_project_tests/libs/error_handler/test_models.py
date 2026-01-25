from datetime import datetime
from unittest.mock import Mock
from pyspark.sql import SparkSession
from pyspark.sql import DataFrame

from demo_comfandi_project.libs.error_handler.models import ErrorData, ErrorArgs


def test_error_data_computed_message_and_source_coercion():
    # error como excepción con traceback
    err = ValueError("boom")
    # source como DataFrame -> debe coercionarse a str
    df = Mock(spec=DataFrame)
    df.__str__ = Mock(return_value="<DataFrame ...>")
    ed = ErrorData(source=df, step=None, error=err, row_data="{}")
    assert isinstance(ed.timestamp, datetime)
    emsg = str(ed.error_message)
    assert "Traceback:" in emsg
    assert ed.source == "<DataFrame ...>"
    # step no string -> debe quedar "UNKNOWN"
    assert ed.step == "UNKNOWN"


def test_error_args_types_and_defaults(spark: SparkSession):
    ea = ErrorArgs(
        spark=spark,
        error_path="/tmp/errors",
    )
    assert ea.extractor == "full"
    assert ea.writer == "spark_csv"
    assert ea.fail_fast is True
    assert ea.step is None
    assert ea.source is None
