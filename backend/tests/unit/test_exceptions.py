"""Unit tests for custom exceptions."""

import pytest

from app.core.exceptions import (
    AlreadyExists,
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    ExpiredTokenError,
    InvalidTokenError,
    NotFound,
    PermissionDenied,
    ValidationError,
)


class TestAuthenticationExceptions:
    """Test authentication-related exceptions."""

    def test_authentication_error_basic(self) -> None:
        """Test basic AuthenticationError functionality."""
        # Given: Error message
        message = "Authentication failed"

        # When: Raising AuthenticationError
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError(message)

        # Then: Should capture correct message
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)

    def test_authentication_error_inheritance(self) -> None:
        """Test AuthenticationError inheritance."""
        # When: Creating AuthenticationError
        error = AuthenticationError("test")

        # Then: Should inherit from Exception
        assert isinstance(error, Exception)
        assert isinstance(error, AuthenticationError)

    def test_expired_token_error(self) -> None:
        """Test ExpiredTokenError functionality."""
        # Given: Error message
        message = "Token has expired"

        # When: Raising ExpiredTokenError
        with pytest.raises(ExpiredTokenError) as exc_info:
            raise ExpiredTokenError(message)

        # Then: Should capture correct message and inherit from AuthenticationError
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, AuthenticationError)
        assert isinstance(exc_info.value, ExpiredTokenError)

    def test_invalid_token_error(self) -> None:
        """Test InvalidTokenError functionality."""
        # Given: Error message
        message = "Invalid token format"

        # When: Raising InvalidTokenError
        with pytest.raises(InvalidTokenError) as exc_info:
            raise InvalidTokenError(message)

        # Then: Should capture correct message and inherit from AuthenticationError
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, AuthenticationError)
        assert isinstance(exc_info.value, InvalidTokenError)

    def test_authentication_error_without_message(self) -> None:
        """Test AuthenticationError without message."""
        # When: Raising AuthenticationError without message
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError()

        # Then: Should handle empty message
        assert str(exc_info.value) == ""


class TestAuthorizationExceptions:
    """Test authorization-related exceptions."""

    def test_authorization_error(self) -> None:
        """Test AuthorizationError functionality."""
        # Given: Error message
        message = "Insufficient permissions"

        # When: Raising AuthorizationError
        with pytest.raises(AuthorizationError) as exc_info:
            raise AuthorizationError(message)

        # Then: Should capture correct message
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)

    def test_permission_denied_error(self) -> None:
        """Test PermissionDenied functionality."""
        # Given: Error message
        message = "Access denied to resource"

        # When: Raising PermissionDenied
        with pytest.raises(PermissionDenied) as exc_info:
            raise PermissionDenied(message)

        # Then: Should capture correct message
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)


class TestBusinessLogicExceptions:
    """Test business logic-related exceptions."""

    def test_business_logic_error(self) -> None:
        """Test BusinessLogicError functionality."""
        # Given: Error message
        message = "Business rule violation"

        # When: Raising BusinessLogicError
        with pytest.raises(BusinessLogicError) as exc_info:
            raise BusinessLogicError(message)

        # Then: Should capture correct message
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)

    def test_validation_error(self) -> None:
        """Test ValidationError functionality."""
        # Given: Error message
        message = "Validation failed for field 'email'"

        # When: Raising ValidationError
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(message)

        # Then: Should capture correct message
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)

    def test_not_found_error(self) -> None:
        """Test NotFound functionality."""
        # Given: Error message
        message = "User with ID 123 not found"

        # When: Raising NotFound
        with pytest.raises(NotFound) as exc_info:
            raise NotFound(message)

        # Then: Should capture correct message
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)

    def test_already_exists_error(self) -> None:
        """Test AlreadyExists functionality."""
        # Given: Error message
        message = "User with email already exists"

        # When: Raising AlreadyExists
        with pytest.raises(AlreadyExists) as exc_info:
            raise AlreadyExists(message)

        # Then: Should capture correct message
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)


class TestExceptionEdgeCases:
    """Test edge cases for exceptions."""

    def test_exception_with_complex_message(self) -> None:
        """Test exceptions with complex messages."""
        # Given: Complex error message with unicode and special characters
        message = "Error: ユーザー認証に失敗しました。詳細: {'code': 401, 'detail': 'Invalid token'}"

        # When: Raising exception with complex message
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError(message)

        # Then: Should handle complex message correctly
        assert str(exc_info.value) == message

    def test_exception_with_numeric_data(self) -> None:
        """Test exceptions with numeric data in message."""
        # Given: Error message with numbers
        message = f"Resource ID {12345} not found after {3} attempts"

        # When: Raising exception
        with pytest.raises(NotFound) as exc_info:
            raise NotFound(message)

        # Then: Should handle numeric data
        assert str(exc_info.value) == message

    def test_exception_chaining(self) -> None:
        """Test exception chaining scenarios."""
        # Given: Original exception
        original_error = ValueError("Original error")

        # When: Raising chained exception
        with pytest.raises(BusinessLogicError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise BusinessLogicError(f"Business logic failed: {e}")

        # Then: Should preserve chain information
        assert "Business logic failed: Original error" in str(exc_info.value)

    def test_all_exceptions_inherit_from_exception(self) -> None:
        """Test that all custom exceptions inherit from Exception."""
        # Given: List of all custom exception classes
        exception_classes = [
            AuthenticationError,
            ExpiredTokenError,
            InvalidTokenError,
            AuthorizationError,
            BusinessLogicError,
            NotFound,
            PermissionDenied,
            AlreadyExists,
            ValidationError,
        ]

        # When/Then: All should inherit from Exception
        for exc_class in exception_classes:
            assert issubclass(exc_class, Exception)

    def test_token_error_inheritance_hierarchy(self) -> None:
        """Test token error inheritance hierarchy."""
        # When: Creating token errors
        expired_error = ExpiredTokenError("Expired")
        invalid_error = InvalidTokenError("Invalid")

        # Then: Should maintain proper inheritance
        assert isinstance(expired_error, AuthenticationError)
        assert isinstance(expired_error, Exception)
        assert isinstance(invalid_error, AuthenticationError)
        assert isinstance(invalid_error, Exception)
        
        # But should be distinct types
        assert not isinstance(expired_error, InvalidTokenError)
        assert not isinstance(invalid_error, ExpiredTokenError)


class TestExceptionUsagePatterns:
    """Test common exception usage patterns."""

    def test_exception_with_context_data(self) -> None:
        """Test exceptions with context data."""
        # Given: Context data
        user_id = 123
        resource_type = "document"

        # When: Creating exception with context
        message = f"User {user_id} cannot access {resource_type}"
        
        with pytest.raises(PermissionDenied) as exc_info:
            raise PermissionDenied(message)

        # Then: Should preserve context information
        assert str(user_id) in str(exc_info.value)
        assert resource_type in str(exc_info.value)

    def test_validation_error_with_field_details(self) -> None:
        """Test validation error with field-specific details."""
        # Given: Field validation failure
        field_name = "email"
        field_value = "invalid-email"
        reason = "Invalid email format"

        # When: Creating detailed validation error
        message = f"Validation failed for field '{field_name}' with value '{field_value}': {reason}"
        
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(message)

        # Then: Should include all details
        assert field_name in str(exc_info.value)
        assert field_value in str(exc_info.value)
        assert reason in str(exc_info.value)

    def test_not_found_with_query_details(self) -> None:
        """Test NotFound with query details."""
        # Given: Query details
        resource_type = "User"
        query_field = "email"
        query_value = "nonexistent@example.com"

        # When: Creating detailed not found error
        message = f"{resource_type} with {query_field}='{query_value}' not found"
        
        with pytest.raises(NotFound) as exc_info:
            raise NotFound(message)

        # Then: Should include query details
        assert resource_type in str(exc_info.value)
        assert query_field in str(exc_info.value)
        assert query_value in str(exc_info.value)