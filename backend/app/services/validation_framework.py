"""
CC02 v55.0 Data Validation Framework
Enterprise-grade Data Validation and Integrity Management System
Day 2 of 7-day intensive backend development
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union, get_type_hints
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit_service import AuditService


class ValidationType(str, Enum):
    REQUIRED = "required"
    TYPE_CHECK = "type_check"
    FORMAT = "format"
    RANGE = "range"
    LENGTH = "length"
    PATTERN = "pattern"
    CUSTOM = "custom"
    BUSINESS_RULE = "business_rule"
    UNIQUE = "unique"
    FOREIGN_KEY = "foreign_key"
    CONDITIONAL = "conditional"


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationTrigger(str, Enum):
    ON_CREATE = "on_create"
    ON_UPDATE = "on_update"
    ON_DELETE = "on_delete"
    ON_READ = "on_read"
    ON_DEMAND = "on_demand"


@dataclass
class ValidationContext:
    """Context for validation execution"""

    entity_type: str
    entity_id: Optional[UUID] = None
    data: Dict[str, Any] = field(default_factory=dict)
    original_data: Optional[Dict[str, Any]] = None
    user_id: Optional[UUID] = None
    session: Optional[AsyncSession] = None
    trigger: ValidationTrigger = ValidationTrigger.ON_DEMAND
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResultDetail:
    """Detailed validation result"""

    field_name: str
    validation_type: ValidationType
    severity: ValidationSeverity
    message: str
    rule_id: Optional[UUID] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationSummary:
    """Summary of validation results"""

    entity_type: str
    entity_id: Optional[UUID]
    is_valid: bool
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    results: List[ValidationResultDetail] = field(default_factory=list)
    execution_time_ms: float = 0
    validated_at: datetime = field(default_factory=datetime.utcnow)


class BaseValidator(ABC):
    """Base class for validators"""

    def __init__(
        self, validation_type: ValidationType, config: Dict[str, Any] = None
    ) -> dict:
        self.validation_type = validation_type
        self.config = config or {}

    @abstractmethod
    async def validate(
        self, field_name: str, value: Any, context: ValidationContext
    ) -> List[ValidationResultDetail]:
        """Validate a field value"""
        pass

    def create_result(
        self,
        field_name: str,
        severity: ValidationSeverity,
        message: str,
        actual_value: Any = None,
        expected_value: Any = None,
        suggestion: str = None,
    ) -> ValidationResultDetail:
        """Create a validation result"""
        return ValidationResultDetail(
            field_name=field_name,
            validation_type=self.validation_type,
            severity=severity,
            message=message,
            actual_value=actual_value,
            expected_value=expected_value,
            suggestion=suggestion,
        )


class RequiredValidator(BaseValidator):
    """Required field validator"""

    def __init__(self, config: Dict[str, Any] = None) -> dict:
        super().__init__(ValidationType.REQUIRED, config)

    async def validate(
        self, field_name: str, value: Any, context: ValidationContext
    ) -> List[ValidationResultDetail]:
        """Validate required field"""

        if value is None or (isinstance(value, str) and value.strip() == ""):
            return [
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Field '{field_name}' is required",
                    actual_value=value,
                    suggestion="Please provide a value for this field",
                )
            ]

        return []


class TypeValidator(BaseValidator):
    """Type checking validator"""

    def __init__(self, expected_type: Type, config: Dict[str, Any] = None) -> dict:
        super().__init__(ValidationType.TYPE_CHECK, config)
        self.expected_type = expected_type

    async def validate(
        self, field_name: str, value: Any, context: ValidationContext
    ) -> List[ValidationResultDetail]:
        """Validate field type"""

        if value is None:
            return []

        # Special handling for common types
        if self.expected_type == int:
            try:
                int(value)
                return []
            except (ValueError, TypeError):
                pass
        elif self.expected_type == float:
            try:
                float(value)
                return []
            except (ValueError, TypeError):
                pass
        elif self.expected_type == Decimal:
            try:
                Decimal(str(value))
                return []
            except (InvalidOperation, TypeError):
                pass
        elif self.expected_type == datetime:
            if isinstance(value, datetime):
                return []
            try:
                datetime.fromisoformat(str(value))
                return []
            except ValueError:
                pass
        elif self.expected_type == date:
            if isinstance(value, date):
                return []
            try:
                date.fromisoformat(str(value))
                return []
            except ValueError:
                pass
        elif isinstance(value, self.expected_type):
            return []

        return [
            self.create_result(
                field_name,
                ValidationSeverity.ERROR,
                f"Field '{field_name}' must be of type {self.expected_type.__name__}",
                actual_value=type(value).__name__,
                expected_value=self.expected_type.__name__,
            )
        ]


class FormatValidator(BaseValidator):
    """Format validation (email, phone, etc.)"""

    FORMATS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "phone": r"^\+?1?\d{9,15}$",
        "url": r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$",
        "ip": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
        "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        "credit_card": r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})$",
    }

    def __init__(self, format_type: str, config: Dict[str, Any] = None) -> dict:
        super().__init__(ValidationType.FORMAT, config)
        self.format_type = format_type
        self.pattern = (
            self.FORMATS.get(format_type) or config.get("pattern") if config else None
        )

    async def validate(
        self, field_name: str, value: Any, context: ValidationContext
    ) -> List[ValidationResultDetail]:
        """Validate field format"""

        if value is None or value == "":
            return []

        if not self.pattern:
            return [
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Unknown format type: {self.format_type}",
                )
            ]

        if not re.match(self.pattern, str(value)):
            return [
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Field '{field_name}' has invalid {self.format_type} format",
                    actual_value=str(value),
                    suggestion=f"Please provide a valid {self.format_type}",
                )
            ]

        return []


class RangeValidator(BaseValidator):
    """Range validation for numeric values"""

    def __init__(
        self,
        min_value: Optional[Union[int, float, Decimal]] = None,
        max_value: Optional[Union[int, float, Decimal]] = None,
        config: Dict[str, Any] = None,
    ):
        super().__init__(ValidationType.RANGE, config)
        self.min_value = min_value
        self.max_value = max_value

    async def validate(
        self, field_name: str, value: Any, context: ValidationContext
    ) -> List[ValidationResultDetail]:
        """Validate numeric range"""

        if value is None:
            return []

        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return [
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Field '{field_name}' must be numeric for range validation",
                    actual_value=str(value),
                )
            ]

        results = []

        if self.min_value is not None and numeric_value < float(self.min_value):
            results.append(
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Field '{field_name}' must be at least {self.min_value}",
                    actual_value=numeric_value,
                    expected_value=f">= {self.min_value}",
                )
            )

        if self.max_value is not None and numeric_value > float(self.max_value):
            results.append(
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Field '{field_name}' must be at most {self.max_value}",
                    actual_value=numeric_value,
                    expected_value=f"<= {self.max_value}",
                )
            )

        return results


class LengthValidator(BaseValidator):
    """Length validation for strings and collections"""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        config: Dict[str, Any] = None,
    ):
        super().__init__(ValidationType.LENGTH, config)
        self.min_length = min_length
        self.max_length = max_length

    async def validate(
        self, field_name: str, value: Any, context: ValidationContext
    ) -> List[ValidationResultDetail]:
        """Validate field length"""

        if value is None:
            return []

        try:
            length = len(value)
        except TypeError:
            return [
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Field '{field_name}' does not support length validation",
                    actual_value=str(value),
                )
            ]

        results = []

        if self.min_length is not None and length < self.min_length:
            results.append(
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Field '{field_name}' must be at least {self.min_length} characters long",
                    actual_value=length,
                    expected_value=f">= {self.min_length} characters",
                )
            )

        if self.max_length is not None and length > self.max_length:
            results.append(
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Field '{field_name}' must be at most {self.max_length} characters long",
                    actual_value=length,
                    expected_value=f"<= {self.max_length} characters",
                )
            )

        return results


class PatternValidator(BaseValidator):
    """Pattern validation using regex"""

    def __init__(
        self, pattern: str, flags: int = 0, config: Dict[str, Any] = None
    ) -> dict:
        super().__init__(ValidationType.PATTERN, config)
        self.pattern = pattern
        self.regex = re.compile(pattern, flags)

    async def validate(
        self, field_name: str, value: Any, context: ValidationContext
    ) -> List[ValidationResultDetail]:
        """Validate field pattern"""

        if value is None or value == "":
            return []

        if not self.regex.match(str(value)):
            return [
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Field '{field_name}' does not match the required pattern",
                    actual_value=str(value),
                    expected_value=f"Pattern: {self.pattern}",
                    suggestion="Please check the format requirements",
                )
            ]

        return []


class UniqueValidator(BaseValidator):
    """Unique value validator (database check)"""

    def __init__(
        self, table_name: str, column_name: str = None, config: Dict[str, Any] = None
    ):
        super().__init__(ValidationType.UNIQUE, config)
        self.table_name = table_name
        self.column_name = column_name

    async def validate(
        self, field_name: str, value: Any, context: ValidationContext
    ) -> List[ValidationResultDetail]:
        """Validate field uniqueness"""

        if value is None or not context.session:
            return []

        column_name = self.column_name or field_name

        # Build query to check uniqueness
        query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {column_name} = :value"

        # Exclude current entity if updating
        if context.entity_id:
            query += " AND id != :entity_id"

        try:
            if context.entity_id:
                result = await context.session.execute(
                    text(query), {"value": value, "entity_id": context.entity_id}
                )
            else:
                result = await context.session.execute(text(query), {"value": value})

            count = result.scalar()

            if count > 0:
                return [
                    self.create_result(
                        field_name,
                        ValidationSeverity.ERROR,
                        f"Field '{field_name}' must be unique. Value '{value}' already exists",
                        actual_value=value,
                        suggestion="Please choose a different value",
                    )
                ]

        except Exception as e:
            return [
                self.create_result(
                    field_name,
                    ValidationSeverity.ERROR,
                    f"Unable to validate uniqueness for '{field_name}': {str(e)}",
                )
            ]

        return []


class ConditionalValidator(BaseValidator):
    """Conditional validation based on other fields"""

    def __init__(
        self,
        condition: Dict[str, Any],
        validator: BaseValidator,
        config: Dict[str, Any] = None,
    ):
        super().__init__(ValidationType.CONDITIONAL, config)
        self.condition = condition
        self.validator = validator

    async def validate(
        self, field_name: str, value: Any, context: ValidationContext
    ) -> List[ValidationResultDetail]:
        """Validate field conditionally"""

        # Check if condition is met
        if not self._evaluate_condition(context.data):
            return []

        # Run the conditional validator
        return await self.validator.validate(field_name, value, context)

    def _evaluate_condition(self, data: Dict[str, Any]) -> bool:
        """Evaluate condition"""

        field_name = self.condition.get("field")
        operator = self.condition.get("operator")
        expected_value = self.condition.get("value")

        if not all([field_name, operator]):
            return False

        actual_value = data.get(field_name)

        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "in":
            return (
                actual_value in expected_value
                if isinstance(expected_value, list)
                else False
            )
        elif operator == "not_in":
            return (
                actual_value not in expected_value
                if isinstance(expected_value, list)
                else True
            )
        elif operator == "is_null":
            return actual_value is None
        elif operator == "is_not_null":
            return actual_value is not None

        return False


class ValidationFramework:
    """Enterprise Data Validation Framework"""

    def __init__(self) -> dict:
        self.schemas: Dict[str, Dict[str, List[BaseValidator]]] = {}
        self.global_validators: List[BaseValidator] = []
        self.audit_service = AuditService()

    def register_schema(
        self, entity_type: str, schema: Dict[str, List[BaseValidator]]
    ) -> dict:
        """Register validation schema for an entity type"""
        self.schemas[entity_type] = schema

    def add_field_validator(
        self, entity_type: str, field_name: str, validator: BaseValidator
    ):
        """Add validator for a specific field"""
        if entity_type not in self.schemas:
            self.schemas[entity_type] = {}

        if field_name not in self.schemas[entity_type]:
            self.schemas[entity_type][field_name] = []

        self.schemas[entity_type][field_name].append(validator)

    def add_global_validator(self, validator: BaseValidator) -> dict:
        """Add global validator applied to all entities"""
        self.global_validators.append(validator)

    async def validate(
        self,
        entity_type: str,
        data: Dict[str, Any],
        entity_id: Optional[UUID] = None,
        original_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
        trigger: ValidationTrigger = ValidationTrigger.ON_DEMAND,
    ) -> ValidationSummary:
        """Validate entity data"""

        start_time = datetime.utcnow()

        context = ValidationContext(
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
            original_data=original_data,
            user_id=user_id,
            session=session,
            trigger=trigger,
        )

        results = []

        # Get entity schema
        schema = self.schemas.get(entity_type, {})

        # Validate each field
        for field_name, value in data.items():
            field_validators = schema.get(field_name, [])

            for validator in field_validators:
                field_results = await validator.validate(field_name, value, context)
                results.extend(field_results)

        # Run global validators
        for validator in self.global_validators:
            for field_name, value in data.items():
                field_results = await validator.validate(field_name, value, context)
                results.extend(field_results)

        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Create summary
        summary = ValidationSummary(
            entity_type=entity_type,
            entity_id=entity_id,
            is_valid=not any(r.severity == ValidationSeverity.ERROR for r in results),
            error_count=len(
                [r for r in results if r.severity == ValidationSeverity.ERROR]
            ),
            warning_count=len(
                [r for r in results if r.severity == ValidationSeverity.WARNING]
            ),
            info_count=len(
                [r for r in results if r.severity == ValidationSeverity.INFO]
            ),
            results=results,
            execution_time_ms=execution_time,
        )

        # Log validation result
        await self._log_validation(context, summary)

        return summary

    async def validate_field(
        self,
        entity_type: str,
        field_name: str,
        value: Any,
        context_data: Dict[str, Any] = None,
        entity_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ) -> List[ValidationResultDetail]:
        """Validate a single field"""

        context = ValidationContext(
            entity_type=entity_type,
            entity_id=entity_id,
            data=context_data or {field_name: value},
            session=session,
        )

        results = []
        schema = self.schemas.get(entity_type, {})
        field_validators = schema.get(field_name, [])

        for validator in field_validators:
            field_results = await validator.validate(field_name, value, context)
            results.extend(field_results)

        return results

    async def bulk_validate(
        self, validations: List[Dict[str, Any]], session: Optional[AsyncSession] = None
    ) -> List[ValidationSummary]:
        """Validate multiple entities in bulk"""

        results = []

        for validation_request in validations:
            entity_type = validation_request.get("entity_type")
            data = validation_request.get("data", {})
            entity_id = validation_request.get("entity_id")
            user_id = validation_request.get("user_id")
            trigger = ValidationTrigger(validation_request.get("trigger", "on_demand"))

            if entity_type and data:
                summary = await self.validate(
                    entity_type, data, entity_id, None, user_id, session, trigger
                )
                results.append(summary)

        return results

    def create_schema_from_pydantic(
        self, entity_type: str, model_class: Type[BaseModel]
    ):
        """Create validation schema from Pydantic model"""

        schema = {}
        type_hints = get_type_hints(model_class)

        for field_name, field_info in model_class.__fields__.items():
            validators = []

            # Required validation
            if field_info.required:
                validators.append(RequiredValidator())

            # Type validation
            field_type = type_hints.get(field_name)
            if field_type:
                validators.append(TypeValidator(field_type))

            # Length validation from Field constraints
            if hasattr(field_info, "min_length") and field_info.min_length is not None:
                min_len = field_info.min_length
                max_len = getattr(field_info, "max_length", None)
                validators.append(LengthValidator(min_len, max_len))

            # Range validation from Field constraints
            if hasattr(field_info, "ge") and field_info.ge is not None:
                min_val = field_info.ge
                max_val = getattr(field_info, "le", None)
                validators.append(RangeValidator(min_val, max_val))

            # Pattern validation from Field regex
            if hasattr(field_info, "regex") and field_info.regex:
                validators.append(PatternValidator(field_info.regex.pattern))

            schema[field_name] = validators

        self.register_schema(entity_type, schema)

    async def _log_validation(
        self, context: ValidationContext, summary: ValidationSummary
    ):
        """Log validation results"""

        await self.audit_service.log_event(
            event_type="data_validation",
            entity_type=context.entity_type,
            entity_id=context.entity_id,
            user_id=context.user_id,
            details={
                "is_valid": summary.is_valid,
                "error_count": summary.error_count,
                "warning_count": summary.warning_count,
                "execution_time_ms": summary.execution_time_ms,
                "trigger": context.trigger.value,
                "errors": [
                    {
                        "field": r.field_name,
                        "message": r.message,
                        "severity": r.severity.value,
                    }
                    for r in summary.results
                    if r.severity == ValidationSeverity.ERROR
                ],
            },
        )


# Singleton instance
validation_framework = ValidationFramework()


# Helper functions
async def validate_entity(
    entity_type: str,
    data: Dict[str, Any],
    entity_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
    trigger: ValidationTrigger = ValidationTrigger.ON_DEMAND,
) -> ValidationSummary:
    """Validate entity data"""
    return await validation_framework.validate(
        entity_type, data, entity_id, None, user_id, session, trigger
    )


async def validate_field(
    entity_type: str,
    field_name: str,
    value: Any,
    context_data: Dict[str, Any] = None,
    entity_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
) -> List[ValidationResultDetail]:
    """Validate single field"""
    return await validation_framework.validate_field(
        entity_type, field_name, value, context_data, entity_id, session
    )


def register_validation_schema(
    entity_type: str, schema: Dict[str, List[BaseValidator]]
):
    """Register validation schema"""
    validation_framework.register_schema(entity_type, schema)


def add_field_validator(
    entity_type: str, field_name: str, validator: BaseValidator
) -> dict:
    """Add field validator"""
    validation_framework.add_field_validator(entity_type, field_name, validator)


# Pre-built validation schemas for common entities
def setup_default_schemas() -> None:
    """Setup default validation schemas"""

    # User validation schema
    user_schema = {
        "email": [
            RequiredValidator(),
            FormatValidator("email"),
            UniqueValidator("users", "email"),
        ],
        "username": [
            RequiredValidator(),
            LengthValidator(3, 50),
            PatternValidator(r"^[a-zA-Z0-9_-]+$"),
            UniqueValidator("users", "username"),
        ],
        "password": [
            RequiredValidator(),
            LengthValidator(8, 100),
            PatternValidator(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]"
            ),
        ],
        "phone": [FormatValidator("phone")],
    }

    # Product validation schema
    product_schema = {
        "name": [RequiredValidator(), LengthValidator(1, 200)],
        "sku": [
            RequiredValidator(),
            LengthValidator(1, 100),
            UniqueValidator("products", "sku"),
        ],
        "price": [
            RequiredValidator(),
            TypeValidator(Decimal),
            RangeValidator(Decimal("0"), None),
        ],
        "weight": [TypeValidator(Decimal), RangeValidator(Decimal("0"), None)],
    }

    # Order validation schema
    order_schema = {
        "customer_id": [RequiredValidator(), TypeValidator(UUID)],
        "total_amount": [
            RequiredValidator(),
            TypeValidator(Decimal),
            RangeValidator(Decimal("0"), None),
        ],
        "status": [
            RequiredValidator(),
            PatternValidator(
                r"^(draft|pending|confirmed|processing|shipped|delivered|completed|cancelled)$"
            ),
        ],
    }

    # Customer validation schema
    customer_schema = {
        "email": [FormatValidator("email"), UniqueValidator("customers", "email")],
        "company_name": [LengthValidator(1, 200)],
        "tax_id": [
            ConditionalValidator(
                {"field": "customer_type", "operator": "equals", "value": "business"},
                RequiredValidator(),
            )
        ],
    }

    # Register schemas
    validation_framework.register_schema("user", user_schema)
    validation_framework.register_schema("product", product_schema)
    validation_framework.register_schema("order", order_schema)
    validation_framework.register_schema("customer", customer_schema)


# Initialize default schemas
setup_default_schemas()
