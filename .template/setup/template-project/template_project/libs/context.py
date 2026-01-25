"""Thread-safe singleton context module for application state management."""

import threading
from typing import Any


class Context:
    """Thread-safe singleton class for application state management."""

    _instance: "Context | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "Context":
        """Create or return the singleton instance of the Context class.

        Returns:
            Context: The singleton instance of the Context class.
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the Context instance with thread-safe state management.

        This method ensures the context is only initialized once per instance.
        """
        if getattr(self, "_initialized", False):
            return
        self._lock = threading.RLock()
        self._state: dict[str, Any] = {}
        self._initialized = True

    @classmethod
    def instance(cls) -> "Context":
        """Get the singleton instance of the Context class.

        Returns:
            Context: The singleton instance of the Context class.
        """
        return cls()

    def _set(self, key: str, value: Any) -> None:
        """Set a key-value pair in the context state.

        Args:
            key: The key to store the value under.
            value: The value to store.
        """
        with self._lock:
            if isinstance(value, dict) and "/" in key:
                for sub_key, sub_value in value.items():
                    full_key = f"{key}/{sub_key}"
                    self._state[full_key] = sub_value
            else:
                if self._is_namespace_key(key):
                    self._clear_namespace(key)
                self._state[key] = value

    def _get(self, key: str, default: Any | None = None) -> Any | None:
        """Get a value from the context state by key.

        Args:
            key: The key to retrieve the value for.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if not found.
            If the key represents a namespace, returns a dictionary with all namespace data.
        """
        with self._lock:
            if key in self._state:
                return self._state[key]

            if self._is_namespace_key(key):
                return self._get_namespace_hierarchy(key)

            return default

    def _has(self, key: str) -> bool:
        """Check if a key exists in the context state.

        Args:
            key: The key to check for.

        Returns:
            True if the key exists, False otherwise.
            If the key represents a namespace, returns True if the namespace has any data.
        """
        with self._lock:
            if key in self._state:
                return True

            return self._is_namespace_key(key)

    def _update(self, values: dict[str, Any]) -> None:
        """Update the context state with multiple key-value pairs.

        Args:
            values: Dictionary of key-value pairs to update the state with.
        """
        if not values:
            return
        with self._lock:
            self._state.update(values)

    def _delete(self, key: str) -> bool:
        """Delete a key from the context state.

        Args:
            key: The key to delete.

        Returns:
            True if the key was deleted, False if it didn't exist.
            If the key represents a namespace, deletes all keys in that namespace.
        """
        with self._lock:
            if key in self._state:
                del self._state[key]
                return True

            if self._is_namespace_key(key):
                return self._clear_namespace(key) > 0

            return False

    def _pop(self, key: str, default: Any | None = None) -> Any | None:
        """Remove and return a value from the context state by key.

        Args:
            key: The key to remove and return the value for.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if not found.
            If the key represents a namespace, returns the namespace data and removes all keys.
        """
        with self._lock:
            if key in self._state:
                return self._state.pop(key, default)

            if self._is_namespace_key(key):
                data = self._get_namespace_hierarchy(key)
                self._clear_namespace(key)
                return data

            return default

    def _clear(self) -> None:
        """Clear all key-value pairs from the context state."""
        with self._lock:
            self._state.clear()

    def _snapshot(self) -> dict[str, Any]:
        """Create a snapshot of the current context state.

        Returns:
            A copy of the current state dictionary.
        """
        with self._lock:
            return dict(self._state)

    @staticmethod
    def _parse_key(key: str) -> tuple[str, str | None]:
        """Parse a key to extract namespace and actual key.

        Args:
            key: The key to parse (e.g., "opel/span_id" or "parent/child1/child2").

        Returns:
            A tuple of (namespace, actual_key). If no namespace, namespace is None.
        """
        if "/" in key:
            namespace, actual_key = key.split("/", 1)
            return namespace, actual_key
        return key, None

    def _is_namespace_key(self, key: str) -> bool:
        """Check if a key represents a namespace (has no actual key part).

        Args:
            key: The key to check.

        Returns:
            True if the key represents a namespace, False otherwise.
        """
        with self._lock:
            namespace_prefix = f"{key}/"
            return any(k.startswith(namespace_prefix) for k in self._state)

    def _get_namespace_hierarchy(self, namespace: str) -> dict[str, Any]:
        """Get all data from a namespace, including nested namespaces.

        Args:
            namespace: The namespace to get data for.

        Returns:
            A dictionary with the namespace data, including nested namespaces.
        """
        with self._lock:
            namespace_prefix = f"{namespace}/"
            result: dict[str, Any] = {}

            for key, value in self._state.items():
                if key.startswith(namespace_prefix):
                    remaining_key = key[len(namespace_prefix) :]

                    if "/" in remaining_key:
                        nested_namespace, nested_key = remaining_key.split("/", 1)
                        if nested_namespace not in result:
                            result[nested_namespace] = {}
                        result[nested_namespace][nested_key] = value
                    else:
                        result[remaining_key] = value

            return result

    @staticmethod
    def _get_namespace_key(namespace: str, key: str) -> str:
        """Get the full key for a namespace and key.

        Args:
            namespace: The namespace.
            key: The key within the namespace.

        Returns:
            The full key in the format "namespace/key".
        """
        return f"{namespace}/{key}"

    def _get_namespace_keys(self, namespace: str) -> list[str]:
        """Get all keys that belong to a specific namespace.

        Args:
            namespace: The namespace to get keys for.

        Returns:
            A list of keys that belong to the namespace.
        """
        with self._lock:
            return [key for key in self._state if key.startswith(f"{namespace}/")]

    def _get_namespace_dict(self, namespace: str) -> dict[str, Any]:
        """Get all key-value pairs that belong to a specific namespace.

        Args:
            namespace: The namespace to get data for.

        Returns:
            A dictionary with keys without the namespace prefix and their values.
        """
        with self._lock:
            namespace_prefix = f"{namespace}/"
            return {
                key[len(namespace_prefix) :]: value for key, value in self._state.items() if key.startswith(namespace_prefix)
            }

    def _clear_namespace(self, namespace: str) -> int:
        """Clear all keys that belong to a specific namespace.

        Args:
            namespace: The namespace to clear.

        Returns:
            The number of keys that were removed.
        """
        with self._lock:
            keys_to_remove = self._get_namespace_keys(namespace)
            for key in keys_to_remove:
                del self._state[key]
            return len(keys_to_remove)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set a key-value pair in the context state.

        Args:
            key: The key to store the value under.
            value: The value to store.
        """
        cls.instance()._set(key, value)

    @classmethod
    def get(cls, key: str, default: Any | None = None) -> Any | None:
        """Get a value from the context state by key.

        Args:
            key: The key to retrieve the value for.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if not found.
        """
        return cls.instance()._get(key, default)

    @classmethod
    def has(cls, key: str) -> bool:
        """Check if a key exists in the context state.

        Args:
            key: The key to check for.

        Returns:
            True if the key exists, False otherwise.
        """
        return cls.instance()._has(key)

    @classmethod
    def update(cls, values: dict[str, Any]) -> None:
        """Update the context state with multiple key-value pairs.

        Args:
            values: Dictionary of key-value pairs to update the state with.
        """
        cls.instance()._update(values)

    @classmethod
    def delete(cls, key: str) -> bool:
        """Delete a key from the context state.

        Args:
            key: The key to delete.

        Returns:
            True if the key was deleted, False if it didn't exist.
        """
        return cls.instance()._delete(key)

    @classmethod
    def pop(cls, key: str, default: Any | None = None) -> Any | None:
        """Remove and return a value from the context state by key.

        Args:
            key: The key to remove and return the value for.
            default: The default value to return if the.key is not found.

        Returns:
            The value associated with the key, or the default value if not found.
        """
        return cls.instance()._pop(key, default)

    @classmethod
    def clear(cls) -> None:
        """Clear all key-value pairs from the context state."""
        cls.instance()._clear()

    @classmethod
    def snapshot(cls) -> dict[str, Any]:
        """Create a snapshot of the current context state.

        Returns:
            A copy of the current state dictionary.
        """
        return cls.instance()._snapshot()

    @classmethod
    def get_namespace(cls, namespace: str) -> dict[str, Any]:
        """Get all key-value pairs that belong to a specific namespace.

        Args:
            namespace: The namespace to get data for.

        Returns:
            A dictionary with keys without the namespace prefix and their values.
        """
        return cls.instance()._get_namespace_dict(namespace)

    @classmethod
    def get_namespace_keys(cls, namespace: str) -> list[str]:
        """Get all keys that belong to a specific namespace.

        Args:
            namespace: The namespace to get keys for.

        Returns:
            A list of keys that belong to the namespace.
        """
        return cls.instance()._get_namespace_keys(namespace)

    @classmethod
    def clear_namespace(cls, namespace: str) -> int:
        """Clear all keys that belong to a specific namespace.

        Args:
            namespace: The namespace to clear.

        Returns:
            The number of keys that were removed.
        """
        return cls.instance()._clear_namespace(namespace)

    @classmethod
    def set_namespace(cls, namespace: str, key: str, value: Any) -> None:
        """Set a key-value pair within a specific namespace.

        Args:
            namespace: The namespace to set the key in.
            key: The key within the namespace.
            value: The value to store.
        """
        full_key = cls._get_namespace_key(namespace, key)
        cls.set(full_key, value)

    @classmethod
    def get_namespace_key(cls, namespace: str, key: str, default: Any | None = None) -> Any | None:
        """Get a value from a specific namespace and key.

        Args:
            namespace: The namespace to get the key from.
            key: The key within the namespace.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if not found.
        """
        full_key = cls._get_namespace_key(namespace, key)
        return cls.get(full_key, default)

    @classmethod
    def has_namespace_key(cls, namespace: str, key: str) -> bool:
        """Check if a key exists within a specific namespace.

        Args:
            namespace: The namespace to check in.
            key: The key within the namespace.

        Returns:
            True if the key exists, False otherwise.
        """
        full_key = cls._get_namespace_key(namespace, key)
        return cls.has(full_key)

    @classmethod
    def delete_namespace_key(cls, namespace: str, key: str) -> bool:
        """Delete a key from a specific namespace.

        Args:
            namespace: The namespace to delete the key from.
            key: The key within the namespace.

        Returns:
            True if the key was deleted, False if it didn't exist.
        """
        full_key = cls._get_namespace_key(namespace, key)
        return cls.delete(full_key)

    @classmethod
    def pop_namespace_key(cls, namespace: str, key: str, default: Any | None = None) -> Any | None:
        """Remove and return a value from a specific namespace and key.

        Args:
            namespace: The namespace to pop the key from.
            key: The key within the namespace.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if not found.
        """
        full_key = cls._get_namespace_key(namespace, key)
        return cls.pop(full_key, default)
