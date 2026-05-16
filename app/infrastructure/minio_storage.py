from typing import Dict
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.interfaces.storage import IStorageEngine
from app.core.config import settings

class MinioStorageEngine(IStorageEngine):
    def __init__(self):
        # 1. Internal Client: For Docker-to-Docker communication (Uploads/Reads)
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )

        # 2. Public Signer Client: STRICTLY for doing the math to generate browser URLs
        self.public_s3_client = boto3.client(
            's3',
            endpoint_url="http://localhost:9000",
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

    def upload_file(self, file_bytes: bytes, object_key: str, metadata: Dict[str, str]) -> bool:
        try:
            s3_metadata = {k: str(v) for k, v in metadata.items()}
            self.s3_client.put_object(
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
        # Generate the URL using the public client so the Host header hash matches exactly!
        return self.public_s3_client.generate_presigned_url(
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
