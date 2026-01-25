"""Spark resource module for singleton session management."""

import os

from pyspark import SparkConf
from pyspark.sql import SparkSession


class SparkResource:
    """Manages a singleton SparkSession instance with optional Hive support."""

    _instance = None

    def __new__(
        cls,
        conf: SparkConf | None = None,
        new_session: bool = False,
        enable_hive_support: bool = True,
        session_log_level: str | None = None,
    ) -> SparkSession:
        """Creates or retrieves a SparkSession instance.

        Args:
            conf (SparkConf | None, optional): Custom Spark configuration. Defaults to None.
            new_session (bool, optional): Whether to return a new session from the existing one. Defaults to False.
            enable_hive_support (bool, optional): Enables Hive support if True. Defaults to True.
            session_log_level (str, optional): The log level for the SparkSession. Defaults to "INFO".
        Returns:
            SparkSession: The existing or newly created SparkSession instance.
        """
        if not conf:
            conf = SparkConf()

        if cls._instance is None:
            builder = cls._build_builder(enable_hive_support, conf)
            cls._instance = builder.getOrCreate()

        if not session_log_level:
            session_log_level = os.getenv("LOG_LEVEL", "WARN")

        if new_session:
            new_instance = cls._instance.newSession()
            new_instance.sparkContext.setLogLevel(session_log_level)
            return new_instance

        cls._instance.sparkContext.setLogLevel(session_log_level)

        return cls._instance

    @staticmethod
    def _build_builder(
        enable_hive_support: bool, conf: SparkConf
    ) -> SparkSession.Builder:
        """Build a SparkSession.Builder with optional Hive support and configuration.

        Args:
            enable_hive_support: Whether to enable Hive support.
            conf: The Spark configuration to apply.

        Returns:
            A configured SparkSession.Builder.
        """
        builder = SparkSession.builder

        if enable_hive_support:
            builder.enableHiveSupport()  # type: ignore[attr-defined]

        return builder.config(conf=conf)  # type: ignore[attr-defined]
