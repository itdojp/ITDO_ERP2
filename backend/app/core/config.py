from typing import Any

from pydantic import AnyHttpUrl, AnyUrl, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ITDO ERP System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # CORS設定
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # データベース設定
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "itdo_user"
    POSTGRES_PASSWORD: str = "itdo_password"
    POSTGRES_DB: str = "itdo_erp"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: PostgresDsn | AnyUrl | None = None

    @model_validator(mode="after")
    def assemble_db_connection(self) -> "Settings":
        if self.DATABASE_URL is None:
            db_url = (
                f"postgresql://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}:"
                f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
            # Convert string to PostgresDsn type
            self.DATABASE_URL = PostgresDsn(db_url)
        return self

    # Redis設定
    REDIS_URL: str = "redis://localhost:6379"

    # Keycloak設定
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "itdo-erp"
    KEYCLOAK_CLIENT_ID: str = "itdo-erp-client"
    KEYCLOAK_CLIENT_SECRET: str = ""

    # セキュリティ設定
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 8

    # 開発環境フラグ
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings
