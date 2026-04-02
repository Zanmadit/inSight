from typing import Self
from urllib.parse import quote_plus, urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    # When POSTGRES_HOST is set (Docker), database_url is assembled from parts (ignores stale DATABASE_URL).
    database_url: str = ""
    postgres_host: str = ""

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @model_validator(mode="after")
    def assemble_database_url(self) -> Self:
        # Only assemble if database_url is not already set.
        if not self.database_url:
            host = self.postgres_host or "localhost"
            u = quote_plus(self.POSTGRES_USER)
            p = quote_plus(self.POSTGRES_PASSWORD)
            db = self.POSTGRES_DB
            url = f"postgresql+asyncpg://{u}:{p}@{host}:5432/{db}"
            object.__setattr__(self, "database_url", url)
        return self

    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_ENDPOINT: str
    MINIO_BUCKET: str
    MINIO_PUBLIC_URL: str

    OPENAI_API_KEY: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_EXPIRE_HOURS: int

    BACKEND_CORS_ORIGINS: str

    @property
    def cors_origins_list(self) -> list[str]:
        return [x.strip() for x in self.BACKEND_CORS_ORIGINS.split(",") if x.strip()]

    @property
    def minio_public_endpoint_secure(self) -> tuple[str, bool]:
        parsed = urlparse(self.MINIO_PUBLIC_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port
        if port:
            endpoint = f"{host}:{port}"
        else:
            endpoint = host
        secure = parsed.scheme == "https"
        return endpoint, secure


settings = Settings()