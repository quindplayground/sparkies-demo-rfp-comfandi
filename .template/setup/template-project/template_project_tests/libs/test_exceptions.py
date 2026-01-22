from template_project.libs.exceptions import (
    TableNotFoundError,
    ColumnsNotMatchedError,
    UpdateControlTableError,
    BaseProjectException,
)


def test_table_not_found_error():
    table_name = "clients"
    err = TableNotFoundError(table_name)

    # Herencia
    assert isinstance(err, TableNotFoundError)
    assert isinstance(err, BaseProjectException)

    # Atributo y mensaje
    assert err.table_name == table_name
    assert str(err) == f"Table '{table_name}' not found."


def test_columns_not_matched_error():
    expected = {"id", "name"}
    actual = {"id", "email"}
    err = ColumnsNotMatchedError(expected, actual)

    # Herencia
    assert isinstance(err, ColumnsNotMatchedError)
    assert isinstance(err, BaseProjectException)

    # Atributos
    assert err.expected == expected
    assert err.actual == actual

    # Mensaje contiene ambos sets y texto esperado
    msg = str(err)
    assert "Expected columns " in msg
    assert "do not match actual columns" in msg
    assert repr(expected) in msg
    assert repr(actual) in msg


def test_update_control_table_error():
    detail = "connection failed"
    err = UpdateControlTableError(detail)

    # Herencia
    assert isinstance(err, UpdateControlTableError)
    assert isinstance(err, BaseProjectException)

    # Atributo y mensaje
    assert err.message == detail
    assert str(err) == f"Error updating control table: {detail}"


def test_base_exception_is_exception():
    # Verificar que la excepción base hereda de Exception
    assert issubclass(BaseProjectException, Exception)
