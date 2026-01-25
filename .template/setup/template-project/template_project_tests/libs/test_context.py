import threading

from template_project.libs.context import Context


def test_context_singleton():
    # Limpiar instancia existente
    Context._instance = None

    context1 = Context()
    context2 = Context()

    assert context1 is context2
    assert Context.instance() is context1


def test_context_thread_safety():
    # Limpiar instancia existente
    Context._instance = None

    results = []

    def create_context():
        results.append(Context())

    threads = [threading.Thread(target=create_context) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Todas las instancias deben ser la misma
    assert all(result is results[0] for result in results)


def test_context_initialization():
    # Limpiar instancia existente
    Context._instance = None

    context = Context()
    assert hasattr(context, "_lock")
    assert hasattr(context, "_state")
    assert hasattr(context, "_initialized")
    assert context._initialized is True


def test_context_set_get():
    # Limpiar instancia existente
    Context._instance = None

    Context.set("test_key", "test_value")
    assert Context.get("test_key") == "test_value"
    assert Context.get("nonexistent", "default") == "default"


def test_context_has():
    # Limpiar instancia existente
    Context._instance = None

    Context.set("test_key", "test_value")
    assert Context.has("test_key") is True
    assert Context.has("nonexistent") is False


def test_context_update():
    # Limpiar instancia existente
    Context._instance = None

    Context.update({"key1": "value1", "key2": "value2"})
    assert Context.get("key1") == "value1"
    assert Context.get("key2") == "value2"


def test_context_delete():
    # Limpiar instancia existente
    Context._instance = None

    Context.set("test_key", "test_value")
    assert Context.delete("test_key") is True
    assert Context.has("test_key") is False
    assert Context.delete("nonexistent") is False


def test_context_pop():
    # Limpiar instancia existente
    Context._instance = None

    Context.set("test_key", "test_value")
    value = Context.pop("test_key")
    assert value == "test_value"
    assert Context.has("test_key") is False

    default_value = Context.pop("nonexistent", "default")
    assert default_value == "default"


def test_context_clear():
    # Limpiar instancia existente
    Context._instance = None

    Context.set("key1", "value1")
    Context.set("key2", "value2")
    Context.clear()
    assert Context.has("key1") is False
    assert Context.has("key2") is False


def test_context_snapshot():
    # Limpiar instancia existente
    Context._instance = None

    Context.set("key1", "value1")
    Context.set("key2", "value2")
    snapshot = Context.snapshot()
    assert snapshot == {"key1": "value1", "key2": "value2"}
    assert isinstance(snapshot, dict)
    # Verificar que es una copia, no referencia
    snapshot["key3"] = "value3"
    assert Context.has("key3") is False


def test_context_update_empty_dict():
    # Limpiar instancia existente
    Context._instance = None

    Context.set("existing_key", "existing_value")
    Context.update({})  # No debe modificar nada
    assert Context.get("existing_key") == "existing_value"


# Tests para la funcionalidad de namespaces unificada


def test_context_namespace_detection():
    """Test que verifica la detección automática de namespaces."""
    # Limpiar instancia existente
    Context._instance = None

    # Establecer datos en un namespace
    Context.set("opel/span_id", "12345")
    Context.set("opel/trace_id", "abc-def-ghi")

    # Verificar que se detecta como namespace
    assert Context.has("opel") is True
    assert Context.get("opel") == {"span_id": "12345", "trace_id": "abc-def-ghi"}


def test_context_namespace_nested():
    """Test que verifica namespaces anidados."""
    # Limpiar instancia existente
    Context._instance = None

    # Establecer datos en namespaces anidados
    Context.set("parent/child1/value1", "data1")
    Context.set("parent/child1/value2", "data2")
    Context.set("parent/child2/value1", "data3")
    Context.set("parent/direct_value", "direct_data")

    # Verificar la estructura anidada
    expected = {
        "child1": {"value1": "data1", "value2": "data2"},
        "child2": {"value1": "data3"},
        "direct_value": "direct_data",
    }
    assert Context.get("parent") == expected


def test_context_namespace_mass_assignment():
    """Test que verifica la asignación masiva a namespaces."""
    # Limpiar instancia existente
    Context._instance = None

    # Asignar un diccionario completo a un namespace
    data = {
        "model": "Model S",
        "year": 2023,
        "color": "red",
        "features": {"autopilot": True, "battery": "100kWh"},
    }
    Context.set("tesla", data)

    # Verificar que se asignó correctamente
    assert Context.get("tesla") == data


def test_context_namespace_delete():
    """Test que verifica la eliminación de namespaces completos."""
    # Limpiar instancia existente
    Context._instance = None

    # Establecer datos en un namespace
    Context.set("opel/span_id", "12345")
    Context.set("opel/trace_id", "abc-def-ghi")
    Context.set("opel/user_id", "user_123")

    # Verificar que existe
    assert Context.has("opel") is True

    # Eliminar el namespace completo
    result = Context.delete("opel")
    assert result is True

    # Verificar que se eliminó
    assert Context.has("opel") is False
    assert Context.get("opel") is None


def test_context_namespace_pop():
    """Test que verifica la extracción y eliminación de namespaces."""
    # Limpiar instancia existente
    Context._instance = None

    # Establecer datos en un namespace
    Context.set("opel/span_id", "12345")
    Context.set("opel/trace_id", "abc-def-ghi")

    # Extraer y eliminar el namespace
    data = Context.pop("opel")
    expected = {"span_id": "12345", "trace_id": "abc-def-ghi"}
    assert data == expected

    # Verificar que se eliminó
    assert Context.has("opel") is False


def test_context_namespace_mixed_keys():
    """Test que verifica la coexistencia de claves simples y namespaces."""
    # Limpiar instancia existente
    Context._instance = None

    # Establecer claves simples
    Context.set("global_config", "production")
    Context.set("debug_mode", True)

    # Establecer namespaces
    Context.set("opel/span_id", "12345")
    Context.set("bmw/span_id", "67890")

    # Verificar que todas coexisten
    assert Context.get("global_config") == "production"
    assert Context.get("debug_mode") is True
    assert Context.get("opel") == {"span_id": "12345"}
    assert Context.get("bmw") == {"span_id": "67890"}


def test_context_namespace_deeply_nested():
    """Test que verifica namespaces muy anidados."""
    # Limpiar instancia existente
    Context._instance = None

    # Establecer datos muy anidados
    Context.set("level1/level2/level3/level4/value", "deep_value")
    Context.set("level1/level2/level3/level4/another", "another_deep_value")
    Context.set("level1/level2/level3/direct", "direct_value")
    Context.set("level1/level2/direct", "level2_direct")

    # Verificar la estructura
    result = Context.get("level1")
    expected = {
        "level2": {
            "level3/level4/value": "deep_value",
            "level3/level4/another": "another_deep_value",
            "level3/direct": "direct_value",
            "direct": "level2_direct",
        }
    }
    assert result == expected


def test_context_namespace_nonexistent():
    """Test que verifica el comportamiento con namespaces inexistentes."""
    # Limpiar instancia existente
    Context._instance = None

    # Verificar namespace inexistente
    assert Context.has("inexistente") is False
    assert Context.get("inexistente") is None
    assert Context.get("inexistente", "default") == "default"
    assert Context.delete("inexistente") is False
    assert Context.pop("inexistente", "default") == "default"


def test_context_namespace_thread_safety():
    """Test que verifica la seguridad de hilos con namespaces."""
    # Limpiar instancia existente
    Context._instance = None

    results = []

    def set_namespace_data(thread_id):
        namespace = f"thread_{thread_id}"
        Context.set(f"{namespace}/data1", f"value1_{thread_id}")
        Context.set(f"{namespace}/data2", f"value2_{thread_id}")
        results.append(Context.get(namespace))

    threads = [threading.Thread(target=set_namespace_data, args=(i,)) for i in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Verificar que todos los namespaces se crearon correctamente
    assert len(results) == 5
    for i, result in enumerate(results):
        expected = {"data1": f"value1_{i}", "data2": f"value2_{i}"}
        assert result == expected


def test_context_namespace_snapshot():
    """Test que verifica el snapshot con namespaces."""
    # Limpiar instancia existente
    Context._instance = None

    # Establecer datos mixtos
    Context.set("global_key", "global_value")
    Context.set("opel/span_id", "12345")
    Context.set("bmw/span_id", "67890")

    # Obtener snapshot
    snapshot = Context.snapshot()

    # Verificar que contiene todas las claves
    assert "global_key" in snapshot
    assert "opel/span_id" in snapshot
    assert "bmw/span_id" in snapshot
    assert snapshot["global_key"] == "global_value"
    assert snapshot["opel/span_id"] == "12345"
    assert snapshot["bmw/span_id"] == "67890"


def test_context_namespace_update():
    """Test que verifica la actualización con namespaces."""
    # Limpiar instancia existente
    Context._instance = None

    # Actualizar con datos mixtos
    Context.update(
        {"global_key": "global_value", "opel/span_id": "12345", "bmw/span_id": "67890"}
    )

    # Verificar que se actualizaron correctamente
    assert Context.get("global_key") == "global_value"
    assert Context.get("opel") == {"span_id": "12345"}
    assert Context.get("bmw") == {"span_id": "67890"}


def test_context_namespace_clear():
    """Test que verifica la limpieza con namespaces."""
    # Limpiar instancia existente
    Context._instance = None

    # Establecer datos mixtos
    Context.set("global_key", "global_value")
    Context.set("opel/span_id", "12345")
    Context.set("bmw/span_id", "67890")

    # Limpiar todo
    Context.clear()

    # Verificar que se limpió todo
    assert Context.has("global_key") is False
    assert Context.has("opel") is False
    assert Context.has("bmw") is False
    assert len(Context.snapshot()) == 0
