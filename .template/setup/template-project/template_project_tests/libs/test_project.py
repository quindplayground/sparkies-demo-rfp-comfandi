import tempfile
import pytest
from pathlib import Path
from dynaconf.utils.boxing import DynaBox
from template_project.libs.utils import get_package_resource_path, get_key_by_value


@pytest.fixture(autouse=True)
def force_tempdir_to_tmp_path(tmp_path, monkeypatch):
    fake_tmp = tmp_path / "temp_for_tests"
    fake_tmp.mkdir()
    monkeypatch.setenv("TMPDIR", str(fake_tmp))
    monkeypatch.setenv("TEMP", str(fake_tmp))
    monkeypatch.setenv("TMP", str(fake_tmp))
    yield


@pytest.fixture
def create_fake_package(tmp_path, monkeypatch):
    pkg_root = tmp_path / "testpkg"
    pkg_root.mkdir()

    init_file = pkg_root / "__init__.py"
    init_file.write_text("# paquete de prueba\n", encoding="utf-8")

    subdir = pkg_root / "subdir"
    subdir.mkdir()
    inner_txt = subdir / "inner.txt"
    inner_txt.write_text("contenido interno\n", encoding="utf-8")

    file_txt = pkg_root / "file.txt"
    file_txt.write_text("contenido de file.txt\n", encoding="utf-8")

    monkeypatch.syspath_prepend(str(tmp_path))

    return "testpkg"


@pytest.fixture
def create_fake_module(tmp_path, monkeypatch):
    mod_path = tmp_path / "testmod.py"
    mod_path.write_text("x = 123\n", encoding="utf-8")

    monkeypatch.syspath_prepend(str(tmp_path))
    return "testmod"


def test_copy_entire_package(create_fake_package):
    package_name = create_fake_package

    dest = get_package_resource_path(package_name)

    assert isinstance(dest, Path)

    expected_root = Path(tempfile.gettempdir()) / package_name
    assert dest == expected_root

    assert (dest / "__init__.py").exists(), "__init__.py no fue copiado"
    assert (dest / "file.txt").exists(), "file.txt no fue copiado"
    assert (dest / "subdir").is_dir(), "subdir no fue copiado como directorio"
    assert (
        dest / "subdir" / "inner.txt"
    ).exists(), "inner.txt no fue copiado dentro de subdir"

    contenido = (dest / "subdir" / "inner.txt").read_text(encoding="utf-8")
    assert contenido == "contenido interno\n"


def test_copy_specific_subdirectory(create_fake_package):
    package_name = create_fake_package
    dest = get_package_resource_path(package_name, resource_path="subdir")

    expected = Path(tempfile.gettempdir()) / package_name / "subdir"
    assert dest == expected

    assert dest.is_dir(), "El destino no es un directorio"

    inner = dest / "inner.txt"
    assert inner.exists(), "inner.txt no existe en la copia de subdir"
    assert inner.read_text(encoding="utf-8") == "contenido interno\n"


def test_copy_file(create_fake_package):
    package_name = create_fake_package
    dest = get_package_resource_path(package_name, resource_path="file.txt")

    expected = Path(tempfile.gettempdir()) / package_name / "file.txt"
    assert dest == expected
    assert dest.is_file(), "El destino no es un archivo"

    contenido = dest.read_text(encoding="utf-8")
    assert contenido == "contenido de file.txt\n"


def test_copy_file_with_string_flag(create_fake_package):
    package_name = create_fake_package
    dest_str = get_package_resource_path(
        package_name, resource_path="file.txt", string=True
    )

    assert isinstance(dest_str, str)
    expected_path = Path(tempfile.gettempdir()) / package_name / "file.txt"
    assert Path(dest_str) == expected_path

    assert Path(dest_str).read_text(encoding="utf-8") == "contenido de file.txt\n"


def test_file_copy_nested_subpath(create_fake_package):
    package_name = create_fake_package
    nested = "subdir/inner.txt"
    dest = get_package_resource_path(package_name, resource_path=nested)

    expected = Path(tempfile.gettempdir()) / package_name / "subdir" / "inner.txt"
    assert dest == expected
    assert dest.is_file()
    assert dest.read_text(encoding="utf-8") == "contenido interno\n"


def test_overwrite_existing_destination(create_fake_package):
    package_name = create_fake_package

    dest1 = get_package_resource_path(package_name, resource_path="subdir")
    assert dest1.is_dir()
    assert (dest1 / "inner.txt").exists()

    src_inner = Path(__import__(package_name).__file__).parent / "subdir" / "inner.txt"
    src_inner.write_text("nuevo contenido\n", encoding="utf-8")

    dest2 = get_package_resource_path(package_name, resource_path="subdir")
    assert dest2.is_dir()
    assert (dest2 / "inner.txt").exists()
    assert (dest2 / "inner.txt").read_text(encoding="utf-8") == "nuevo contenido\n"


def test_nonexistent_resource_raises_exception(create_fake_package):
    package_name = create_fake_package
    with pytest.raises(Exception):
        get_package_resource_path(package_name, resource_path="no_existe.txt")


def test_get_key_by_value_found():
    """Test cuando el valor existe en el DynaBox."""
    # Crear un DynaBox con datos de prueba
    test_data = {"key1": "value1", "key2": "value2", "key3": "value3"}
    box = DynaBox(test_data)

    # Probar encontrar una clave existente
    result = get_key_by_value(box, "value2")
    assert result == "key2"


def test_get_key_by_value_not_found():
    """Test cuando el valor no existe en el DynaBox."""
    # Crear un DynaBox con datos de prueba
    test_data = {"key1": "value1", "key2": "value2"}
    box = DynaBox(test_data)

    # Probar buscar un valor que no existe
    result = get_key_by_value(box, "non_existent_value")
    assert result is None


def test_get_key_by_value_empty_box():
    """Test con un DynaBox vacío."""
    # Crear un DynaBox vacío
    box = DynaBox({})

    # Probar buscar en un box vacío
    result = get_key_by_value(box, "any_value")
    assert result is None


def test_get_key_by_value_multiple_matches():
    """Test cuando hay múltiples claves con el mismo valor."""
    # Crear un DynaBox con valores duplicados
    test_data = {"key1": "same_value", "key2": "different_value", "key3": "same_value"}
    box = DynaBox(test_data)

    # Probar encontrar un valor que existe múltiples veces
    # Debería devolver la primera clave encontrada
    result = get_key_by_value(box, "same_value")
    assert result == "key1"  # Debería devolver la primera clave encontrada


def test_get_key_by_value_different_types():
    """Test con valores de diferentes tipos."""
    # Crear un DynaBox con valores de diferentes tipos
    test_data = {
        "str_key": "string_value",
        "int_key": 123,
        "bool_key": True,
        "none_key": None,
    }
    box = DynaBox(test_data)

    # Probar buscar valores de diferentes tipos
    assert get_key_by_value(box, "string_value") == "str_key"
    assert get_key_by_value(box, 123) == "int_key"
    assert get_key_by_value(box, True) == "bool_key"
    assert get_key_by_value(box, None) == "none_key"
