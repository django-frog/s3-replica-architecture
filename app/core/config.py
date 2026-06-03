from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    APP_ENV: str = "development"

    # pydantic-settings automatically parses the JSON array from the .env!
    BACKEND_CORS_ORIGINS: list[str] = []

    # Infrastructure (MinIO / S3) Settings
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str = "secure-vault"
    URL_EXPIRATION: int = 60

    # Identity Provider Settings
    KEYCLOAK_URL: str = "http://idp.vault.local:8080"
    KEYCLOAK_REALM: str = "secure-vault-realm"
    KEYCLOAK_CLIENT_ID: str = "vault-client"
    KEYCLOAK_FRONTEND_URL: str = "http://localhost:8080"

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.KEYCLOAK_FRONTEND_URL}/realms/{self.KEYCLOAK_REALM}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
