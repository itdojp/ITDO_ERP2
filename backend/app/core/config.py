from typing import Any, List, Optional, Union
import json

from pydantic import AnyUrl, PostgresDsn, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ITDO ERP System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # CORS設定 - 文字列フィールドとして定義してvalidatorで処理
    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000"
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        """
        CORS origins parser with CI environment compatibility.
        Handles None, empty strings, comma-separated values, and JSON arrays.
        """
        # デフォルト値を常に定義
        default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
        
        # Noneまたは空文字列の場合
        if v is None or v == "":
            return default_origins
            
        # 既にリストの場合はそのまま使用
        if isinstance(v, list):
            if len(v) > 0:
                return [str(origin).strip() for origin in v if origin]
            return default_origins
            
        # 文字列の場合の処理
        if isinstance(v, str):
            v_stripped = v.strip()
            
            # 空文字列チェック
            if not v_stripped:
                return default_origins
            
            # カンマ区切り形式を最初に処理（最も一般的）
            if "," in v_stripped:
                origins = []
                for origin in v_stripped.split(","):
                    cleaned = origin.strip()
                    if cleaned:
                        origins.append(cleaned)
                return origins if origins else default_origins
            
            # 単一のURL（カンマなし）
            return [v_stripped]
        
        # その他の型の場合はデフォルトを返す
        return default_origins

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins as a list for use in middleware."""
        return self.assemble_cors_origins(self.BACKEND_CORS_ORIGINS)

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