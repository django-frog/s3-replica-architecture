from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    APP_ENV: str = "development"
    
    # Infrastructure (MinIO / S3) Settings
    MINIO_ENDPOINT: str       # e.g., "minio:9000" inside Docker network
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str = "secure-vault"
    URL_EXPIRATION: int = 60  # seconds

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()


