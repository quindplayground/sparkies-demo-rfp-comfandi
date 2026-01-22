from dynaconf.utils.boxing import DynaBox

from demo_comfandi_project.libs.utils import get_key_by_value


def test_get_key_by_value_found():
    box = DynaBox({"key1": "value1", "key2": "value2", "key3": "value1"})
    result = get_key_by_value(box, "value1")
    assert result == "key1"  # Primera coincidencia


def test_get_key_by_value_not_found():
    box = DynaBox({"key1": "value1", "key2": "value2"})
    result = get_key_by_value(box, "value3")
    assert result is None


def test_get_key_by_value_empty_box():
    box = DynaBox({})
    result = get_key_by_value(box, "value1")
    assert result is None
