"""
Test settings utilities.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TestSettings:
    """Test settings that mimic the real Settings class."""
    
    # Application
    PROJECT_NAME: str = "Test Project"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "test-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 8
    
    # Environment
    DEBUG: bool = True
    ENVIRONMENT: str = "test"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = field(default_factory=list)
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "test"
    POSTGRES_PASSWORD: str = "test"
    POSTGRES_DB: str = "test"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Keycloak
    KEYCLOAK_SERVER_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "test-realm"
    KEYCLOAK_CLIENT_ID: str = "test-client"
    KEYCLOAK_CLIENT_SECRET: str = "test-secret"
    KEYCLOAK_CALLBACK_URL: str = "http://localhost:8000/callback"


def create_test_settings(**overrides: Any) -> TestSettings:
    """
    Create test settings with overrides.
    
    Args:
        **overrides: Values to override defaults
        
    Returns:
        Test settings instance
    """
    return TestSettings(**overrides)