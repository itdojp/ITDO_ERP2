"""Data Pipeline & ETL Processing System."""

import asyncio
import json
import pickle
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from uuid import uuid4

from app.core.monitoring import monitor_performance


class DataSourceType(str, Enum):
    """Data source types."""
    DATABASE = "database"
    API = "api"
    FILE = "file"
    STREAM = "stream"
    WEBHOOK = "webhook"
    FTP = "ftp"
    S3 = "s3"
    MESSAGE_QUEUE = "message_queue"


class DataFormat(str, Enum):
    """Data formats."""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    PARQUET = "parquet"
    AVRO = "avro"
    BINARY = "binary"
    TEXT = "text"


class TransformationType(str, Enum):
    """Data transformation types."""
    FILTER = "filter"
    MAP = "map"
    AGGREGATE = "aggregate"
    JOIN = "join"
    UNION = "union"
    SORT = "sort"
    VALIDATE = "validate"
    CLEAN = "clean"
    ENRICH = "enrich"
    CUSTOM = "custom"


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class DataQuality(str, Enum):
    """Data quality levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    POOR = "poor"


@dataclass
class DataSource:
    """Data source configuration."""
    id: str
    name: str
    source_type: DataSourceType
    connection_config: Dict[str, Any]
    data_format: DataFormat
    schema_definition: Dict[str, Any] = field(default_factory=dict)
    refresh_interval: int = 3600  # seconds
    enabled: bool = True
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class TransformationStep:
    """Data transformation step."""
    id: str
    name: str
    transformation_type: TransformationType
    configuration: Dict[str, Any]
    order: int = 0
    enabled: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class DataTarget:
    """Data target configuration."""
    id: str
    name: str
    target_type: DataSourceType
    connection_config: Dict[str, Any]
    data_format: DataFormat
    batch_size: int = 1000
    enabled: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class Pipeline:
    """Data pipeline definition."""
    id: str
    name: str
    description: str
    sources: List[DataSource] = field(default_factory=list)
    transformations: List[TransformationStep] = field(default_factory=list)
    targets: List[DataTarget] = field(default_factory=list)
    schedule: Optional[str] = None  # Cron expression
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class PipelineExecution:
    """Pipeline execution instance."""
    id: str
    pipeline_id: str
    status: PipelineStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class DataQualityReport:
    """Data quality assessment report."""
    id: str
    pipeline_id: str
    execution_id: str
    quality_score: float
    quality_level: DataQuality
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


class DataConnector:
    """Data connector for various sources and targets."""
    
    def __init__(self):
        """Initialize data connector."""
        self.connections: Dict[str, Any] = {}
        self.connection_pools: Dict[str, Any] = {}
    
    @monitor_performance("data_pipeline.connector.read")
    async def read_data(
        self,
        source: DataSource,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Read data from source."""
        try:
            if source.source_type == DataSourceType.DATABASE:
                return await self._read_from_database(source, limit)
            elif source.source_type == DataSourceType.API:
                return await self._read_from_api(source, limit)
            elif source.source_type == DataSourceType.FILE:
                return await self._read_from_file(source, limit)
            elif source.source_type == DataSourceType.STREAM:
                return await self._read_from_stream(source, limit)
            else:
                # Simulate reading data
                return await self._generate_sample_data(source, limit or 100)
        
        except Exception as e:
            print(f"Error reading from source {source.id}: {e}")
            return []
    
    @monitor_performance("data_pipeline.connector.write")
    async def write_data(
        self,
        target: DataTarget,
        data: List[Dict[str, Any]]
    ) -> bool:
        """Write data to target."""
        try:
            if target.target_type == DataSourceType.DATABASE:
                return await self._write_to_database(target, data)
            elif target.target_type == DataSourceType.API:
                return await self._write_to_api(target, data)
            elif target.target_type == DataSourceType.FILE:
                return await self._write_to_file(target, data)
            else:
                # Simulate writing data
                await asyncio.sleep(0.1)
                return True
        
        except Exception as e:
            print(f"Error writing to target {target.id}: {e}")
            return False
    
    async def _read_from_database(
        self,
        source: DataSource,
        limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Read data from database source."""
        # Simulate database read
        await asyncio.sleep(0.2)
        return await self._generate_sample_data(source, limit or 100)
    
    async def _read_from_api(
        self,
        source: DataSource,
        limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Read data from API source."""
        # Simulate API call
        await asyncio.sleep(0.3)
        return await self._generate_sample_data(source, limit or 50)
    
    async def _read_from_file(
        self,
        source: DataSource,
        limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Read data from file source."""
        # Simulate file read
        await asyncio.sleep(0.1)
        return await self._generate_sample_data(source, limit or 200)
    
    async def _read_from_stream(
        self,
        source: DataSource,
        limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Read data from stream source."""
        # Simulate stream read
        await asyncio.sleep(0.05)
        return await self._generate_sample_data(source, limit or 10)
    
    async def _write_to_database(
        self,
        target: DataTarget,
        data: List[Dict[str, Any]]
    ) -> bool:
        """Write data to database target."""
        # Simulate database write
        await asyncio.sleep(len(data) * 0.001)
        return True
    
    async def _write_to_api(
        self,
        target: DataTarget,
        data: List[Dict[str, Any]]
    ) -> bool:
        """Write data to API target."""
        # Simulate API write
        await asyncio.sleep(len(data) * 0.002)
        return True
    
    async def _write_to_file(
        self,
        target: DataTarget,
        data: List[Dict[str, Any]]
    ) -> bool:
        """Write data to file target."""
        # Simulate file write
        await asyncio.sleep(len(data) * 0.0005)
        return True
    
    async def _generate_sample_data(
        self,
        source: DataSource,
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate sample data for demonstration."""
        data = []
        
        for i in range(count):
            record = {
                "id": f"{source.name}_{i}",
                "timestamp": datetime.utcnow().isoformat(),
                "source": source.name,
                "value": 100 + (i % 50),
                "category": f"category_{i % 5}",
                "status": "active" if i % 3 == 0 else "inactive"
            }
            data.append(record)
        
        return data


class DataTransformer:
    """Data transformation engine."""
    
    def __init__(self):
        """Initialize data transformer."""
        self.custom_functions: Dict[str, Callable] = {}
    
    @monitor_performance("data_pipeline.transformer.transform")
    async def apply_transformations(
        self,
        data: List[Dict[str, Any]],
        transformations: List[TransformationStep]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Apply transformations to data."""
        transformed_data = data.copy()
        errors = []
        
        # Sort transformations by order
        sorted_transformations = sorted(
            [t for t in transformations if t.enabled],
            key=lambda x: x.order
        )
        
        for transformation in sorted_transformations:
            try:
                transformed_data = await self._apply_single_transformation(
                    transformed_data, transformation
                )
            except Exception as e:
                errors.append({
                    "transformation_id": transformation.id,
                    "transformation_name": transformation.name,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return transformed_data, errors
    
    async def _apply_single_transformation(
        self,
        data: List[Dict[str, Any]],
        transformation: TransformationStep
    ) -> List[Dict[str, Any]]:
        """Apply single transformation step."""
        config = transformation.configuration
        
        if transformation.transformation_type == TransformationType.FILTER:
            return await self._apply_filter(data, config)
        elif transformation.transformation_type == TransformationType.MAP:
            return await self._apply_map(data, config)
        elif transformation.transformation_type == TransformationType.AGGREGATE:
            return await self._apply_aggregate(data, config)
        elif transformation.transformation_type == TransformationType.JOIN:
            return await self._apply_join(data, config)
        elif transformation.transformation_type == TransformationType.SORT:
            return await self._apply_sort(data, config)
        elif transformation.transformation_type == TransformationType.VALIDATE:
            return await self._apply_validate(data, config)
        elif transformation.transformation_type == TransformationType.CLEAN:
            return await self._apply_clean(data, config)
        elif transformation.transformation_type == TransformationType.ENRICH:
            return await self._apply_enrich(data, config)
        else:
            return data
    
    async def _apply_filter(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filter transformation."""
        condition = config.get("condition", "True")
        filtered_data = []
        
        for record in data:
            try:
                # Simple condition evaluation - in production, use safer evaluation
                if eval(condition, {}, record):
                    filtered_data.append(record)
            except:
                # Skip invalid records
                continue
        
        return filtered_data
    
    async def _apply_map(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply map transformation."""
        mappings = config.get("mappings", {})
        mapped_data = []
        
        for record in data:
            mapped_record = {}
            for target_field, source_field in mappings.items():
                if source_field in record:
                    mapped_record[target_field] = record[source_field]
            
            # Include unmapped fields
            for field, value in record.items():
                if field not in mappings.values():
                    mapped_record[field] = value
            
            mapped_data.append(mapped_record)
        
        return mapped_data
    
    async def _apply_aggregate(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply aggregate transformation."""
        group_by = config.get("group_by", [])
        aggregations = config.get("aggregations", {})
        
        if not group_by:
            return data
        
        # Group data
        groups = defaultdict(list)
        for record in data:
            key = tuple(record.get(field) for field in group_by)
            groups[key].append(record)
        
        # Apply aggregations
        aggregated_data = []
        for group_key, group_records in groups.items():
            agg_record = {}
            
            # Add group by fields
            for i, field in enumerate(group_by):
                agg_record[field] = group_key[i]
            
            # Apply aggregation functions
            for field, agg_func in aggregations.items():
                values = [r.get(field, 0) for r in group_records if r.get(field) is not None]
                
                if agg_func == "sum":
                    agg_record[f"{field}_sum"] = sum(values)
                elif agg_func == "avg":
                    agg_record[f"{field}_avg"] = sum(values) / len(values) if values else 0
                elif agg_func == "count":
                    agg_record[f"{field}_count"] = len(values)
                elif agg_func == "min":
                    agg_record[f"{field}_min"] = min(values) if values else None
                elif agg_func == "max":
                    agg_record[f"{field}_max"] = max(values) if values else None
            
            aggregated_data.append(agg_record)
        
        return aggregated_data
    
    async def _apply_join(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply join transformation."""
        # Simplified join - in production, implement proper join logic
        return data
    
    async def _apply_sort(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply sort transformation."""
        sort_field = config.get("field", "id")
        reverse = config.get("reverse", False)
        
        try:
            return sorted(data, key=lambda x: x.get(sort_field, ""), reverse=reverse)
        except:
            return data
    
    async def _apply_validate(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply validation transformation."""
        rules = config.get("rules", {})
        validated_data = []
        
        for record in data:
            valid = True
            
            for field, rule in rules.items():
                value = record.get(field)
                
                if rule.get("required") and value is None:
                    valid = False
                    break
                
                if rule.get("type") and value is not None:
                    expected_type = rule["type"]
                    if expected_type == "int" and not isinstance(value, int):
                        valid = False
                        break
                    elif expected_type == "str" and not isinstance(value, str):
                        valid = False
                        break
            
            if valid:
                validated_data.append(record)
        
        return validated_data
    
    async def _apply_clean(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply data cleaning transformation."""
        cleaned_data = []
        
        for record in data:
            cleaned_record = {}
            
            for field, value in record.items():
                if value is not None:
                    # Remove leading/trailing whitespace for strings
                    if isinstance(value, str):
                        cleaned_record[field] = value.strip()
                    else:
                        cleaned_record[field] = value
            
            cleaned_data.append(cleaned_record)
        
        return cleaned_data
    
    async def _apply_enrich(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply data enrichment transformation."""
        enrichments = config.get("enrichments", {})
        enriched_data = []
        
        for record in data:
            enriched_record = record.copy()
            
            # Add enrichment fields
            for field, enrichment in enrichments.items():
                if enrichment["type"] == "timestamp":
                    enriched_record[field] = datetime.utcnow().isoformat()
                elif enrichment["type"] == "constant":
                    enriched_record[field] = enrichment["value"]
            
            enriched_data.append(enriched_record)
        
        return enriched_data


class DataQualityAssessor:
    """Data quality assessment engine."""
    
    def __init__(self):
        """Initialize data quality assessor."""
        pass
    
    @monitor_performance("data_pipeline.quality.assess")
    async def assess_quality(
        self,
        data: List[Dict[str, Any]],
        pipeline_id: str,
        execution_id: str
    ) -> DataQualityReport:
        """Assess data quality."""
        total_records = len(data)
        if total_records == 0:
            return DataQualityReport(
                id=str(uuid4()),
                pipeline_id=pipeline_id,
                execution_id=execution_id,
                quality_score=0.0,
                quality_level=DataQuality.POOR,
                issues=[{"type": "no_data", "message": "No data to assess"}]
            )
        
        issues = []
        metrics = {}
        
        # Check for null values
        null_counts = defaultdict(int)
        for record in data:
            for field, value in record.items():
                if value is None or value == "":
                    null_counts[field] += 1
        
        # Calculate null percentages
        for field, count in null_counts.items():
            percentage = (count / total_records) * 100
            metrics[f"{field}_null_percentage"] = percentage
            
            if percentage > 20:
                issues.append({
                    "type": "high_null_rate",
                    "field": field,
                    "percentage": percentage,
                    "message": f"High null rate in field {field}: {percentage:.1f}%"
                })
        
        # Check for duplicates
        unique_records = set()
        duplicate_count = 0
        
        for record in data:
            record_hash = hash(str(sorted(record.items())))
            if record_hash in unique_records:
                duplicate_count += 1
            else:
                unique_records.add(record_hash)
        
        duplicate_percentage = (duplicate_count / total_records) * 100
        metrics["duplicate_percentage"] = duplicate_percentage
        
        if duplicate_percentage > 5:
            issues.append({
                "type": "high_duplicate_rate",
                "percentage": duplicate_percentage,
                "count": duplicate_count,
                "message": f"High duplicate rate: {duplicate_percentage:.1f}%"
            })
        
        # Check data types consistency
        field_types = defaultdict(set)
        for record in data:
            for field, value in record.items():
                if value is not None:
                    field_types[field].add(type(value).__name__)
        
        for field, types in field_types.items():
            if len(types) > 1:
                issues.append({
                    "type": "inconsistent_types",
                    "field": field,
                    "types": list(types),
                    "message": f"Inconsistent data types in field {field}: {types}"
                })
        
        # Calculate overall quality score
        quality_score = 100.0
        
        # Deduct for issues
        quality_score -= len(issues) * 5  # 5 points per issue
        quality_score -= duplicate_percentage  # Deduct duplicate percentage
        
        # Deduct for high null rates
        for field_null_pct in metrics.values():
            if isinstance(field_null_pct, (int, float)) and field_null_pct > 10:
                quality_score -= field_null_pct / 2
        
        quality_score = max(0.0, min(100.0, quality_score))
        
        # Determine quality level
        if quality_score >= 90:
            quality_level = DataQuality.HIGH
        elif quality_score >= 70:
            quality_level = DataQuality.MEDIUM
        elif quality_score >= 50:
            quality_level = DataQuality.LOW
        else:
            quality_level = DataQuality.POOR
        
        return DataQualityReport(
            id=str(uuid4()),
            pipeline_id=pipeline_id,
            execution_id=execution_id,
            quality_score=quality_score,
            quality_level=quality_level,
            issues=issues,
            metrics=metrics
        )


class PipelineExecutor:
    """Pipeline execution engine."""
    
    def __init__(self):
        """Initialize pipeline executor."""
        self.data_connector = DataConnector()
        self.data_transformer = DataTransformer()
        self.quality_assessor = DataQualityAssessor()
        self.active_executions: Dict[str, PipelineExecution] = {}
    
    @monitor_performance("data_pipeline.executor.execute")
    async def execute_pipeline(self, pipeline: Pipeline) -> PipelineExecution:
        """Execute a data pipeline."""
        execution = PipelineExecution(
            id=str(uuid4()),
            pipeline_id=pipeline.id,
            status=PipelineStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        self.active_executions[execution.id] = execution
        
        try:
            # Extract data from sources
            all_data = []
            for source in pipeline.sources:
                if not source.enabled:
                    continue
                
                source_data = await self.data_connector.read_data(source)
                all_data.extend(source_data)
            
            execution.records_processed = len(all_data)
            
            # Apply transformations
            transformed_data, transformation_errors = await self.data_transformer.apply_transformations(
                all_data, pipeline.transformations
            )
            
            execution.records_failed = len(transformation_errors)
            
            # Assess data quality
            quality_report = await self.quality_assessor.assess_quality(
                transformed_data, pipeline.id, execution.id
            )
            
            # Load data to targets
            load_success = True
            for target in pipeline.targets:
                if not target.enabled:
                    continue
                
                # Split data into batches
                batch_size = target.batch_size
                for i in range(0, len(transformed_data), batch_size):
                    batch = transformed_data[i:i + batch_size]
                    
                    success = await self.data_connector.write_data(target, batch)
                    if not success:
                        load_success = False
                        break
                
                if not load_success:
                    break
            
            # Update execution status
            if load_success and execution.records_failed == 0:
                execution.status = PipelineStatus.COMPLETED
            elif load_success:
                execution.status = PipelineStatus.COMPLETED
                execution.error_message = f"Completed with {execution.records_failed} transformation errors"
            else:
                execution.status = PipelineStatus.FAILED
                execution.error_message = "Failed to load data to targets"
            
            execution.completed_at = datetime.utcnow()
            execution.execution_metrics = {
                "sources_processed": len([s for s in pipeline.sources if s.enabled]),
                "transformations_applied": len([t for t in pipeline.transformations if t.enabled]),
                "targets_loaded": len([t for t in pipeline.targets if t.enabled]),
                "quality_score": quality_report.quality_score,
                "quality_level": quality_report.quality_level.value,
                "execution_time_seconds": (execution.completed_at - execution.started_at).total_seconds()
            }
        
        except Exception as e:
            execution.status = PipelineStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
        
        finally:
            if execution.id in self.active_executions:
                del self.active_executions[execution.id]
        
        return execution


class DataPipelineManager:
    """Main data pipeline management system."""
    
    def __init__(self):
        """Initialize pipeline manager."""
        self.pipelines: Dict[str, Pipeline] = {}
        self.executions: Dict[str, PipelineExecution] = {}
        self.executor = PipelineExecutor()
        self.scheduler_running = False
    
    # Pipeline Management
    async def create_pipeline(self, pipeline: Pipeline) -> str:
        """Create a new data pipeline."""
        self.pipelines[pipeline.id] = pipeline
        return pipeline.id
    
    async def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get pipeline by ID."""
        return self.pipelines.get(pipeline_id)
    
    async def list_pipelines(self) -> List[Pipeline]:
        """List all pipelines."""
        return list(self.pipelines.values())
    
    async def update_pipeline(self, pipeline: Pipeline) -> bool:
        """Update existing pipeline."""
        if pipeline.id in self.pipelines:
            pipeline.updated_at = datetime.utcnow()
            self.pipelines[pipeline.id] = pipeline
            return True
        return False
    
    async def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete pipeline."""
        if pipeline_id in self.pipelines:
            del self.pipelines[pipeline_id]
            return True
        return False
    
    # Pipeline Execution
    async def execute_pipeline(self, pipeline_id: str) -> Optional[PipelineExecution]:
        """Execute a pipeline."""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline or not pipeline.enabled:
            return None
        
        execution = await self.executor.execute_pipeline(pipeline)
        self.executions[execution.id] = execution
        
        # Update last run time
        pipeline.last_run = execution.started_at
        
        return execution
    
    async def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get execution by ID."""
        return self.executions.get(execution_id)
    
    async def list_executions(
        self,
        pipeline_id: Optional[str] = None,
        limit: int = 100
    ) -> List[PipelineExecution]:
        """List pipeline executions."""
        executions = list(self.executions.values())
        
        if pipeline_id:
            executions = [e for e in executions if e.pipeline_id == pipeline_id]
        
        # Sort by start time, newest first
        executions.sort(key=lambda x: x.started_at, reverse=True)
        
        return executions[:limit]
    
    # System Management
    async def get_system_status(self) -> Dict[str, Any]:
        """Get pipeline system status."""
        total_pipelines = len(self.pipelines)
        enabled_pipelines = len([p for p in self.pipelines.values() if p.enabled])
        
        # Execution statistics
        total_executions = len(self.executions)
        recent_executions = [
            e for e in self.executions.values()
            if e.started_at > datetime.utcnow() - timedelta(hours=24)
        ]
        
        successful_executions = len([e for e in recent_executions if e.status == PipelineStatus.COMPLETED])
        failed_executions = len([e for e in recent_executions if e.status == PipelineStatus.FAILED])
        
        return {
            "total_pipelines": total_pipelines,
            "enabled_pipelines": enabled_pipelines,
            "total_executions": total_executions,
            "recent_executions_24h": len(recent_executions),
            "successful_executions_24h": successful_executions,
            "failed_executions_24h": failed_executions,
            "active_executions": len(self.executor.active_executions),
            "scheduler_running": self.scheduler_running,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global pipeline manager instance
pipeline_manager = DataPipelineManager()


# Health check for data pipeline system
async def check_data_pipeline_health() -> Dict[str, Any]:
    """Check data pipeline system health."""
    status = await pipeline_manager.get_system_status()
    
    # Determine health status
    health_status = "healthy"
    
    if status["failed_executions_24h"] > status["successful_executions_24h"]:
        health_status = "degraded"
    
    if status["enabled_pipelines"] == 0:
        health_status = "warning"
    
    return {
        "status": health_status,
        "system_status": status,
        "data_connector_connections": len(pipeline_manager.executor.data_connector.connections),
        "transformer_functions": len(pipeline_manager.executor.data_transformer.custom_functions)
    }