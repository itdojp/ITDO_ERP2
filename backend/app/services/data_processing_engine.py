"""
CC02 v55.0 Data Processing Engine
Enterprise-grade Data Processing and Analytics System
Day 4 of 7-day intensive backend development
"""

from typing import List, Dict, Any, Optional, Union, Callable, Type, Iterator
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import json
import asyncio
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import concurrent.futures
from functools import reduce

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import DataProcessingError, ValidationError
from app.models.data_processing import (
    DataPipeline, ProcessingJob, DataTransformation, DataSource,
    ProcessingStep, JobExecution, DataQualityCheck, ProcessingMetrics
)
from app.services.audit_service import AuditService

class ProcessingType(str, Enum):
    ETL = "etl"
    AGGREGATION = "aggregation"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    ANALYTICS = "analytics"
    MACHINE_LEARNING = "machine_learning"
    REAL_TIME = "real_time"
    BATCH = "batch"

class DataSourceType(str, Enum):
    DATABASE = "database"
    FILE = "file"
    API = "api"
    STREAM = "stream"
    QUEUE = "queue"
    WEBHOOK = "webhook"
    SCHEDULED = "scheduled"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class QualityCheckType(str, Enum):
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    TIMELINESS = "timeliness"

class AggregationType(str, Enum):
    SUM = "sum"
    COUNT = "count"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STDDEV = "stddev"
    PERCENTILE = "percentile"

@dataclass
class ProcessingContext:
    """Context for data processing operations"""
    job_id: UUID
    pipeline_id: Optional[UUID] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[UUID] = None
    session: Optional[AsyncSession] = None
    execution_id: Optional[UUID] = None

@dataclass
class ProcessingResult:
    """Result of data processing operation"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_deleted: int = 0
    execution_time_ms: float = 0
    memory_used_mb: float = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

class BaseProcessor(ABC):
    """Base class for data processors"""
    
    def __init__(self, processor_type: ProcessingType, config: Dict[str, Any]):
        self.processor_type = processor_type
        self.config = config
    
    @abstractmethod
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """Process data"""
        pass
    
    def validate_config(self) -> List[str]:
        """Validate processor configuration"""
        return []

class ETLProcessor(BaseProcessor):
    """Extract, Transform, Load processor"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(ProcessingType.ETL, config)
        self.extract_config = config.get('extract', {})
        self.transform_config = config.get('transform', {})
        self.load_config = config.get('load', {})
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """Execute ETL process"""
        
        start_time = datetime.utcnow()
        result = ProcessingResult(success=True)
        
        try:
            # Extract
            extracted_data = await self._extract_data(context)
            result.records_processed = len(extracted_data) if isinstance(extracted_data, list) else 1
            
            # Transform
            transformed_data = await self._transform_data(extracted_data, context)
            
            # Load
            load_result = await self._load_data(transformed_data, context)
            result.records_created = load_result.get('created', 0)
            result.records_updated = load_result.get('updated', 0)
            
            result.data = {"processed_records": result.records_processed}
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        
        finally:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
        
        return result
    
    async def _extract_data(self, context: ProcessingContext) -> List[Dict[str, Any]]:
        """Extract data from source"""
        
        source_type = self.extract_config.get('source_type', 'database')
        
        if source_type == 'database':
            return await self._extract_from_database(context)
        elif source_type == 'file':
            return await self._extract_from_file(context)
        elif source_type == 'api':
            return await self._extract_from_api(context)
        else:
            raise DataProcessingError(f"Unsupported source type: {source_type}")
    
    async def _extract_from_database(self, context: ProcessingContext) -> List[Dict[str, Any]]:
        """Extract data from database"""
        
        if not context.session:
            raise DataProcessingError("Database session required for extraction")
        
        query = self.extract_config.get('query')
        table = self.extract_config.get('table')
        
        if query:
            result = await context.session.execute(text(query))
            return [dict(row) for row in result.fetchall()]
        elif table:
            # Simple table extraction
            result = await context.session.execute(text(f"SELECT * FROM {table}"))
            return [dict(row) for row in result.fetchall()]
        else:
            raise DataProcessingError("Query or table name required for database extraction")
    
    async def _extract_from_file(self, context: ProcessingContext) -> List[Dict[str, Any]]:
        """Extract data from file"""
        
        file_path = self.extract_config.get('file_path')
        file_format = self.extract_config.get('format', 'csv')
        
        if not file_path:
            raise DataProcessingError("File path required for file extraction")
        
        try:
            if file_format == 'csv':
                df = pd.read_csv(file_path)
                return df.to_dict('records')
            elif file_format == 'json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return data if isinstance(data, list) else [data]
            elif file_format == 'excel':
                df = pd.read_excel(file_path)
                return df.to_dict('records')
            else:
                raise DataProcessingError(f"Unsupported file format: {file_format}")
        
        except Exception as e:
            raise DataProcessingError(f"Error extracting from file: {str(e)}")
    
    async def _extract_from_api(self, context: ProcessingContext) -> List[Dict[str, Any]]:
        """Extract data from API"""
        
        # Would implement API extraction
        # For now, return mock data
        return [{"id": 1, "data": "mock"}]
    
    async def _transform_data(self, data: List[Dict[str, Any]], context: ProcessingContext) -> List[Dict[str, Any]]:
        """Transform extracted data"""
        
        transformations = self.transform_config.get('transformations', [])
        
        for transformation in transformations:
            transform_type = transformation.get('type')
            
            if transform_type == 'filter':
                data = self._filter_data(data, transformation.get('condition'))
            elif transform_type == 'map':
                data = self._map_data(data, transformation.get('mapping'))
            elif transform_type == 'aggregate':
                data = self._aggregate_data(data, transformation.get('groupby'), transformation.get('aggregations'))
            elif transform_type == 'join':
                data = await self._join_data(data, transformation, context)
            elif transform_type == 'clean':
                data = self._clean_data(data, transformation.get('rules'))
            elif transform_type == 'validate':
                data = self._validate_data(data, transformation.get('rules'))
        
        return data
    
    def _filter_data(self, data: List[Dict[str, Any]], condition: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter data based on condition"""
        
        if not condition:
            return data
        
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        if not all([field, operator, value]):
            return data
        
        filtered_data = []
        for record in data:
            record_value = record.get(field)
            
            if operator == 'equals' and record_value == value:
                filtered_data.append(record)
            elif operator == 'not_equals' and record_value != value:
                filtered_data.append(record)
            elif operator == 'greater_than' and record_value > value:
                filtered_data.append(record)
            elif operator == 'less_than' and record_value < value:
                filtered_data.append(record)
            elif operator == 'contains' and value in str(record_value):
                filtered_data.append(record)
        
        return filtered_data
    
    def _map_data(self, data: List[Dict[str, Any]], mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Map/rename fields in data"""
        
        if not mapping:
            return data
        
        mapped_data = []
        for record in data:
            mapped_record = {}
            for old_field, new_field in mapping.items():
                if old_field in record:
                    mapped_record[new_field] = record[old_field]
            
            # Keep unmapped fields
            for field, value in record.items():
                if field not in mapping and field not in mapped_record:
                    mapped_record[field] = value
            
            mapped_data.append(mapped_record)
        
        return mapped_data
    
    def _aggregate_data(self, data: List[Dict[str, Any]], groupby: List[str], aggregations: Dict[str, str]) -> List[Dict[str, Any]]:
        """Aggregate data by group"""
        
        if not groupby or not aggregations:
            return data
        
        # Convert to pandas for easier aggregation
        df = pd.DataFrame(data)
        
        agg_functions = {}
        for field, agg_type in aggregations.items():
            if agg_type == 'sum':
                agg_functions[field] = 'sum'
            elif agg_type == 'count':
                agg_functions[field] = 'count'
            elif agg_type == 'average':
                agg_functions[field] = 'mean'
            elif agg_type == 'min':
                agg_functions[field] = 'min'
            elif agg_type == 'max':
                agg_functions[field] = 'max'
        
        if agg_functions:
            result_df = df.groupby(groupby).agg(agg_functions).reset_index()
            return result_df.to_dict('records')
        
        return data
    
    async def _join_data(self, data: List[Dict[str, Any]], join_config: Dict[str, Any], context: ProcessingContext) -> List[Dict[str, Any]]:
        """Join data with another dataset"""
        
        # Would implement data joining logic
        # For now, return original data
        return data
    
    def _clean_data(self, data: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean data based on rules"""
        
        if not rules:
            return data
        
        cleaned_data = []
        for record in data:
            cleaned_record = record.copy()
            
            for rule in rules:
                rule_type = rule.get('type')
                field = rule.get('field')
                
                if field not in cleaned_record:
                    continue
                
                if rule_type == 'remove_nulls' and cleaned_record[field] is None:
                    del cleaned_record[field]
                elif rule_type == 'trim_whitespace' and isinstance(cleaned_record[field], str):
                    cleaned_record[field] = cleaned_record[field].strip()
                elif rule_type == 'convert_type':
                    target_type = rule.get('target_type')
                    try:
                        if target_type == 'int':
                            cleaned_record[field] = int(cleaned_record[field])
                        elif target_type == 'float':
                            cleaned_record[field] = float(cleaned_record[field])
                        elif target_type == 'str':
                            cleaned_record[field] = str(cleaned_record[field])
                    except (ValueError, TypeError):
                        pass
            
            cleaned_data.append(cleaned_record)
        
        return cleaned_data
    
    def _validate_data(self, data: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate data and remove invalid records"""
        
        if not rules:
            return data
        
        valid_data = []
        for record in data:
            is_valid = True
            
            for rule in rules:
                rule_type = rule.get('type')
                field = rule.get('field')
                
                if field not in record:
                    if rule.get('required', False):
                        is_valid = False
                        break
                    continue
                
                value = record[field]
                
                if rule_type == 'not_null' and value is None:
                    is_valid = False
                    break
                elif rule_type == 'min_length' and len(str(value)) < rule.get('value', 0):
                    is_valid = False
                    break
                elif rule_type == 'max_length' and len(str(value)) > rule.get('value', 999):
                    is_valid = False
                    break
                elif rule_type == 'regex' and not re.match(rule.get('pattern', ''), str(value)):
                    is_valid = False
                    break
            
            if is_valid:
                valid_data.append(record)
        
        return valid_data
    
    async def _load_data(self, data: List[Dict[str, Any]], context: ProcessingContext) -> Dict[str, int]:
        """Load transformed data to target"""
        
        target_type = self.load_config.get('target_type', 'database')
        
        if target_type == 'database':
            return await self._load_to_database(data, context)
        elif target_type == 'file':
            return await self._load_to_file(data, context)
        elif target_type == 'api':
            return await self._load_to_api(data, context)
        else:
            raise DataProcessingError(f"Unsupported target type: {target_type}")
    
    async def _load_to_database(self, data: List[Dict[str, Any]], context: ProcessingContext) -> Dict[str, int]:
        """Load data to database"""
        
        if not context.session:
            raise DataProcessingError("Database session required for loading")
        
        table = self.load_config.get('table')
        mode = self.load_config.get('mode', 'insert')  # insert, update, upsert
        
        if not table:
            raise DataProcessingError("Target table required for database loading")
        
        created = 0
        updated = 0
        
        for record in data:
            if mode == 'insert':
                # Insert record
                fields = ', '.join(record.keys())
                placeholders = ', '.join([f":{key}" for key in record.keys()])
                query = f"INSERT INTO {table} ({fields}) VALUES ({placeholders})"
                await context.session.execute(text(query), record)
                created += 1
            elif mode == 'update':
                # Update existing record
                # Would implement update logic
                updated += 1
            elif mode == 'upsert':
                # Insert or update
                # Would implement upsert logic
                created += 1
        
        return {"created": created, "updated": updated}
    
    async def _load_to_file(self, data: List[Dict[str, Any]], context: ProcessingContext) -> Dict[str, int]:
        """Load data to file"""
        
        file_path = self.load_config.get('file_path')
        file_format = self.load_config.get('format', 'csv')
        
        if not file_path:
            raise DataProcessingError("File path required for file loading")
        
        try:
            if file_format == 'csv':
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False)
            elif file_format == 'json':
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            elif file_format == 'excel':
                df = pd.DataFrame(data)
                df.to_excel(file_path, index=False)
            
            return {"created": len(data), "updated": 0}
        
        except Exception as e:
            raise DataProcessingError(f"Error loading to file: {str(e)}")
    
    async def _load_to_api(self, data: List[Dict[str, Any]], context: ProcessingContext) -> Dict[str, int]:
        """Load data to API"""
        
        # Would implement API loading
        return {"created": len(data), "updated": 0}

class AggregationProcessor(BaseProcessor):
    """Data aggregation processor"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(ProcessingType.AGGREGATION, config)
        self.groupby_fields = config.get('groupby', [])
        self.aggregations = config.get('aggregations', {})
        self.filters = config.get('filters', [])
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """Process aggregation"""
        
        start_time = datetime.utcnow()
        result = ProcessingResult(success=True)
        
        try:
            # Get source data
            source_data = context.data.get('records', [])
            if not source_data:
                # Load from database if no data provided
                source_data = await self._load_source_data(context)
            
            result.records_processed = len(source_data)
            
            # Apply filters
            filtered_data = self._apply_filters(source_data)
            
            # Perform aggregation
            aggregated_data = self._perform_aggregation(filtered_data)
            
            result.data = {"aggregated_records": aggregated_data}
            result.records_created = len(aggregated_data)
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        
        finally:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
        
        return result
    
    async def _load_source_data(self, context: ProcessingContext) -> List[Dict[str, Any]]:
        """Load source data from database"""
        
        if not context.session:
            return []
        
        table = self.config.get('source_table')
        if not table:
            return []
        
        result = await context.session.execute(text(f"SELECT * FROM {table}"))
        return [dict(row) for row in result.fetchall()]
    
    def _apply_filters(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply filters to data"""
        
        filtered_data = data
        
        for filter_config in self.filters:
            field = filter_config.get('field')
            operator = filter_config.get('operator')
            value = filter_config.get('value')
            
            if not all([field, operator, value]):
                continue
            
            filtered_data = [
                record for record in filtered_data
                if self._evaluate_filter(record.get(field), operator, value)
            ]
        
        return filtered_data
    
    def _evaluate_filter(self, field_value: Any, operator: str, filter_value: Any) -> bool:
        """Evaluate filter condition"""
        
        try:
            if operator == 'equals':
                return field_value == filter_value
            elif operator == 'not_equals':
                return field_value != filter_value
            elif operator == 'greater_than':
                return float(field_value) > float(filter_value)
            elif operator == 'less_than':
                return float(field_value) < float(filter_value)
            elif operator == 'greater_equal':
                return float(field_value) >= float(filter_value)
            elif operator == 'less_equal':
                return float(field_value) <= float(filter_value)
            elif operator == 'in':
                return field_value in filter_value if isinstance(filter_value, list) else False
            elif operator == 'contains':
                return str(filter_value) in str(field_value)
        except (ValueError, TypeError):
            return False
        
        return False
    
    def _perform_aggregation(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform data aggregation"""
        
        if not data:
            return []
        
        # Convert to pandas DataFrame for easier aggregation
        df = pd.DataFrame(data)
        
        # Group by specified fields
        if self.groupby_fields:
            grouped = df.groupby(self.groupby_fields)
        else:
            # No grouping - aggregate entire dataset
            grouped = df
        
        # Apply aggregations
        agg_results = []
        
        if self.groupby_fields:
            for name, group in grouped:
                agg_record = {}
                
                # Add groupby fields
                if isinstance(name, tuple):
                    for i, field in enumerate(self.groupby_fields):
                        agg_record[field] = name[i]
                else:
                    agg_record[self.groupby_fields[0]] = name
                
                # Add aggregated fields
                for field, agg_type in self.aggregations.items():
                    if field in group.columns:
                        agg_value = self._calculate_aggregation(group[field], agg_type)
                        agg_record[f"{field}_{agg_type}"] = agg_value
                
                agg_results.append(agg_record)
        else:
            # Single aggregation record
            agg_record = {}
            for field, agg_type in self.aggregations.items():
                if field in df.columns:
                    agg_value = self._calculate_aggregation(df[field], agg_type)
                    agg_record[f"{field}_{agg_type}"] = agg_value
            
            agg_results.append(agg_record)
        
        return agg_results
    
    def _calculate_aggregation(self, series: pd.Series, agg_type: str) -> Any:
        """Calculate aggregation value"""
        
        try:
            if agg_type == AggregationType.SUM:
                return float(series.sum())
            elif agg_type == AggregationType.COUNT:
                return int(series.count())
            elif agg_type == AggregationType.AVERAGE:
                return float(series.mean())
            elif agg_type == AggregationType.MIN:
                return float(series.min())
            elif agg_type == AggregationType.MAX:
                return float(series.max())
            elif agg_type == AggregationType.MEDIAN:
                return float(series.median())
            elif agg_type == AggregationType.STDDEV:
                return float(series.std())
            else:
                return 0
        except Exception:
            return 0

class ValidationProcessor(BaseProcessor):
    """Data validation processor"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(ProcessingType.VALIDATION, config)
        self.validation_rules = config.get('rules', [])
        self.quality_checks = config.get('quality_checks', [])
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """Process data validation"""
        
        start_time = datetime.utcnow()
        result = ProcessingResult(success=True)
        
        try:
            source_data = context.data.get('records', [])
            result.records_processed = len(source_data)
            
            # Run validation rules
            validation_results = self._run_validation_rules(source_data)
            
            # Run quality checks
            quality_results = self._run_quality_checks(source_data)
            
            # Combine results
            all_issues = validation_results + quality_results
            
            if all_issues:
                result.warnings.extend([issue['message'] for issue in all_issues])
            
            result.data = {
                "validation_issues": all_issues,
                "valid_records": len(source_data) - len(all_issues),
                "total_records": len(source_data)
            }
            
            # Mark as failed if critical issues found
            critical_issues = [issue for issue in all_issues if issue.get('severity') == 'critical']
            if critical_issues:
                result.success = False
                result.errors.extend([issue['message'] for issue in critical_issues])
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        
        finally:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
        
        return result
    
    def _run_validation_rules(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run validation rules on data"""
        
        issues = []
        
        for i, record in enumerate(data):
            for rule in self.validation_rules:
                rule_type = rule.get('type')
                field = rule.get('field')
                
                if field not in record:
                    if rule.get('required', False):
                        issues.append({
                            'record_index': i,
                            'field': field,
                            'rule': rule_type,
                            'message': f"Required field '{field}' is missing",
                            'severity': 'critical'
                        })
                    continue
                
                value = record[field]
                
                if rule_type == 'not_null' and value is None:
                    issues.append({
                        'record_index': i,
                        'field': field,
                        'rule': rule_type,
                        'message': f"Field '{field}' cannot be null",
                        'severity': 'critical'
                    })
                elif rule_type == 'data_type':
                    expected_type = rule.get('expected_type')
                    if not self._check_data_type(value, expected_type):
                        issues.append({
                            'record_index': i,
                            'field': field,
                            'rule': rule_type,
                            'message': f"Field '{field}' has incorrect data type",
                            'severity': 'high'
                        })
                elif rule_type == 'range':
                    min_val = rule.get('min')
                    max_val = rule.get('max')
                    if not self._check_range(value, min_val, max_val):
                        issues.append({
                            'record_index': i,
                            'field': field,
                            'rule': rule_type,
                            'message': f"Field '{field}' value out of range",
                            'severity': 'medium'
                        })
                elif rule_type == 'format':
                    pattern = rule.get('pattern')
                    if pattern and not re.match(pattern, str(value)):
                        issues.append({
                            'record_index': i,
                            'field': field,
                            'rule': rule_type,
                            'message': f"Field '{field}' format is invalid",
                            'severity': 'medium'
                        })
        
        return issues
    
    def _run_quality_checks(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run data quality checks"""
        
        issues = []
        
        for check in self.quality_checks:
            check_type = check.get('type')
            
            if check_type == QualityCheckType.COMPLETENESS:
                completeness_issues = self._check_completeness(data, check)
                issues.extend(completeness_issues)
            elif check_type == QualityCheckType.UNIQUENESS:
                uniqueness_issues = self._check_uniqueness(data, check)
                issues.extend(uniqueness_issues)
            elif check_type == QualityCheckType.CONSISTENCY:
                consistency_issues = self._check_consistency(data, check)
                issues.extend(consistency_issues)
        
        return issues
    
    def _check_data_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected data type"""
        
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'integer':
            return isinstance(value, int) or (isinstance(value, str) and value.isdigit())
        elif expected_type == 'float':
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        elif expected_type == 'boolean':
            return isinstance(value, bool) or str(value).lower() in ['true', 'false', '0', '1']
        elif expected_type == 'date':
            try:
                pd.to_datetime(value)
                return True
            except:
                return False
        
        return True
    
    def _check_range(self, value: Any, min_val: Any, max_val: Any) -> bool:
        """Check if value is within range"""
        
        try:
            num_value = float(value)
            if min_val is not None and num_value < float(min_val):
                return False
            if max_val is not None and num_value > float(max_val):
                return False
            return True
        except (ValueError, TypeError):
            return True
    
    def _check_completeness(self, data: List[Dict[str, Any]], check: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check data completeness"""
        
        issues = []
        fields = check.get('fields', [])
        threshold = check.get('threshold', 0.95)  # 95% completeness required
        
        for field in fields:
            non_null_count = sum(1 for record in data if record.get(field) is not None)
            completeness_rate = non_null_count / len(data) if data else 0
            
            if completeness_rate < threshold:
                issues.append({
                    'field': field,
                    'check': 'completeness',
                    'message': f"Field '{field}' completeness {completeness_rate:.2%} below threshold {threshold:.2%}",
                    'severity': 'medium',
                    'metrics': {
                        'completeness_rate': completeness_rate,
                        'threshold': threshold,
                        'non_null_count': non_null_count,
                        'total_count': len(data)
                    }
                })
        
        return issues
    
    def _check_uniqueness(self, data: List[Dict[str, Any]], check: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check data uniqueness"""
        
        issues = []
        fields = check.get('fields', [])
        
        for field in fields:
            values = [record.get(field) for record in data if record.get(field) is not None]
            unique_values = set(values)
            
            if len(values) != len(unique_values):
                duplicate_count = len(values) - len(unique_values)
                issues.append({
                    'field': field,
                    'check': 'uniqueness',
                    'message': f"Field '{field}' has {duplicate_count} duplicate values",
                    'severity': 'high',
                    'metrics': {
                        'total_values': len(values),
                        'unique_values': len(unique_values),
                        'duplicate_count': duplicate_count
                    }
                })
        
        return issues
    
    def _check_consistency(self, data: List[Dict[str, Any]], check: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check data consistency"""
        
        issues = []
        rules = check.get('rules', [])
        
        for rule in rules:
            rule_type = rule.get('type')
            
            if rule_type == 'cross_field':
                # Check consistency between fields
                field1 = rule.get('field1')
                field2 = rule.get('field2')
                operator = rule.get('operator')
                
                inconsistent_count = 0
                for record in data:
                    val1 = record.get(field1)
                    val2 = record.get(field2)
                    
                    if val1 is not None and val2 is not None:
                        try:
                            if operator == 'greater_than' and float(val1) <= float(val2):
                                inconsistent_count += 1
                            elif operator == 'less_than' and float(val1) >= float(val2):
                                inconsistent_count += 1
                            elif operator == 'equals' and val1 != val2:
                                inconsistent_count += 1
                        except (ValueError, TypeError):
                            pass
                
                if inconsistent_count > 0:
                    issues.append({
                        'fields': [field1, field2],
                        'check': 'consistency',
                        'message': f"Cross-field consistency violation: {field1} {operator} {field2}",
                        'severity': 'medium',
                        'metrics': {
                            'inconsistent_records': inconsistent_count,
                            'total_records': len(data)
                        }
                    })
        
        return issues

class DataProcessingEngine:
    """Enterprise Data Processing Engine"""
    
    def __init__(self):
        self.processors: Dict[ProcessingType, Type[BaseProcessor]] = {}
        self.active_jobs: Dict[UUID, ProcessingJob] = {}
        self.audit_service = AuditService()
        self._register_default_processors()
    
    def _register_default_processors(self):
        """Register default processors"""
        self.processors[ProcessingType.ETL] = ETLProcessor
        self.processors[ProcessingType.AGGREGATION] = AggregationProcessor
        self.processors[ProcessingType.VALIDATION] = ValidationProcessor
    
    async def create_job(
        self,
        name: str,
        processing_type: ProcessingType,
        config: Dict[str, Any],
        schedule: Optional[str] = None,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None
    ) -> ProcessingJob:
        """Create a new processing job"""
        
        job = ProcessingJob(
            id=uuid4(),
            name=name,
            processing_type=processing_type,
            config=config,
            schedule=schedule,
            status=JobStatus.PENDING,
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if session:
            session.add(job)
            await session.commit()
            await session.refresh(job)
        
        return job
    
    async def execute_job(
        self,
        job_id: UUID,
        input_data: Dict[str, Any] = None,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None
    ) -> ProcessingResult:
        """Execute a processing job"""
        
        # Get job
        if session:
            job_result = await session.execute(
                select(ProcessingJob).where(ProcessingJob.id == job_id)
            )
            job = job_result.scalar_one_or_none()
        else:
            job = self.active_jobs.get(job_id)
        
        if not job:
            raise DataProcessingError(f"Job {job_id} not found")
        
        # Create processor
        processor_class = self.processors.get(job.processing_type)
        if not processor_class:
            raise DataProcessingError(f"No processor found for type {job.processing_type}")
        
        processor = processor_class(job.config)
        
        # Validate processor config
        config_errors = processor.validate_config()
        if config_errors:
            raise DataProcessingError(f"Invalid processor config: {', '.join(config_errors)}")
        
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        
        self.active_jobs[job_id] = job
        
        try:
            # Create processing context
            context = ProcessingContext(
                job_id=job_id,
                data=input_data or {},
                user_id=user_id,
                session=session,
                execution_id=uuid4()
            )
            
            # Execute processor
            result = await processor.process(context)
            
            # Update job with results
            job.status = JobStatus.COMPLETED if result.success else JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            job.records_processed = result.records_processed
            job.execution_time_ms = result.execution_time_ms
            job.error_message = '; '.join(result.errors) if result.errors else None
            
            # Log job execution
            await self._log_job_execution(job, result, user_id)
            
            return result
        
        except Exception as e:
            # Update job with error
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            job.error_message = str(e)
            
            raise DataProcessingError(f"Job execution failed: {str(e)}")
        
        finally:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    async def schedule_job(
        self,
        job_id: UUID,
        schedule_expression: str,
        session: Optional[AsyncSession] = None
    ):
        """Schedule a job for execution"""
        
        # Would implement job scheduling with cron-like expressions
        # For now, just update the job record
        if session:
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.id == job_id)
                .values(
                    schedule=schedule_expression,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
    
    async def cancel_job(
        self,
        job_id: UUID,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None
    ):
        """Cancel a running job"""
        
        job = self.active_jobs.get(job_id)
        if job:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
        
        if session:
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.id == job_id)
                .values(
                    status=JobStatus.CANCELLED,
                    completed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
    
    async def get_job_status(
        self,
        job_id: UUID,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Get job execution status"""
        
        job = None
        if session:
            job_result = await session.execute(
                select(ProcessingJob).where(ProcessingJob.id == job_id)
            )
            job = job_result.scalar_one_or_none()
        else:
            job = self.active_jobs.get(job_id)
        
        if not job:
            return {"error": "Job not found"}
        
        return {
            "job_id": str(job.id),
            "name": job.name,
            "status": job.status.value,
            "processing_type": job.processing_type.value,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "records_processed": job.records_processed,
            "execution_time_ms": job.execution_time_ms,
            "error_message": job.error_message
        }
    
    async def _log_job_execution(
        self,
        job: ProcessingJob,
        result: ProcessingResult,
        user_id: Optional[UUID]
    ):
        """Log job execution details"""
        
        await self.audit_service.log_event(
            event_type="data_processing_job",
            entity_type="processing_job",
            entity_id=job.id,
            user_id=user_id,
            details={
                "job_name": job.name,
                "processing_type": job.processing_type.value,
                "status": job.status.value,
                "success": result.success,
                "records_processed": result.records_processed,
                "records_created": result.records_created,
                "records_updated": result.records_updated,
                "execution_time_ms": result.execution_time_ms,
                "memory_used_mb": result.memory_used_mb,
                "error_count": len(result.errors),
                "warning_count": len(result.warnings)
            }
        )
    
    def register_processor(self, processing_type: ProcessingType, processor_class: Type[BaseProcessor]):
        """Register custom processor"""
        self.processors[processing_type] = processor_class
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get list of active jobs"""
        return [
            {
                "job_id": str(job.id),
                "name": job.name,
                "status": job.status.value,
                "started_at": job.started_at.isoformat() if job.started_at else None
            }
            for job in self.active_jobs.values()
        ]

# Singleton instance
data_processing_engine = DataProcessingEngine()

# Helper functions
async def create_processing_job(
    name: str,
    processing_type: ProcessingType,
    config: Dict[str, Any],
    schedule: Optional[str] = None,
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None
) -> ProcessingJob:
    """Create processing job"""
    return await data_processing_engine.create_job(
        name, processing_type, config, schedule, user_id, session
    )

async def execute_processing_job(
    job_id: UUID,
    input_data: Dict[str, Any] = None,
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None
) -> ProcessingResult:
    """Execute processing job"""
    return await data_processing_engine.execute_job(job_id, input_data, user_id, session)

async def get_processing_job_status(
    job_id: UUID,
    session: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """Get job status"""
    return await data_processing_engine.get_job_status(job_id, session)