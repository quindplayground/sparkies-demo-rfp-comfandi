"""Utilities for downloading files and folders from S3."""

import shutil
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from template_project.libs.logging import get_logger


def download_s3_folder_to_local(
    s3_bucket: str, s3_prefix: str, local_dest_path: Path | str
) -> None:
    """Download a complete folder from S3 to a local path.

    Args:
        s3_bucket: Name of the S3 bucket.
        s3_prefix: Prefix of the bucket in S3.
        local_dest_path: Local destination path.
    """
    logger = get_logger(__name__)

    if isinstance(local_dest_path, str):
        local_dest_path = Path(local_dest_path)

    try:
        s3_client = boto3.client("s3")
        if local_dest_path.exists():
            shutil.rmtree(local_dest_path)
        local_dest_path.mkdir(exist_ok=True)
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix)

        files_downloaded = 0
        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    s3_key = obj.get("Key", "")
                    if not s3_key:
                        continue

                    relative_path = s3_key[len(s3_prefix) :].lstrip("/")
                    if not relative_path:
                        continue

                    local_file_path = local_dest_path / relative_path
                    local_file_path.parent.mkdir(parents=True, exist_ok=True)
                    s3_client.download_file(s3_bucket, s3_key, str(local_file_path))
                    files_downloaded += 1

        if files_downloaded > 0:
            logger.info(
                "Downloaded files from s3",
                extra={
                    "attributes": {
                        "files_downloaded": files_downloaded,
                        "s3_bucket": s3_bucket,
                        "s3_prefix": s3_prefix,
                        "local_dest_path": str(local_dest_path),
                    }
                },
            )
        else:
            logger.warning(
                "Files not found in s3",
                extra={
                    "attributes": {
                        "s3_bucket": s3_bucket,
                        "s3_prefix": s3_prefix,
                        "local_dest_path": str(local_dest_path),
                    }
                },
            )
    except ClientError as e:
        logger.error(
            "Error on AWS S3",
            extra={
                "attributes": {
                    "s3_bucket": s3_bucket,
                    "s3_prefix": s3_prefix,
                    "local_dest_path": str(local_dest_path),
                }
            },
            exc_info=e,
        )
        raise e
    except Exception as e:
        logger.error(
            "Error downloading from S3",
            extra={
                "attributes": {
                    "s3_bucket": s3_bucket,
                    "s3_prefix": s3_prefix,
                    "local_dest_path": str(local_dest_path),
                }
            },
            exc_info=e,
        )
        raise e
