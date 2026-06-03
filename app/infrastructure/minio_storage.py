import asyncio
from typing import Dict
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.interfaces.storage import IStorageEngine
from app.core.config import settings

class MinioStorageEngine(IStorageEngine):
    def __init__(self):
        # A single client to rule them all.
        # Inside Docker, vault.local -> 10.5.0.10 (via CoreDNS)
        # On your host laptop, vault.local -> 127.0.0.1 (via /etc/hosts)
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        self.bucket = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                self.s3_client.create_bucket(Bucket=self.bucket)

    async def upload_file(self, file_bytes: bytes, object_key: str, metadata: Dict[str, str]) -> bool:
        try:
            s3_metadata = {k: str(v) for k, v in metadata.items()}
            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.bucket,
                Key=object_key,
                Body=file_bytes,
                Metadata=s3_metadata
            )
            return True
        except ClientError as e:
            print(f"Infrastructure Write Failure: {e}")
            return False

    def generate_download_url(self, object_key: str, expires_in: int) -> str:
        # Sign the URL directly with the unified domain name
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': object_key},
            ExpiresIn=expires_in
        )

    def fetch_metadata(self, object_key: str) -> Dict[str, str]:
        try:
            response = self.s3_client.head_object(Bucket=self.bucket, Key=object_key)
            return response.get('Metadata', {})
        except ClientError:
            return {}

    async def list_files(self, prefix: str) -> list[str]:
        def _list():
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket,
                    Prefix=prefix
                )
                if 'Contents' in response:
                    return [item['Key'] for item in response['Contents']]
                return []
            except ClientError as e:
                print(f"Failed to list objects: {e}")
                return []

        return await asyncio.to_thread(_list)
