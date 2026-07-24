from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_ENV: str = "development"

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

    INFRA_KEYCLOAK_ADMIN: str = "admin"
    INFRA_KEYCLOAK_PASSWORD: str = "super_secret_idp_password"

    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        """
        Parses comma-separated strings or JSON arrays into a list of origins.
        Prevents validation errors if .env contains:
        BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(f"Invalid CORS origins value: {v}")

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.KEYCLOAK_FRONTEND_URL}/realms/{self.KEYCLOAK_REALM}"

    # Pydantic v2 modern configuration settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
