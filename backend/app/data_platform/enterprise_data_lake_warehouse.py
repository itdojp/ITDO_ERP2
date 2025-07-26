"""
CC02 v79.0 Day 24: Enterprise Integrated Data Platform & Analytics
Module 1: Enterprise Data Lake & Data Warehouse

Advanced enterprise data lake and data warehouse platform with multi-format support,
intelligent data partitioning, automated optimization, and hybrid analytics architecture.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from delta import *
from sqlalchemy import create_engine, text

from ..core.mobile_erp_sdk import MobileERPSDK


class DataFormat(Enum):
    """Supported data formats"""

    PARQUET = "parquet"
    DELTA = "delta"
    JSON = "json"
    CSV = "csv"
    AVRO = "avro"
    ORC = "orc"
    ICEBERG = "iceberg"


class CompressionType(Enum):
    """Compression algorithms"""

    SNAPPY = "snappy"
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"
    BROTLI = "brotli"


class PartitionStrategy(Enum):
    """Data partitioning strategies"""

    DATE = "date"
    HASH = "hash"
    RANGE = "range"
    ROUND_ROBIN = "round_robin"
    CUSTOM = "custom"


class StorageTier(Enum):
    """Storage tier classifications"""

    HOT = "hot"  # Frequently accessed
    WARM = "warm"  # Occasionally accessed
    COLD = "cold"  # Rarely accessed
    ARCHIVE = "archive"  # Long-term storage


class DataQuality(Enum):
    """Data quality levels"""

    RAW = "raw"  # Unprocessed data
    BRONZE = "bronze"  # Basic cleaning applied
    SILVER = "silver"  # Structured and validated
    GOLD = "gold"  # Business-ready analytics


@dataclass
class DataSchema:
    """Data schema definition"""

    name: str
    version: str
    fields: List[Dict[str, Any]]
    primary_keys: List[str] = field(default_factory=list)
    partition_keys: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class DataTable:
    """Data table definition"""

    id: str
    name: str
    schema: DataSchema
    format: DataFormat
    location: str
    partition_strategy: PartitionStrategy
    storage_tier: StorageTier
    quality_tier: DataQuality
    compression: CompressionType = CompressionType.SNAPPY
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DataPartition:
    """Data partition definition"""

    id: str
    table_id: str
    partition_path: str
    partition_values: Dict[str, Any]
    size_bytes: int
    row_count: int
    created_at: datetime
    last_accessed: Optional[datetime] = None
    compression_ratio: float = 1.0


@dataclass
class DataOperation:
    """Data operation tracking"""

    id: str
    operation_type: str
    table_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    affected_partitions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class SchemaManager:
    """Advanced schema management system"""

    def __init__(self) -> dict:
        self.schemas: Dict[str, DataSchema] = {}
        self.schema_evolution_history: List[Dict[str, Any]] = []
        self.schema_registry_enabled = True

    def register_schema(self, schema: DataSchema) -> bool:
        """Register new data schema"""
        try:
            # Validate schema
            if not self._validate_schema(schema):
                return False

            # Check for conflicts
            if schema.name in self.schemas:
                existing_schema = self.schemas[schema.name]
                if not self._is_compatible_schema(existing_schema, schema):
                    logging.error(f"Schema conflict detected: {schema.name}")
                    return False

                # Record evolution
                self.schema_evolution_history.append(
                    {
                        "schema_name": schema.name,
                        "old_version": existing_schema.version,
                        "new_version": schema.version,
                        "timestamp": datetime.now(),
                        "changes": self._get_schema_changes(existing_schema, schema),
                    }
                )

            self.schemas[schema.name] = schema
            logging.info(f"Schema registered: {schema.name} v{schema.version}")
            return True

        except Exception as e:
            logging.error(f"Schema registration failed: {e}")
            return False

    def _validate_schema(self, schema: DataSchema) -> bool:
        """Validate schema definition"""
        # Check required fields
        if not schema.name or not schema.version or not schema.fields:
            return False

        # Validate field definitions
        for field in schema.fields:
            if not all(key in field for key in ["name", "type"]):
                return False

        # Validate primary keys exist in fields
        field_names = {field["name"] for field in schema.fields}
        for pk in schema.primary_keys:
            if pk not in field_names:
                return False

        return True

    def _is_compatible_schema(
        self, old_schema: DataSchema, new_schema: DataSchema
    ) -> bool:
        """Check if schema evolution is compatible"""
        old_fields = {field["name"]: field for field in old_schema.fields}
        new_fields = {field["name"]: field for field in new_schema.fields}

        # Check for removed required fields
        for field_name, field in old_fields.items():
            if field_name not in new_fields:
                if not field.get("nullable", True):
                    return False  # Cannot remove required field

        # Check for type changes
        for field_name, new_field in new_fields.items():
            if field_name in old_fields:
                old_field = old_fields[field_name]
                if not self._are_types_compatible(old_field["type"], new_field["type"]):
                    return False

        return True

    def _are_types_compatible(self, old_type: str, new_type: str) -> bool:
        """Check if data types are compatible for evolution"""
        # Define compatible type transitions
        compatible_transitions = {
            "int": ["bigint", "float", "double", "string"],
            "bigint": ["float", "double", "string"],
            "float": ["double", "string"],
            "string": ["string"],  # String can only stay string
            "boolean": ["string"],
            "date": ["timestamp", "string"],
            "timestamp": ["string"],
        }

        return new_type in compatible_transitions.get(old_type, [])

    def _get_schema_changes(
        self, old_schema: DataSchema, new_schema: DataSchema
    ) -> List[Dict[str, Any]]:
        """Get list of changes between schema versions"""
        changes = []

        old_fields = {field["name"]: field for field in old_schema.fields}
        new_fields = {field["name"]: field for field in new_schema.fields}

        # Added fields
        for field_name, field in new_fields.items():
            if field_name not in old_fields:
                changes.append(
                    {
                        "type": "field_added",
                        "field_name": field_name,
                        "field_definition": field,
                    }
                )

        # Removed fields
        for field_name, field in old_fields.items():
            if field_name not in new_fields:
                changes.append(
                    {
                        "type": "field_removed",
                        "field_name": field_name,
                        "field_definition": field,
                    }
                )

        # Modified fields
        for field_name, new_field in new_fields.items():
            if field_name in old_fields:
                old_field = old_fields[field_name]
                if old_field != new_field:
                    changes.append(
                        {
                            "type": "field_modified",
                            "field_name": field_name,
                            "old_definition": old_field,
                            "new_definition": new_field,
                        }
                    )

        return changes

    def get_schema(
        self, name: str, version: Optional[str] = None
    ) -> Optional[DataSchema]:
        """Get schema by name and optional version"""
        if name not in self.schemas:
            return None

        schema = self.schemas[name]

        if version and schema.version != version:
            # Look for specific version in history
            for evolution in self.schema_evolution_history:
                if (
                    evolution["schema_name"] == name
                    and evolution["new_version"] == version
                ):
                    # Would need to reconstruct schema from history
                    # Simplified implementation returns latest
                    break

        return schema

    def get_schema_evolution(self, name: str) -> List[Dict[str, Any]]:
        """Get schema evolution history"""
        return [
            evolution
            for evolution in self.schema_evolution_history
            if evolution["schema_name"] == name
        ]


class DataLakeStorage:
    """Enterprise data lake storage system"""

    def __init__(self, base_path: str = "/data/lake") -> dict:
        self.base_path = Path(base_path)
        self.tables: Dict[str, DataTable] = {}
        self.partitions: Dict[str, List[DataPartition]] = {}
        self.storage_stats: Dict[str, Dict[str, Any]] = {}

    def create_table(self, table: DataTable) -> bool:
        """Create new data table"""
        try:
            # Create table directory structure
            table_path = self.base_path / table.name
            table_path.mkdir(parents=True, exist_ok=True)

            # Initialize table metadata
            self.tables[table.id] = table
            self.partitions[table.id] = []

            # Create table metadata file
            metadata_path = table_path / "_metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(
                    {
                        "table_id": table.id,
                        "name": table.name,
                        "schema": {
                            "name": table.schema.name,
                            "version": table.schema.version,
                            "fields": table.schema.fields,
                        },
                        "format": table.format.value,
                        "partition_strategy": table.partition_strategy.value,
                        "created_at": table.created_at.isoformat(),
                    },
                    f,
                    indent=2,
                )

            logging.info(f"Table created: {table.name}")
            return True

        except Exception as e:
            logging.error(f"Table creation failed: {e}")
            return False

    def write_data(
        self,
        table_id: str,
        data: pd.DataFrame,
        partition_values: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Write data to table with automatic partitioning"""
        try:
            if table_id not in self.tables:
                raise ValueError(f"Table not found: {table_id}")

            table = self.tables[table_id]

            # Generate partition if not provided
            if partition_values is None:
                partition_values = self._generate_partition_values(table, data)

            # Create partition path
            partition_path = self._create_partition_path(table, partition_values)
            full_partition_path = self.base_path / table.name / partition_path
            full_partition_path.mkdir(parents=True, exist_ok=True)

            # Write data based on format
            if table.format == DataFormat.PARQUET:
                file_path = full_partition_path / f"data_{uuid.uuid4().hex}.parquet"
                data.to_parquet(file_path, compression=table.compression.value)

            elif table.format == DataFormat.DELTA:
                # Delta Lake format
                delta_table_path = str(full_partition_path)
                data.write.format("delta").mode("append").save(delta_table_path)

            elif table.format == DataFormat.JSON:
                file_path = full_partition_path / f"data_{uuid.uuid4().hex}.json"
                data.to_json(file_path, orient="records", lines=True)

            elif table.format == DataFormat.CSV:
                file_path = full_partition_path / f"data_{uuid.uuid4().hex}.csv"
                data.to_csv(file_path, index=False)

            # Create partition record
            partition = DataPartition(
                id=f"{table_id}_{hashlib.md5(str(partition_values).encode()).hexdigest()}",
                table_id=table_id,
                partition_path=partition_path,
                partition_values=partition_values,
                size_bytes=self._calculate_partition_size(full_partition_path),
                row_count=len(data),
                created_at=datetime.now(),
            )

            self.partitions[table_id].append(partition)

            # Update table metadata
            table.last_updated = datetime.now()

            logging.info(
                f"Data written to table {table.name}, partition: {partition_path}"
            )
            return True

        except Exception as e:
            logging.error(f"Data write failed: {e}")
            return False

    def read_data(
        self,
        table_id: str,
        partition_filter: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
    ) -> Optional[pd.DataFrame]:
        """Read data from table with optional filtering"""
        try:
            if table_id not in self.tables:
                raise ValueError(f"Table not found: {table_id}")

            table = self.tables[table_id]
            relevant_partitions = self._filter_partitions(table_id, partition_filter)

            if not relevant_partitions:
                return pd.DataFrame()

            dataframes = []

            for partition in relevant_partitions:
                partition_path = self.base_path / table.name / partition.partition_path

                if table.format == DataFormat.PARQUET:
                    df = pd.read_parquet(partition_path, columns=columns)
                elif table.format == DataFormat.DELTA:
                    # Delta Lake read
                    df = spark.read.format("delta").load(str(partition_path)).toPandas()
                    if columns:
                        df = df[columns]
                elif table.format == DataFormat.JSON:
                    df = pd.read_json(partition_path, lines=True)
                    if columns:
                        df = df[columns]
                elif table.format == DataFormat.CSV:
                    df = pd.read_csv(partition_path)
                    if columns:
                        df = df[columns]
                else:
                    continue

                dataframes.append(df)

                # Update access time
                partition.last_accessed = datetime.now()

            if dataframes:
                return pd.concat(dataframes, ignore_index=True)
            else:
                return pd.DataFrame()

        except Exception as e:
            logging.error(f"Data read failed: {e}")
            return None

    def _generate_partition_values(
        self, table: DataTable, data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate partition values based on strategy"""
        if table.partition_strategy == PartitionStrategy.DATE:
            # Use current date for date partitioning
            now = datetime.now()
            return {"year": now.year, "month": now.month, "day": now.day}
        elif table.partition_strategy == PartitionStrategy.HASH:
            # Use hash of primary key values
            if table.schema.primary_keys:
                pk_cols = [
                    col for col in table.schema.primary_keys if col in data.columns
                ]
                if pk_cols:
                    hash_input = str(data[pk_cols].iloc[0].to_dict())
                    hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
                    return {"hash_partition": hash_value}
        elif table.partition_strategy == PartitionStrategy.RANGE:
            # Range partitioning (simplified)
            if table.schema.partition_keys:
                pk = table.schema.partition_keys[0]
                if pk in data.columns:
                    min_val = data[pk].min()
                    max_val = data[pk].max()
                    return {"range_start": min_val, "range_end": max_val}

        # Default: single partition
        return {"partition": "default"}

    def _create_partition_path(
        self, table: DataTable, partition_values: Dict[str, Any]
    ) -> str:
        """Create partition directory path"""
        path_parts = []

        for key, value in partition_values.items():
            path_parts.append(f"{key}={value}")

        return "/".join(path_parts)

    def _filter_partitions(
        self, table_id: str, partition_filter: Optional[Dict[str, Any]]
    ) -> List[DataPartition]:
        """Filter partitions based on criteria"""
        if table_id not in self.partitions:
            return []

        partitions = self.partitions[table_id]

        if not partition_filter:
            return partitions

        filtered_partitions = []

        for partition in partitions:
            match = True
            for key, value in partition_filter.items():
                if key not in partition.partition_values:
                    match = False
                    break
                if partition.partition_values[key] != value:
                    match = False
                    break

            if match:
                filtered_partitions.append(partition)

        return filtered_partitions

    def _calculate_partition_size(self, partition_path: Path) -> int:
        """Calculate partition size in bytes"""
        total_size = 0

        for file_path in partition_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    def optimize_table(self, table_id: str) -> bool:
        """Optimize table storage and performance"""
        try:
            if table_id not in self.tables:
                return False

            table = self.tables[table_id]
            partitions = self.partitions[table_id]

            # Analyze partition sizes
            small_partitions = [
                p for p in partitions if p.size_bytes < 100 * 1024 * 1024
            ]  # < 100MB

            if len(small_partitions) > 10:
                # Compact small partitions
                await self._compact_partitions(table, small_partitions)

            # Update statistics
            self._update_table_statistics(table_id)

            logging.info(f"Table optimization completed: {table.name}")
            return True

        except Exception as e:
            logging.error(f"Table optimization failed: {e}")
            return False

    async def _compact_partitions(
        self, table: DataTable, partitions: List[DataPartition]
    ):
        """Compact small partitions into larger ones"""
        # Group partitions by common partition keys
        partition_groups = {}

        for partition in partitions:
            # Create grouping key (exclude specific date/time parts)
            group_key = tuple(
                sorted(
                    [
                        (k, v)
                        for k, v in partition.partition_values.items()
                        if k not in ["hour", "minute"]
                    ]
                )
            )

            if group_key not in partition_groups:
                partition_groups[group_key] = []
            partition_groups[group_key].append(partition)

        # Compact each group
        for group_key, group_partitions in partition_groups.items():
            if len(group_partitions) > 1:
                await self._merge_partitions(table, group_partitions)

    async def _merge_partitions(
        self, table: DataTable, partitions: List[DataPartition]
    ):
        """Merge multiple partitions into one"""
        # Read data from all partitions
        dataframes = []

        for partition in partitions:
            partition_path = self.base_path / table.name / partition.partition_path

            if table.format == DataFormat.PARQUET:
                df = pd.read_parquet(partition_path)
            elif table.format == DataFormat.JSON:
                df = pd.read_json(partition_path, lines=True)
            elif table.format == DataFormat.CSV:
                df = pd.read_csv(partition_path)
            else:
                continue

            dataframes.append(df)

        if not dataframes:
            return

        # Merge data
        merged_data = pd.concat(dataframes, ignore_index=True)

        # Create new merged partition
        merged_partition_values = partitions[0].partition_values.copy()
        merged_partition_values["merged"] = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Write merged data
        self.write_data(table.id, merged_data, merged_partition_values)

        # Remove old partitions
        for partition in partitions:
            self._remove_partition(table, partition)

    def _remove_partition(self, table: DataTable, partition: DataPartition) -> dict:
        """Remove partition from storage and metadata"""
        partition_path = self.base_path / table.name / partition.partition_path

        # Remove files
        if partition_path.exists():
            import shutil

            shutil.rmtree(partition_path)

        # Remove from metadata
        if table.id in self.partitions:
            self.partitions[table.id] = [
                p for p in self.partitions[table.id] if p.id != partition.id
            ]

    def _update_table_statistics(self, table_id: str) -> dict:
        """Update table statistics"""
        if table_id not in self.tables:
            return

        self.tables[table_id]
        partitions = self.partitions.get(table_id, [])

        total_size = sum(p.size_bytes for p in partitions)
        total_rows = sum(p.row_count for p in partitions)

        self.storage_stats[table_id] = {
            "total_size_bytes": total_size,
            "total_rows": total_rows,
            "partition_count": len(partitions),
            "avg_partition_size": total_size / len(partitions) if partitions else 0,
            "last_updated": datetime.now(),
        }

    def get_table_info(self, table_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive table information"""
        if table_id not in self.tables:
            return None

        table = self.tables[table_id]
        partitions = self.partitions.get(table_id, [])
        stats = self.storage_stats.get(table_id, {})

        return {
            "table": {
                "id": table.id,
                "name": table.name,
                "format": table.format.value,
                "partition_strategy": table.partition_strategy.value,
                "storage_tier": table.storage_tier.value,
                "quality_tier": table.quality_tier.value,
                "created_at": table.created_at,
                "last_updated": table.last_updated,
            },
            "schema": {
                "name": table.schema.name,
                "version": table.schema.version,
                "field_count": len(table.schema.fields),
            },
            "partitions": {
                "count": len(partitions),
                "size_bytes": sum(p.size_bytes for p in partitions),
                "row_count": sum(p.row_count for p in partitions),
            },
            "statistics": stats,
        }


class DataWarehouse:
    """Enterprise data warehouse system"""

    def __init__(self, connection_string: str) -> dict:
        self.engine = create_engine(connection_string)
        self.tables: Dict[str, Dict[str, Any]] = {}
        self.materialized_views: Dict[str, Dict[str, Any]] = {}
        self.aggregation_jobs: Dict[str, Dict[str, Any]] = {}

    def create_dimensional_model(
        self,
        model_name: str,
        fact_table: Dict[str, Any],
        dimension_tables: List[Dict[str, Any]],
    ) -> bool:
        """Create dimensional data model (star/snowflake schema)"""
        try:
            with self.engine.begin() as conn:
                # Create fact table
                self._create_fact_table(conn, fact_table)

                # Create dimension tables
                for dim_table in dimension_tables:
                    self._create_dimension_table(conn, dim_table)

                # Create relationships
                self._create_foreign_keys(conn, fact_table, dimension_tables)

            self.tables[model_name] = {
                "fact_table": fact_table,
                "dimension_tables": dimension_tables,
                "created_at": datetime.now(),
            }

            logging.info(f"Dimensional model created: {model_name}")
            return True

        except Exception as e:
            logging.error(f"Dimensional model creation failed: {e}")
            return False

    def _create_fact_table(self, conn, fact_table: Dict[str, Any]) -> dict:
        """Create fact table with measures and foreign keys"""
        table_name = fact_table["name"]
        columns = fact_table["columns"]

        # Build CREATE TABLE statement
        col_definitions = []
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            if col.get("primary_key"):
                col_def += " PRIMARY KEY"
            if not col.get("nullable", True):
                col_def += " NOT NULL"
            col_definitions.append(col_def)

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {", ".join(col_definitions)}
        )
        """

        conn.execute(text(create_sql))

    def _create_dimension_table(self, conn, dim_table: Dict[str, Any]) -> dict:
        """Create dimension table with attributes"""
        table_name = dim_table["name"]
        columns = dim_table["columns"]

        # Build CREATE TABLE statement
        col_definitions = []
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            if col.get("primary_key"):
                col_def += " PRIMARY KEY"
            if not col.get("nullable", True):
                col_def += " NOT NULL"
            col_definitions.append(col_def)

        # Add SCD Type 2 columns if specified
        if dim_table.get("scd_type") == 2:
            col_definitions.extend(
                [
                    "valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "valid_to TIMESTAMP",
                    "is_current BOOLEAN DEFAULT TRUE",
                ]
            )

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {", ".join(col_definitions)}
        )
        """

        conn.execute(text(create_sql))

    def _create_foreign_keys(
        self, conn, fact_table: Dict[str, Any], dimension_tables: List[Dict[str, Any]]
    ):
        """Create foreign key relationships"""
        fact_name = fact_table["name"]

        for dim_table in dimension_tables:
            dim_name = dim_table["name"]

            # Find foreign key column in fact table
            fk_col = None
            for col in fact_table["columns"]:
                if col.get("references") == dim_name:
                    fk_col = col["name"]
                    break

            if fk_col:
                # Find primary key in dimension table
                pk_col = None
                for col in dim_table["columns"]:
                    if col.get("primary_key"):
                        pk_col = col["name"]
                        break

                if pk_col:
                    fk_sql = f"""
                    ALTER TABLE {fact_name}
                    ADD CONSTRAINT fk_{fact_name}_{dim_name}
                    FOREIGN KEY ({fk_col}) REFERENCES {dim_name}({pk_col})
                    """

                    try:
                        conn.execute(text(fk_sql))
                    except Exception as e:
                        # Foreign key might already exist
                        logging.warning(f"Foreign key creation warning: {e}")

    def create_materialized_view(
        self, view_name: str, query: str, refresh_schedule: Optional[str] = None
    ) -> bool:
        """Create materialized view for performance optimization"""
        try:
            with self.engine.begin() as conn:
                # Create materialized view
                create_sql = f"CREATE MATERIALIZED VIEW {view_name} AS {query}"
                conn.execute(text(create_sql))

                # Create indexes for performance
                self._create_view_indexes(conn, view_name, query)

            self.materialized_views[view_name] = {
                "query": query,
                "refresh_schedule": refresh_schedule,
                "created_at": datetime.now(),
                "last_refreshed": datetime.now(),
            }

            logging.info(f"Materialized view created: {view_name}")
            return True

        except Exception as e:
            logging.error(f"Materialized view creation failed: {e}")
            return False

    def _create_view_indexes(self, conn, view_name: str, query: str) -> dict:
        """Create indexes on materialized view based on query analysis"""
        # Analyze query to identify potential index columns
        # This is a simplified implementation

        # Common patterns for index creation
        if "GROUP BY" in query.upper():
            # Create index on GROUP BY columns
            # Extract columns (simplified)
            pass

        if "ORDER BY" in query.upper():
            # Create index on ORDER BY columns
            # Extract columns (simplified)
            pass

        # Create a default index on first column
        try:
            index_sql = f"CREATE INDEX idx_{view_name}_default ON {view_name} (1)"
            conn.execute(text(index_sql))
        except Exception:
            pass  # Index might already exist

    async def refresh_materialized_view(self, view_name: str) -> bool:
        """Refresh materialized view data"""
        try:
            if view_name not in self.materialized_views:
                return False

            with self.engine.begin() as conn:
                refresh_sql = f"REFRESH MATERIALIZED VIEW {view_name}"
                conn.execute(text(refresh_sql))

                # Update last refreshed timestamp
                self.materialized_views[view_name]["last_refreshed"] = datetime.now()

            logging.info(f"Materialized view refreshed: {view_name}")
            return True

        except Exception as e:
            logging.error(f"Materialized view refresh failed: {e}")
            return False

    def create_aggregation_job(
        self,
        job_name: str,
        source_table: str,
        target_table: str,
        aggregation_config: Dict[str, Any],
    ) -> bool:
        """Create data aggregation job"""
        try:
            job_config = {
                "source_table": source_table,
                "target_table": target_table,
                "aggregation_config": aggregation_config,
                "created_at": datetime.now(),
                "last_run": None,
                "status": "created",
            }

            # Create target table if it doesn't exist
            self._create_aggregation_table(target_table, aggregation_config)

            self.aggregation_jobs[job_name] = job_config

            logging.info(f"Aggregation job created: {job_name}")
            return True

        except Exception as e:
            logging.error(f"Aggregation job creation failed: {e}")
            return False

    def _create_aggregation_table(self, table_name: str, config: Dict[str, Any]) -> dict:
        """Create table for aggregated data"""
        try:
            with self.engine.begin() as conn:
                # Build table schema based on aggregation config
                columns = []

                # Add dimension columns
                for dim_col in config.get("dimensions", []):
                    columns.append(f"{dim_col} VARCHAR(255)")

                # Add measure columns
                for measure in config.get("measures", []):
                    col_name = f"{measure['function']}_{measure['column']}"
                    col_type = (
                        "DECIMAL(18,2)"
                        if measure["function"] in ["SUM", "AVG"]
                        else "INTEGER"
                    )
                    columns.append(f"{col_name} {col_type}")

                # Add metadata columns
                columns.extend(
                    [
                        "aggregation_date DATE",
                        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    ]
                )

                create_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {", ".join(columns)}
                )
                """

                conn.execute(text(create_sql))

        except Exception as e:
            logging.error(f"Aggregation table creation failed: {e}")

    async def run_aggregation_job(self, job_name: str) -> bool:
        """Execute aggregation job"""
        try:
            if job_name not in self.aggregation_jobs:
                return False

            job = self.aggregation_jobs[job_name]
            config = job["aggregation_config"]

            # Build aggregation query
            query = self._build_aggregation_query(
                job["source_table"], job["target_table"], config
            )

            with self.engine.begin() as conn:
                # Execute aggregation
                conn.execute(text(query))

                # Update job status
                job["last_run"] = datetime.now()
                job["status"] = "completed"

            logging.info(f"Aggregation job executed: {job_name}")
            return True

        except Exception as e:
            logging.error(f"Aggregation job execution failed: {e}")

            if job_name in self.aggregation_jobs:
                self.aggregation_jobs[job_name]["status"] = "failed"

            return False

    def _build_aggregation_query(
        self, source_table: str, target_table: str, config: Dict[str, Any]
    ) -> str:
        """Build SQL query for data aggregation"""
        dimensions = config.get("dimensions", [])
        measures = config.get("measures", [])
        filters = config.get("filters", [])

        # Build SELECT clause
        select_parts = []
        select_parts.extend(dimensions)

        for measure in measures:
            col_name = f"{measure['function']}_{measure['column']}"
            func_expr = f"{measure['function']}({measure['column']}) AS {col_name}"
            select_parts.append(func_expr)

        # Add metadata columns
        select_parts.extend(
            ["CURRENT_DATE AS aggregation_date", "CURRENT_TIMESTAMP AS created_at"]
        )

        # Build WHERE clause
        where_clause = ""
        if filters:
            where_conditions = []
            for filter_cond in filters:
                where_conditions.append(
                    f"{filter_cond['column']} {filter_cond['operator']} '{filter_cond['value']}'"
                )
            where_clause = f"WHERE {' AND '.join(where_conditions)}"

        # Build GROUP BY clause
        group_by_clause = ""
        if dimensions:
            group_by_clause = f"GROUP BY {', '.join(dimensions)}"

        # Construct final query
        query = f"""
        INSERT INTO {target_table} ({", ".join(select_parts.split(" AS ")[0] for part in select_parts)})
        SELECT {", ".join(select_parts)}
        FROM {source_table}
        {where_clause}
        {group_by_clause}
        """

        return query

    def get_warehouse_stats(self) -> Dict[str, Any]:
        """Get data warehouse statistics"""
        return {
            "dimensional_models": len(self.tables),
            "materialized_views": len(self.materialized_views),
            "aggregation_jobs": len(self.aggregation_jobs),
            "last_updated": datetime.now(),
        }


class EnterpriseDataLakeWarehouseSystem:
    """Main enterprise data lake and warehouse system"""

    def __init__(
        self,
        sdk: MobileERPSDK,
        lake_path: str = "/data/lake",
        warehouse_connection: str = "postgresql://localhost:5432/warehouse",
    ):
        self.sdk = sdk
        self.schema_manager = SchemaManager()
        self.data_lake = DataLakeStorage(lake_path)
        self.data_warehouse = DataWarehouse(warehouse_connection)

        # System configuration
        self.lake_enabled = True
        self.warehouse_enabled = True
        self.auto_optimization_enabled = True

        # Initialize default schemas and tables
        self._initialize_default_setup()

        logging.info("Enterprise Data Lake & Warehouse system initialized")

    def _initialize_default_setup(self) -> dict:
        """Initialize default schemas and data structures"""

        # Register sample schemas
        erp_transaction_schema = DataSchema(
            name="erp_transaction",
            version="1.0",
            fields=[
                {"name": "transaction_id", "type": "string", "nullable": False},
                {"name": "customer_id", "type": "string", "nullable": False},
                {"name": "product_id", "type": "string", "nullable": False},
                {"name": "amount", "type": "decimal", "nullable": False},
                {"name": "quantity", "type": "integer", "nullable": False},
                {"name": "transaction_date", "type": "timestamp", "nullable": False},
                {"name": "status", "type": "string", "nullable": False},
            ],
            primary_keys=["transaction_id"],
            partition_keys=["transaction_date"],
        )
        self.schema_manager.register_schema(erp_transaction_schema)

        # Create sample data lake table
        transaction_table = DataTable(
            id="tbl_transactions",
            name="transactions",
            schema=erp_transaction_schema,
            format=DataFormat.PARQUET,
            location="/data/lake/transactions",
            partition_strategy=PartitionStrategy.DATE,
            storage_tier=StorageTier.HOT,
            quality_tier=DataQuality.SILVER,
            compression=CompressionType.SNAPPY,
            tags={"domain": "finance", "criticality": "high"},
        )
        self.data_lake.create_table(transaction_table)

        # Create sample dimensional model in warehouse
        fact_sales = {
            "name": "fact_sales",
            "columns": [
                {"name": "sale_id", "type": "BIGINT", "primary_key": True},
                {
                    "name": "customer_key",
                    "type": "BIGINT",
                    "references": "dim_customer",
                },
                {"name": "product_key", "type": "BIGINT", "references": "dim_product"},
                {"name": "date_key", "type": "INTEGER", "references": "dim_date"},
                {"name": "quantity", "type": "INTEGER"},
                {"name": "unit_price", "type": "DECIMAL(10,2)"},
                {"name": "total_amount", "type": "DECIMAL(12,2)"},
                {"name": "created_at", "type": "TIMESTAMP"},
            ],
        }

        dim_customer = {
            "name": "dim_customer",
            "columns": [
                {"name": "customer_key", "type": "BIGINT", "primary_key": True},
                {"name": "customer_id", "type": "VARCHAR(50)"},
                {"name": "customer_name", "type": "VARCHAR(200)"},
                {"name": "customer_type", "type": "VARCHAR(50)"},
                {"name": "region", "type": "VARCHAR(100)"},
                {"name": "created_at", "type": "TIMESTAMP"},
            ],
            "scd_type": 2,
        }

        dim_product = {
            "name": "dim_product",
            "columns": [
                {"name": "product_key", "type": "BIGINT", "primary_key": True},
                {"name": "product_id", "type": "VARCHAR(50)"},
                {"name": "product_name", "type": "VARCHAR(200)"},
                {"name": "category", "type": "VARCHAR(100)"},
                {"name": "price", "type": "DECIMAL(10,2)"},
                {"name": "created_at", "type": "TIMESTAMP"},
            ],
        }

        dim_date = {
            "name": "dim_date",
            "columns": [
                {"name": "date_key", "type": "INTEGER", "primary_key": True},
                {"name": "date", "type": "DATE"},
                {"name": "year", "type": "INTEGER"},
                {"name": "quarter", "type": "INTEGER"},
                {"name": "month", "type": "INTEGER"},
                {"name": "day", "type": "INTEGER"},
                {"name": "day_of_week", "type": "INTEGER"},
                {"name": "is_weekend", "type": "BOOLEAN"},
            ],
        }

        self.data_warehouse.create_dimensional_model(
            "sales_analytics", fact_sales, [dim_customer, dim_product, dim_date]
        )

    async def ingest_data(
        self, table_id: str, data: pd.DataFrame, quality_checks: bool = True
    ) -> bool:
        """Ingest data into data lake with optional quality checks"""
        try:
            if quality_checks:
                # Perform data quality validation
                if not self._validate_data_quality(table_id, data):
                    logging.error("Data quality validation failed")
                    return False

            # Write to data lake
            success = self.data_lake.write_data(table_id, data)

            if success:
                logging.info(f"Data ingested successfully: {len(data)} rows")

                # Trigger optimization if enabled
                if self.auto_optimization_enabled:
                    await self._schedule_optimization(table_id)

            return success

        except Exception as e:
            logging.error(f"Data ingestion failed: {e}")
            return False

    def _validate_data_quality(self, table_id: str, data: pd.DataFrame) -> bool:
        """Validate data quality before ingestion"""
        if table_id not in self.data_lake.tables:
            return False

        table = self.data_lake.tables[table_id]
        schema = table.schema

        # Check required columns
        schema_fields = {field["name"] for field in schema.fields}
        data_columns = set(data.columns)

        missing_columns = schema_fields - data_columns
        if missing_columns:
            logging.error(f"Missing required columns: {missing_columns}")
            return False

        # Check data types
        for field in schema.fields:
            col_name = field["name"]
            expected_type = field["type"]

            if col_name in data.columns:
                if not self._validate_column_type(data[col_name], expected_type):
                    logging.error(f"Invalid data type for column {col_name}")
                    return False

        # Check for null values in non-nullable columns
        for field in schema.fields:
            if not field.get("nullable", True):
                col_name = field["name"]
                if col_name in data.columns and data[col_name].isnull().any():
                    logging.error(
                        f"Null values found in non-nullable column: {col_name}"
                    )
                    return False

        return True

    def _validate_column_type(self, column: pd.Series, expected_type: str) -> bool:
        """Validate column data type"""
        if expected_type == "string":
            return column.dtype == object or column.dtype.name.startswith("str")
        elif expected_type in ["integer", "bigint"]:
            return pd.api.types.is_integer_dtype(column)
        elif expected_type in ["decimal", "float", "double"]:
            return pd.api.types.is_numeric_dtype(column)
        elif expected_type == "boolean":
            return pd.api.types.is_bool_dtype(column)
        elif expected_type in ["date", "timestamp"]:
            return pd.api.types.is_datetime64_any_dtype(column)
        else:
            return True  # Unknown type, assume valid

    async def _schedule_optimization(self, table_id: str) -> dict:
        """Schedule table optimization"""
        # Create async task for optimization
        asyncio.create_task(self._optimize_table_async(table_id))

    async def _optimize_table_async(self, table_id: str) -> dict:
        """Asynchronously optimize table"""
        try:
            await asyncio.sleep(60)  # Wait before optimization
            self.data_lake.optimize_table(table_id)
        except Exception as e:
            logging.error(f"Async table optimization failed: {e}")

    async def sync_lake_to_warehouse(self, table_mapping: Dict[str, str]) -> bool:
        """Synchronize data from lake to warehouse"""
        try:
            for lake_table_id, warehouse_table in table_mapping.items():
                # Read data from lake
                data = self.data_lake.read_data(lake_table_id)

                if data is not None and not data.empty:
                    # Transform data for warehouse format
                    transformed_data = self._transform_for_warehouse(
                        data, warehouse_table
                    )

                    # Load into warehouse
                    self._load_to_warehouse(transformed_data, warehouse_table)

            logging.info("Lake to warehouse sync completed")
            return True

        except Exception as e:
            logging.error(f"Lake to warehouse sync failed: {e}")
            return False

    def _transform_for_warehouse(
        self, data: pd.DataFrame, target_table: str
    ) -> pd.DataFrame:
        """Transform data for warehouse loading"""
        # Apply business transformations
        transformed_data = data.copy()

        # Add derived columns if needed
        if target_table == "fact_sales":
            if "unit_price" in data.columns and "quantity" in data.columns:
                transformed_data["total_amount"] = data["unit_price"] * data["quantity"]

        # Add audit columns
        transformed_data["created_at"] = datetime.now()

        return transformed_data

    def _load_to_warehouse(self, data: pd.DataFrame, table_name: str) -> dict:
        """Load data into warehouse table"""
        try:
            data.to_sql(
                table_name,
                self.data_warehouse.engine,
                if_exists="append",
                index=False,
                method="multi",
            )
            logging.info(f"Data loaded to warehouse table: {table_name}")
        except Exception as e:
            logging.error(f"Warehouse loading failed: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        lake_stats = {
            "tables": len(self.data_lake.tables),
            "total_partitions": sum(
                len(partitions) for partitions in self.data_lake.partitions.values()
            ),
            "total_size_bytes": sum(
                sum(p.size_bytes for p in partitions)
                for partitions in self.data_lake.partitions.values()
            ),
        }

        warehouse_stats = self.data_warehouse.get_warehouse_stats()

        return {
            "timestamp": datetime.now(),
            "lake_enabled": self.lake_enabled,
            "warehouse_enabled": self.warehouse_enabled,
            "auto_optimization_enabled": self.auto_optimization_enabled,
            "schemas_registered": len(self.schema_manager.schemas),
            "data_lake": lake_stats,
            "data_warehouse": warehouse_stats,
        }


# Example usage and testing
async def main() -> None:
    """Example usage of the Enterprise Data Lake & Warehouse system"""

    # Initialize SDK (mock)
    class MockMobileERPSDK:
        pass

    sdk = MockMobileERPSDK()

    # Create data platform system
    data_platform = EnterpriseDataLakeWarehouseSystem(sdk)

    # Get initial system status
    status = data_platform.get_system_status()
    print(f"Initial Data Platform Status: {json.dumps(status, indent=2, default=str)}")

    # Generate sample transaction data
    sample_data = pd.DataFrame(
        {
            "transaction_id": [f"txn_{i:06d}" for i in range(1000)],
            "customer_id": [f"cust_{i % 100:03d}" for i in range(1000)],
            "product_id": [f"prod_{i % 50:03d}" for i in range(1000)],
            "amount": np.random.uniform(10, 1000, 1000).round(2),
            "quantity": np.random.randint(1, 10, 1000),
            "transaction_date": pd.date_range(
                start="2024-01-01", periods=1000, freq="H"
            ),
            "status": np.random.choice(["completed", "pending", "cancelled"], 1000),
        }
    )

    print(f"Generated sample data: {len(sample_data)} transactions")

    # Ingest data into lake
    print("Ingesting data into data lake...")
    success = await data_platform.ingest_data("tbl_transactions", sample_data)

    if success:
        print("Data ingestion successful")

        # Read data back from lake
        retrieved_data = data_platform.data_lake.read_data(
            "tbl_transactions",
            partition_filter={"year": 2024, "month": 1},
            columns=["transaction_id", "amount", "status"],
        )

        if retrieved_data is not None:
            print(f"Retrieved {len(retrieved_data)} records from data lake")

        # Sync to warehouse
        print("Syncing data to warehouse...")
        sync_success = await data_platform.sync_lake_to_warehouse(
            {"tbl_transactions": "fact_sales"}
        )

        if sync_success:
            print("Data sync to warehouse successful")

    # Get final system status
    final_status = data_platform.get_system_status()
    print(
        f"Final Data Platform Status: {json.dumps(final_status, indent=2, default=str)}"
    )

    print("Enterprise Data Lake & Warehouse demonstration completed")


if __name__ == "__main__":
    asyncio.run(main())
