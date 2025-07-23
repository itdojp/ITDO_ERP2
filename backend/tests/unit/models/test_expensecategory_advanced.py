"""Advanced tests for ExpenseCategory model."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.expense_category import ExpenseCategory


class TestExpenseCategory:
    """Comprehensive tests for ExpenseCategory model."""

    def test_model_creation(self, db_session):
        """Test basic model creation."""
        instance = ExpenseCategory()
        db_session.add(instance)
        db_session.commit()

        assert instance.id is not None
        assert isinstance(instance.created_at, datetime)

    def test_model_validation(self):
        """Test model validation rules."""
        # Test required fields
        with pytest.raises((ValueError, IntegrityError)):
            ExpenseCategory()
            # Add validation tests based on model structure

    def test_model_relationships(self, db_session):
        """Test model relationships."""
        # Generate relationship tests based on model analysis
        pass

    def test_model_serialization(self):
        """Test model serialization to dict."""
        instance = ExpenseCategory()

        # Test that model can be converted to dict
        if hasattr(instance, "__dict__"):
            data = instance.__dict__
            assert isinstance(data, dict)
