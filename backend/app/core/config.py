from typing import Any, List, Optional, Union

from pydantic import AnyHttpUrl, AnyUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ITDO ERP System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # CORS設定
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        # Handle None or empty values gracefully
        if v is None:
            return []

        if isinstance(v, str):
            # Skip empty strings
            if not v.strip():
                return []

            # Handle JSON array format like '["http://localhost:3000"]'
            if v.strip().startswith("[") and v.strip().endswith("]"):
                try:
                    import json

                    parsed = json.loads(v.strip())
                    return parsed if isinstance(parsed, list) else []
                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, treat as comma-separated
                    pass

            # Handle comma-separated format
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v

        # Fallback for any other type
        return []

    # データベース設定
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "itdo_user"
    POSTGRES_PASSWORD: str = "itdo_password"
    POSTGRES_DB: str = "itdo_erp"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[Union[PostgresDsn, AnyUrl]] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str):
            return v
        values = info.data if hasattr(info, "data") else {}
        return (
            f"postgresql://{values.get('POSTGRES_USER', 'itdo_user')}:"
            f"{values.get('POSTGRES_PASSWORD', 'itdo_password')}@"
            f"{values.get('POSTGRES_SERVER', 'localhost')}:"
            f"{values.get('POSTGRES_PORT', 5432)}/"
            f"{values.get('POSTGRES_DB', 'itdo_erp')}"
        )

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

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
