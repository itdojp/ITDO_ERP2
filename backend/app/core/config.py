import json
from typing import Any, List, Optional, Union

from pydantic import AnyUrl, Field, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ITDO ERP System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # CORS設定
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        """Parse CORS origins from string or list."""
        if v is None:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]

        if isinstance(v, list):
            return v

        # Handle string values
        v_stripped = v.strip()
        if not v_stripped:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]

        # Try comma-separated first
        if "," in v_stripped:
            return [origin.strip() for origin in v_stripped.split(",") if origin.strip()]

        # Try JSON parsing
        try:
            import json
            parsed = json.loads(v_stripped)
            if isinstance(parsed, list):
                return parsed
        except:
            pass

        # Single value
        return [v_stripped]

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins as a list for use in middleware."""
        # Since BACKEND_CORS_ORIGINS is now validated as a list, return it directly
        return self.BACKEND_CORS_ORIGINS

    # データベース設定
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "itdo_user"
    POSTGRES_PASSWORD: str = "itdo_password"
    POSTGRES_DB: str = "itdo_erp"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[Union[PostgresDsn, AnyUrl]] = None

    # Test environment overrides
    @property
    def postgres_db_name(self) -> str:
        """Get the correct database name based on environment."""
        if self.ENVIRONMENT in ("test", "testing") or self.TESTING:
            return "itdo_erp_test"
        return self.POSTGRES_DB

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        values = info.data if hasattr(info, "data") else {}
        # Use test database for test environment
        env = values.get("ENVIRONMENT", "development")
        is_test_env = env in ("test", "testing") or values.get("TESTING")
        db_name = "itdo_erp_test" if is_test_env else "itdo_erp"
        return (
            f"postgresql://{values.get('POSTGRES_USER', 'itdo_user')}:"
            f"{values.get('POSTGRES_PASSWORD', 'itdo_password')}@"
            f"{values.get('POSTGRES_SERVER', 'localhost')}:"
            f"{values.get('POSTGRES_PORT', 5432)}/"
            f"{db_name}"
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
