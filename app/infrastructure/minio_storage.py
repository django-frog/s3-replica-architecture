import asyncio
import logging
from typing import Dict, List
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.interfaces.storage import IStorageEngine

logger = logging.getLogger(__name__)


class MinioStorageEngine(IStorageEngine):
    def __init__(self) -> None:
        # Prevent double 'http://' prefixes if MINIO_ENDPOINT already contains the protocol
        endpoint = settings.MINIO_ENDPOINT
        if not endpoint.startswith(("http://", "https://")):
            endpoint = f"http://{endpoint}"

        # s3={'addressing_style': 'path'} transforms requests from:
        # http://<bucket>.domain/key (Virtual Host-style) -> http://domain/<bucket>/key (Path-style)
        # This completely removes the dependency on CoreDNS / Wildcard TLS certificates in production.
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
            region_name="us-east-1",
        )
        self.bucket = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            # Handle 404 or NoSuchBucket gracefully by creating it on boot
            if error_code in ("404", "NoSuchBucket"):
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket)
                    logger.info("Successfully created S3 bucket: %s", self.bucket)
                except ClientError as create_err:
                    logger.error("Failed to auto-create bucket %s: %s", self.bucket, create_err)
            else:
                logger.error("Error checking bucket %s status: %s", self.bucket, e)

    async def upload_file(
        self, file_bytes: bytes, object_key: str, metadata: Dict[str, str]
    ) -> bool:
        try:
            s3_metadata = {k: str(v) for k, v in metadata.items()}
            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.bucket,
                Key=object_key,
                Body=file_bytes,
                Metadata=s3_metadata,
            )
            return True
        except ClientError as e:
            logger.error("Infrastructure Write Failure for object %s: %s", object_key, e)
            return False

    def generate_download_url(self, object_key: str, expires_in: int) -> str:
        """Generates a presigned URL using path-style bucket routing."""
        try:
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logger.error("Failed to generate presigned URL for %s: %s", object_key, e)
            return ""

    async def fetch_metadata(self, object_key: str) -> Dict[str, str]:
        def _head() -> Dict[str, str]:
            try:
                response = self.s3_client.head_object(
                    Bucket=self.bucket, Key=object_key
                )
                return response.get("Metadata", {})
            except ClientError as e:
                logger.warning("Metadata fetch failed for %s: %s", object_key, e)
                return {}

        # Offload blocking network I/O call to a thread pool
        return await asyncio.to_thread(_head)

    async def list_files(self, prefix: str) -> List[str]:
        def _list() -> List[str]:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket, Prefix=prefix
                )
                if "Contents" in response:
                    return [item["Key"] for item in response["Contents"]]
                return []
            except ClientError as e:
                logger.error("Failed to list objects with prefix %s: %s", prefix, e)
                return []

        # Offload blocking network I/O call to a thread pool
        return await asyncio.to_thread(_list)
