import pytest
from unittest.mock import Mock, patch

from demo_comfandi_project.libs.aws.s3.download_utils import download_s3_folder_to_local


def test_download_s3_folder_to_local_success():
    with patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.boto3.client"
    ) as mock_boto3, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.shutil.rmtree"
    ) as _mock_rmtree, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.Path"
    ) as mock_path, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.get_logger"
    ) as mock_get_logger:

        mock_s3_client = Mock()
        mock_boto3.return_value = mock_s3_client

        mock_paginator = Mock()
        mock_s3_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "Contents": [
                {"Key": "test-prefix/file1.txt"},
                {"Key": "test-prefix/subdir/file2.txt"},
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        mock_dest_path = Mock()
        mock_dest_path.exists.return_value = True
        mock_dest_path.mkdir = Mock()
        mock_dest_path.__truediv__ = Mock(return_value=mock_dest_path)
        mock_dest_path.parent = Mock()
        mock_dest_path.parent.mkdir = Mock()
        mock_path.return_value = mock_dest_path

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        download_s3_folder_to_local("test-bucket", "test-prefix", "/local/path")

        mock_s3_client.download_file.assert_called()
        mock_logger.info.assert_called()


def test_download_s3_folder_to_local_no_files():
    with patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.boto3.client"
    ) as mock_boto3, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.shutil.rmtree"
    ) as _mock_rmtree, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.Path"
    ) as mock_path, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.get_logger"
    ) as mock_get_logger:

        mock_s3_client = Mock()
        mock_boto3.return_value = mock_s3_client

        mock_paginator = Mock()
        mock_s3_client.get_paginator.return_value = mock_paginator

        mock_page = {}  # Sin Contents
        mock_paginator.paginate.return_value = [mock_page]

        mock_dest_path = Mock()
        mock_dest_path.exists.return_value = False
        mock_dest_path.mkdir = Mock()
        mock_path.return_value = mock_dest_path

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        download_s3_folder_to_local("test-bucket", "test-prefix", "/local/path")

        mock_logger.warning.assert_called()


def test_download_s3_folder_to_local_client_error():
    with patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.boto3.client"
    ) as mock_boto3, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.shutil.rmtree"
    ) as _mock_rmtree, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.Path"
    ) as mock_path, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.get_logger"
    ) as mock_get_logger:

        from botocore.exceptions import ClientError

        mock_s3_client = Mock()
        mock_s3_client.get_paginator.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
            "ListObjectsV2",
        )
        mock_boto3.return_value = mock_s3_client

        mock_dest_path = Mock()
        mock_dest_path.exists.return_value = False
        mock_dest_path.mkdir = Mock()
        mock_path.return_value = mock_dest_path

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with pytest.raises(ClientError):
            download_s3_folder_to_local("test-bucket", "test-prefix", "/local/path")

        mock_logger.error.assert_called()


def test_download_s3_folder_to_local_string_path():
    with patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.boto3.client"
    ) as mock_boto3, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.shutil.rmtree"
    ) as _mock_rmtree, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.Path"
    ) as mock_path, patch(
        "demo_comfandi_project.libs.aws.s3.download_utils.get_logger"
    ) as _mock_get_logger:

        mock_s3_client = Mock()
        mock_boto3.return_value = mock_s3_client

        mock_paginator = Mock()
        mock_s3_client.get_paginator.return_value = mock_paginator

        mock_page = {"Contents": []}
        mock_paginator.paginate.return_value = [mock_page]

        mock_dest_path = Mock()
        mock_dest_path.exists.return_value = False
        mock_dest_path.mkdir = Mock()
        mock_path.return_value = mock_dest_path

        # Pasar string en lugar de Path
        download_s3_folder_to_local("test-bucket", "test-prefix", "/local/path")

        mock_path.assert_called_once_with("/local/path")
