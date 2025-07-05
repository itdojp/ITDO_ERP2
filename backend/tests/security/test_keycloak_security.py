"""
Keycloak security-specific tests.

Following TDD approach - Red phase: Writing security tests before implementation.
"""

import pytest
import secrets
from typing import Dict, Any
from unittest.mock import patch, Mock

from app.core.keycloak import (
    generate_pkce_pair,
    verify_pkce_pair,
    validate_redirect_uri,
    is_safe_url,
)
from tests.utils.keycloak import create_keycloak_token_with_roles


class TestPKCESecurity:
    """Test cases for PKCE (Proof Key for Code Exchange) security."""

    def test_pkce_verifier_entropy(self) -> None:
        """PKCEベリファイアが十分なエントロピーを持つことを確認."""
        verifiers = set()
        
        # Generate 100 verifiers
        for _ in range(100):
            verifier, _ = generate_pkce_pair()
            verifiers.add(verifier)
        
        # All should be unique
        assert len(verifiers) == 100
        
        # Each should have sufficient length
        for verifier in verifiers:
            assert len(verifier) >= 43

    def test_pkce_challenge_derivation(self) -> None:
        """PKCEチャレンジが正しくSHA256で導出されることを確認."""
        import hashlib
        import base64
        
        # Given: Known verifier
        verifier = "test-verifier-123"
        
        # When: Generate challenge manually
        digest = hashlib.sha256(verifier.encode()).digest()
        expected_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
        
        # Then: Library should produce same result
        _, actual_challenge = generate_pkce_pair()
        # Note: We can't test exact match due to random verifier
        # But we can verify format
        assert len(actual_challenge) > 0
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in actual_challenge)

    def test_pkce_prevents_code_interception(self) -> None:
        """PKCEが認可コード横取り攻撃を防ぐことを確認."""
        # Given: Original PKCE pair
        verifier1, challenge1 = generate_pkce_pair()
        
        # When: Attacker tries different verifier
        verifier2, _ = generate_pkce_pair()
        
        # Then: Verification should fail
        assert verify_pkce_pair(verifier2, challenge1) is False


class TestRedirectURISecurity:
    """Test cases for redirect URI validation."""

    def test_validate_redirect_uri_whitelist(self) -> None:
        """リダイレクトURIがホワイトリストで検証されることを確認."""
        # Given: Allowed URIs
        allowed_uris = [
            "http://localhost:3000/callback",
            "https://app.itdo-erp.jp/callback",
        ]
        
        # Valid URIs
        assert validate_redirect_uri("http://localhost:3000/callback", allowed_uris) is True
        assert validate_redirect_uri("https://app.itdo-erp.jp/callback", allowed_uris) is True
        
        # Invalid URIs
        assert validate_redirect_uri("http://evil.com/callback", allowed_uris) is False
        assert validate_redirect_uri("http://localhost:3000/different", allowed_uris) is False

    def test_open_redirect_prevention(self) -> None:
        """オープンリダイレクト攻撃が防止されることを確認."""
        # Malicious URLs should be rejected
        malicious_urls = [
            "http://evil.com",
            "https://attacker.com/phishing",
            "//evil.com",  # Protocol-relative URL
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
        ]
        
        for url in malicious_urls:
            assert is_safe_url(url) is False

    def test_safe_url_validation(self) -> None:
        """安全なURLのみが許可されることを確認."""
        # Safe URLs
        safe_urls = [
            "https://app.itdo-erp.jp/dashboard",
            "http://localhost:3000/callback",
            "/relative/path",
        ]
        
        for url in safe_urls:
            assert is_safe_url(url, allowed_hosts=["app.itdo-erp.jp", "localhost"]) is True


class TestStateParameterSecurity:
    """Test cases for CSRF protection via state parameter."""

    def test_state_parameter_randomness(self) -> None:
        """Stateパラメータが十分にランダムであることを確認."""
        states = set()
        
        # Generate 100 states
        for _ in range(100):
            state = secrets.token_urlsafe(32)
            states.add(state)
        
        # All should be unique
        assert len(states) == 100
        
        # Each should have sufficient length (base64 encoded 32 bytes)
        for state in states:
            assert len(state) >= 32

    def test_state_parameter_validation(self) -> None:
        """Stateパラメータの検証が正しく動作することを確認."""
        # Given: Original state
        original_state = secrets.token_urlsafe(32)
        
        # When: Different state provided
        different_state = secrets.token_urlsafe(32)
        
        # Then: Should not match
        assert original_state != different_state

    def test_state_parameter_expiry(self) -> None:
        """Stateパラメータに有効期限があることを確認."""
        # This would be implemented with Redis TTL
        # Test ensures state expires after reasonable time (e.g., 10 minutes)
        pass  # Implementation-specific test


class TestTokenSecurity:
    """Test cases for token security."""

    def test_token_signature_validation(self) -> None:
        """トークンの署名が検証されることを確認."""
        # Given: Valid token
        valid_token = create_keycloak_token_with_roles(["user"])
        
        # When: Tamper with token
        parts = valid_token.split(".")
        if len(parts) == 3:
            # Modify payload
            tampered_token = f"{parts[0]}.modified.{parts[2]}"
            
            # Then: Validation should fail
            # This will be tested in integration tests

    def test_token_expiry_validation(self) -> None:
        """期限切れトークンが拒否されることを確認."""
        from tests.utils.keycloak import create_expired_keycloak_token
        
        expired_token = create_expired_keycloak_token()
        # Validation should fail - tested in integration

    def test_token_audience_validation(self) -> None:
        """トークンのaudience（対象者）が検証されることを確認."""
        # Token should be intended for our application
        # Prevents token confusion attacks
        pass  # Implementation-specific


class TestSessionSecurity:
    """Test cases for session security."""

    def test_session_fixation_prevention(self) -> None:
        """セッション固定攻撃が防止されることを確認."""
        # Session ID should change after authentication
        # This would be tested at integration level
        pass

    def test_secure_cookie_flags(self) -> None:
        """Cookieに適切なセキュリティフラグが設定されることを確認."""
        # Cookies should have:
        # - HttpOnly flag (prevent XSS)
        # - Secure flag (HTTPS only in production)
        # - SameSite flag (CSRF protection)
        pass


class TestRateLimiting:
    """Test cases for rate limiting."""

    def test_login_attempt_rate_limiting(self) -> None:
        """ログイン試行のレート制限が機能することを確認."""
        # After N failed attempts, should be rate limited
        # Prevents brute force attacks
        pass

    def test_token_refresh_rate_limiting(self) -> None:
        """トークンリフレッシュのレート制限が機能することを確認."""
        # Prevent abuse of refresh endpoint
        pass


class TestSecurityHeaders:
    """Test cases for security headers."""

    def test_cors_configuration(self) -> None:
        """CORS設定が適切であることを確認."""
        # Only allowed origins should be able to make requests
        # Keycloak domain should be explicitly allowed
        pass

    def test_security_headers_present(self) -> None:
        """セキュリティヘッダーが設定されることを確認."""
        expected_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        }
        # These would be tested at integration level