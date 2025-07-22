"""
Common filtering utilities for ERP API
"""

from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from sqlalchemy.orm import Query
from sqlalchemy import and_, or_, func, text
from sqlalchemy.sql import operators
from pydantic import BaseModel


class FilterOperator(str, Enum):
    """Available filter operators"""
    EQ = "eq"           # Equal
    NE = "ne"           # Not equal
    GT = "gt"           # Greater than
    GTE = "gte"         # Greater than or equal
    LT = "lt"           # Less than
    LTE = "lte"         # Less than or equal
    IN = "in"           # In list
    NOT_IN = "not_in"   # Not in list
    LIKE = "like"       # SQL LIKE
    ILIKE = "ilike"     # Case-insensitive LIKE
    IS_NULL = "is_null" # IS NULL
    IS_NOT_NULL = "is_not_null"  # IS NOT NULL
    CONTAINS = "contains"        # For array/JSON contains
    BETWEEN = "between"          # Between two values


class FilterField(BaseModel):
    """Single filter field definition"""
    field: str
    operator: FilterOperator
    value: Any
    case_sensitive: bool = True


class FilterGroup(BaseModel):
    """Group of filters with AND/OR logic"""
    filters: List[Union[FilterField, "FilterGroup"]]
    logic: str = "and"  # "and" or "or"


# Fix forward reference
FilterGroup.model_rebuild()


class BaseFilter:
    """Base filter class for common filtering operations"""
    
    def __init__(self, model_class: Type):
        self.model_class = model_class
    
    def apply_filters(
        self,
        query: Query,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        date_filters: Optional[Dict[str, Any]] = None
    ) -> Query:
        """
        Apply common filters to a query
        
        Args:
            query: SQLAlchemy query
            filters: Dictionary of field filters
            search: Search term for text fields
            search_fields: Fields to search in
            date_filters: Date range filters
            
        Returns:
            Filtered query
        """
        # Apply field filters
        if filters:
            for field, value in filters.items():
                if value is not None:
                    query = self._apply_field_filter(query, field, value)
        
        # Apply search filters
        if search and search_fields:
            query = self._apply_search_filter(query, search, search_fields)
        
        # Apply date filters
        if date_filters:
            query = self._apply_date_filters(query, date_filters)
        
        return query
    
    def _apply_field_filter(self, query: Query, field: str, value: Any) -> Query:
        """Apply filter for a single field"""
        if not hasattr(self.model_class, field):
            return query
        
        column = getattr(self.model_class, field)
        
        # Handle different filter types
        if isinstance(value, dict) and "operator" in value:
            return self._apply_operator_filter(query, column, value)
        elif isinstance(value, list):
            return query.filter(column.in_(value))
        elif value is None:
            return query.filter(column.is_(None))
        else:
            return query.filter(column == value)
    
    def _apply_operator_filter(self, query: Query, column: Any, filter_config: Dict) -> Query:
        """Apply operator-based filter"""
        operator = FilterOperator(filter_config["operator"])
        value = filter_config["value"]
        
        if operator == FilterOperator.EQ:
            return query.filter(column == value)
        elif operator == FilterOperator.NE:
            return query.filter(column != value)
        elif operator == FilterOperator.GT:
            return query.filter(column > value)
        elif operator == FilterOperator.GTE:
            return query.filter(column >= value)
        elif operator == FilterOperator.LT:
            return query.filter(column < value)
        elif operator == FilterOperator.LTE:
            return query.filter(column <= value)
        elif operator == FilterOperator.IN:
            return query.filter(column.in_(value))
        elif operator == FilterOperator.NOT_IN:
            return query.filter(~column.in_(value))
        elif operator == FilterOperator.LIKE:
            return query.filter(column.like(f"%{value}%"))
        elif operator == FilterOperator.ILIKE:
            return query.filter(column.ilike(f"%{value}%"))
        elif operator == FilterOperator.IS_NULL:
            return query.filter(column.is_(None))
        elif operator == FilterOperator.IS_NOT_NULL:
            return query.filter(column.is_not(None))
        elif operator == FilterOperator.BETWEEN:
            if isinstance(value, list) and len(value) == 2:
                return query.filter(column.between(value[0], value[1]))
        
        return query
    
    def _apply_search_filter(self, query: Query, search: str, search_fields: List[str]) -> Query:
        """Apply search filter across multiple fields"""
        if not search.strip():
            return query
        
        search_term = f"%{search.strip()}%"
        search_conditions = []
        
        for field in search_fields:
            if hasattr(self.model_class, field):
                column = getattr(self.model_class, field)
                search_conditions.append(column.ilike(search_term))
        
        if search_conditions:
            return query.filter(or_(*search_conditions))
        
        return query
    
    def _apply_date_filters(self, query: Query, date_filters: Dict[str, Any]) -> Query:
        """Apply date range filters"""
        for field, date_config in date_filters.items():
            if not hasattr(self.model_class, field):
                continue
            
            column = getattr(self.model_class, field)
            
            if isinstance(date_config, dict):
                if "from" in date_config and date_config["from"]:
                    query = query.filter(column >= date_config["from"])
                if "to" in date_config and date_config["to"]:
                    query = query.filter(column <= date_config["to"])
            elif isinstance(date_config, (date, datetime)):
                query = query.filter(func.date(column) == date_config)
        
        return query


class AdvancedFilter(BaseFilter):
    """Advanced filtering with complex logic support"""
    
    def apply_advanced_filters(self, query: Query, filter_groups: List[FilterGroup]) -> Query:
        """Apply advanced filter groups with complex logic"""
        for group in filter_groups:
            query = self._apply_filter_group(query, group)
        return query
    
    def _apply_filter_group(self, query: Query, group: FilterGroup) -> Query:
        """Apply a single filter group"""
        if not group.filters:
            return query
        
        conditions = []
        for filter_item in group.filters:
            if isinstance(filter_item, FilterField):
                condition = self._create_filter_condition(filter_item)
                if condition is not None:
                    conditions.append(condition)
            elif isinstance(filter_item, FilterGroup):
                # Recursive handling of nested groups
                subquery_conditions = []
                for subfilter in filter_item.filters:
                    if isinstance(subfilter, FilterField):
                        condition = self._create_filter_condition(subfilter)
                        if condition is not None:
                            subquery_conditions.append(condition)
                
                if subquery_conditions:
                    if filter_item.logic.lower() == "or":
                        conditions.append(or_(*subquery_conditions))
                    else:
                        conditions.append(and_(*subquery_conditions))
        
        if conditions:
            if group.logic.lower() == "or":
                return query.filter(or_(*conditions))
            else:
                return query.filter(and_(*conditions))
        
        return query
    
    def _create_filter_condition(self, filter_field: FilterField):
        """Create a filter condition from FilterField"""
        if not hasattr(self.model_class, filter_field.field):
            return None
        
        column = getattr(self.model_class, filter_field.field)
        operator = filter_field.operator
        value = filter_field.value
        
        if operator == FilterOperator.EQ:
            return column == value
        elif operator == FilterOperator.NE:
            return column != value
        elif operator == FilterOperator.GT:
            return column > value
        elif operator == FilterOperator.GTE:
            return column >= value
        elif operator == FilterOperator.LT:
            return column < value
        elif operator == FilterOperator.LTE:
            return column <= value
        elif operator == FilterOperator.IN:
            return column.in_(value)
        elif operator == FilterOperator.NOT_IN:
            return ~column.in_(value)
        elif operator == FilterOperator.LIKE:
            if filter_field.case_sensitive:
                return column.like(f"%{value}%")
            else:
                return column.ilike(f"%{value}%")
        elif operator == FilterOperator.ILIKE:
            return column.ilike(f"%{value}%")
        elif operator == FilterOperator.IS_NULL:
            return column.is_(None)
        elif operator == FilterOperator.IS_NOT_NULL:
            return column.is_not(None)
        elif operator == FilterOperator.BETWEEN:
            if isinstance(value, list) and len(value) == 2:
                return column.between(value[0], value[1])
        
        return None


class SortConfig(BaseModel):
    """Sorting configuration"""
    field: str
    direction: str = "asc"  # "asc" or "desc"
    
    def validate_direction(self):
        if self.direction.lower() not in ["asc", "desc"]:
            self.direction = "asc"


def apply_sorting(
    query: Query,
    model_class: Type,
    sorts: List[Union[SortConfig, Dict[str, str]]]
) -> Query:
    """
    Apply sorting to a query
    
    Args:
        query: SQLAlchemy query
        model_class: Model class
        sorts: List of sort configurations
        
    Returns:
        Sorted query
    """
    for sort_config in sorts:
        if isinstance(sort_config, dict):
            sort_config = SortConfig(**sort_config)
        
        if hasattr(model_class, sort_config.field):
            column = getattr(model_class, sort_config.field)
            if sort_config.direction.lower() == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
    
    return query


def create_filter_from_query_params(
    params: Dict[str, Any],
    allowed_fields: List[str]
) -> Dict[str, Any]:
    """
    Create filter dictionary from query parameters
    
    Args:
        params: Query parameters
        allowed_fields: List of allowed filter fields
        
    Returns:
        Filter dictionary
    """
    filters = {}
    
    for key, value in params.items():
        # Skip None values and pagination params
        if value is None or key in ["page", "size", "limit", "offset", "sort", "search"]:
            continue
        
        # Check if field is allowed
        base_field = key.split("__")[0]  # Handle operator suffix like "field__gt"
        if base_field in allowed_fields:
            # Handle operator syntax (field__operator)
            if "__" in key:
                field, operator = key.split("__", 1)
                filters[field] = {
                    "operator": operator,
                    "value": value
                }
            else:
                filters[key] = value
    
    return filters


class ERPBaseFilter(BaseFilter):
    """ERP-specific base filter with common patterns"""
    
    def apply_erp_filters(
        self,
        query: Query,
        organization_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_deleted: bool = False,
        **kwargs
    ) -> Query:
        """Apply common ERP filters"""
        
        # Organization filter
        if organization_id is not None and hasattr(self.model_class, "organization_id"):
            query = query.filter(self.model_class.organization_id == organization_id)
        
        # Active status filter
        if is_active is not None and hasattr(self.model_class, "is_active"):
            query = query.filter(self.model_class.is_active == is_active)
        
        # Soft delete filter
        if not is_deleted and hasattr(self.model_class, "deleted_at"):
            query = query.filter(self.model_class.deleted_at.is_(None))
        
        # Apply other filters
        return self.apply_filters(query, kwargs)


# Predefined filter sets for common use cases
COMMON_SEARCH_FIELDS = {
    "user": ["full_name", "email", "phone"],
    "customer": ["name", "code", "email", "phone", "contact_person"],
    "product": ["name", "code", "sku", "barcode", "description"],
    "organization": ["name", "code", "email", "website"],
    "order": ["order_number", "customer_po_number", "notes"]
}