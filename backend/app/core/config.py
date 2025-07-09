from typing import Any, List, Optional, Union
import json

from pydantic import AnyHttpUrl, AnyUrl, PostgresDsn, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ITDO ERP System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # CORS設定 - Field使用でデフォルト値を明示的に設定
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        # デフォルト値
        default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
        
        # None または空の場合
        if v is None:
            return default_origins
            
        if isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped:
                return default_origins

            # JSON配列形式の処理
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [str(origin) for origin in parsed if origin]
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

            # カンマ区切り形式の処理
            origins = [origin.strip() for origin in v_stripped.split(",") if origin.strip()]
            return origins if origins else default_origins

        elif isinstance(v, list):
            return [str(origin) for origin in v if origin]

        # フォールバック
        return default_origins

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
    ENVIRONMENT: str = "development"
    TESTING: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()