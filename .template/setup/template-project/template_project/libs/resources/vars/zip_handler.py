"""ZIP file handler module."""

import inspect
import os
import tempfile
import zipfile
from pathlib import Path

from pyspark import SparkFiles
from pyspark.sql import SparkSession

from template_project.libs.resources.spark_resource import SparkResource


class ZipHandler:
    """Handles ZIP file extraction and path resolution for Spark clusters."""

    _extracted_paths = {}

    def __init__(self, spark: SparkSession):
        """Initialize the ZipHandler with a SparkSession.

        Args:
            spark: An active Spark session.
        """
        self.spark = spark

    def _extract_zip(self, zip_path: str) -> str:
        """Extract the ZIP file to a temporary directory if not previously extracted.

        Args:
            zip_path: Path to the ZIP file.

        Returns:
            Path to the extracted content.

        Raises:
            FileNotFoundError: If the ZIP file doesn't exist.
        """
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"No such file or directory: '{zip_path}'")

        if zip_path in self._extracted_paths:
            temp_dir = self._extracted_paths[zip_path]
        else:
            temp_dir = tempfile.mkdtemp()

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                try:
                    zip_ref.extractall(temp_dir)
                except FileExistsError:
                    pass

            self._extracted_paths[zip_path] = temp_dir

        return temp_dir

    @staticmethod
    def _locate_file_in_spark(file_name: str) -> str:
        """Locate a file within the Spark context or local directory.

        Args:
            file_name: Name of the file to locate.

        Returns:
            Path to the located file.

        Raises:
            FileNotFoundError: If the file is not found.
        """
        spark_file_path = SparkFiles.get(file_name)
        if os.path.exists(spark_file_path):
            return spark_file_path

        current_working_directory_path = os.path.join(os.getcwd(), file_name)

        if os.path.exists(current_working_directory_path):
            return current_working_directory_path

        raise FileNotFoundError(
            f"The file {file_name} is not found in either SparkFiles or the current working directory."
        )

    def get_working_path(
        self, path: str | object | Path, in_spark_cluster: bool
    ) -> str:
        """Resolve the working path, handling potential ZIP extraction.

        Args:
            path: Input path or module reference.
            in_spark_cluster: Whether the environment is a Spark cluster.

        Returns:
            Resolved working path.

        Raises:
            FileNotFoundError: If the path doesn't exist.
        """
        if inspect.ismodule(path):
            tmp_path = path.__path__[0]
        else:
            tmp_path = str(path)

        if in_spark_cluster:
            tmp_path = self._locate_file_in_spark(tmp_path)

        path_parts = tmp_path.split("/")

        for i in range(len(path_parts)):
            partial_path = "/".join(path_parts[: i + 1])
            if zipfile.is_zipfile(partial_path):
                if not os.path.exists(partial_path):
                    raise FileNotFoundError(
                        f"No such file or directory: '{partial_path}'"
                    )

                remaining_path = "/".join(path_parts[i + 1 :])
                extracted_dir = self._extract_zip(partial_path)
                full_extracted_path = (
                    os.path.join(extracted_dir, remaining_path)
                    if remaining_path
                    else extracted_dir
                )
                return full_extracted_path

        return tmp_path


def get_working_path(path: str | object | Path, in_spark_cluster: bool = False) -> str:
    """Public function to resolve working paths with optional ZIP extraction in Spark clusters.

    Args:
        path: Input path or module reference.
        in_spark_cluster: Whether the environment is a Spark cluster. Defaults to False.

    Returns:
        Resolved and accessible path.
    """
    spark = SparkResource(new_session=True)
    zip_handler = ZipHandler(spark)
    return zip_handler.get_working_path(path, in_spark_cluster)
