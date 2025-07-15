from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    Field,
    PostgresDsn,
    field_validator,
    model_validator,
)
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
    POSTGRES_SERVER: str = Field(default="localhost", description="PostgreSQL server")
    POSTGRES_USER: str = Field(default="itdo_user", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(
        default="itdo_password", description="PostgreSQL password"
    )
    POSTGRES_DB: str = Field(default="itdo_erp", description="PostgreSQL database")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
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
    KEYCLOAK_URL: str = Field(
        default="http://localhost:8080", description="Keycloak URL"
    )
    KEYCLOAK_REALM: str = Field(default="itdo-erp", description="Keycloak realm")
    KEYCLOAK_CLIENT_ID: str = Field(
        default="itdo-erp-client", description="Keycloak client ID"
    )
    KEYCLOAK_CLIENT_SECRET: str = Field(
        default="", description="Keycloak client secret"
    )

    # セキュリティ設定
    SECRET_KEY: str = Field(
        default="test-secret-key-for-development-only",
        description="Secret key for JWT tokens",
    )
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
