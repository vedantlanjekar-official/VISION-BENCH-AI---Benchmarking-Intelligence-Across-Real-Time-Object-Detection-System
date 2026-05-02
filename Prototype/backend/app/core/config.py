from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ann"
    cors_origins: str = "http://localhost:5173"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60 * 24
    jwt_refresh_token_days: int = 14
    redis_url: str = "redis://localhost:6379/0"
    trust_proxy_headers: bool = False
    trusted_proxy_cidrs: str = "127.0.0.1/32,::1/128"
    media_dir: str = "./data/media"
    artifacts_dir: str = "./data/artifacts"
    storage_backend: str = "local"  # local|s3
    s3_bucket: str | None = None
    s3_region: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_endpoint_url: str | None = None  # for MinIO/testing
    model_device: str = "auto"  # auto|cpu|cuda
    yolo_model: str = "yolov8n.pt"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def trusted_proxy_cidr_list(self) -> List[str]:
        return [c.strip() for c in self.trusted_proxy_cidrs.split(",") if c.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

