"""GraphQL Federation support for microservices architecture."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import strawberry
from strawberry.federation import Schema

from app.core.monitoring import monitor_performance


class SubgraphStatus(str, Enum):
    """Subgraph health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class SubgraphConfig:
    """Subgraph configuration."""
    name: str
    url: str
    schema_url: str
    version: str = "1.0.0"
    timeout: int = 30
    retry_count: int = 3
    headers: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    health_check_interval: int = 60  # seconds


@dataclass
class SubgraphMetrics:
    """Subgraph performance metrics."""
    name: str
    status: SubgraphStatus
    response_time_ms: float
    success_rate: float
    error_count: int
    last_check: datetime
    uptime_percentage: float = 100.0
    schema_version: str = "1.0.0"


@dataclass
class FederationConfig:
    """GraphQL Federation configuration."""
    gateway_name: str = "ITDO_ERP_Gateway"
    subgraphs: List[SubgraphConfig] = field(default_factory=list)
    composition_cache_ttl: int = 300  # 5 minutes
    schema_validation_enabled: bool = True
    introspection_enabled: bool = True
    query_planning_cache_size: int = 1000
    federation_version: str = "2.0"


class SubgraphRegistry:
    """Registry for managing GraphQL subgraphs."""
    
    def __init__(self, config: FederationConfig):
        """Initialize subgraph registry."""
        self.config = config
        self.subgraphs: Dict[str, SubgraphConfig] = {}
        self.metrics: Dict[str, SubgraphMetrics] = {}
        self.schemas: Dict[str, str] = {}  # Cached schemas
        self.composition_cache: Optional[str] = None
        self.last_composition: Optional[datetime] = None
        
        # Initialize with configured subgraphs
        for subgraph in config.subgraphs:
            self.register_subgraph(subgraph)
    
    def register_subgraph(self, subgraph: SubgraphConfig) -> None:
        """Register a new subgraph."""
        self.subgraphs[subgraph.name] = subgraph
        self.metrics[subgraph.name] = SubgraphMetrics(
            name=subgraph.name,
            status=SubgraphStatus.UNKNOWN,
            response_time_ms=0.0,
            success_rate=0.0,
            error_count=0,
            last_check=datetime.utcnow()
        )
    
    def unregister_subgraph(self, name: str) -> bool:
        """Unregister a subgraph."""
        if name in self.subgraphs:
            del self.subgraphs[name]
            if name in self.metrics:
                del self.metrics[name]
            if name in self.schemas:
                del self.schemas[name]
            # Invalidate composition cache
            self.composition_cache = None
            return True
        return False
    
    @monitor_performance("graphql.federation.fetch_schema")
    async def fetch_subgraph_schema(self, name: str) -> Optional[str]:
        """Fetch schema from a subgraph."""
        subgraph = self.subgraphs.get(name)
        if not subgraph or not subgraph.enabled:
            return None
        
        try:
            # Simulate schema fetching (would use HTTP client in production)
            await asyncio.sleep(0.1)
            
            # Mock schema based on subgraph name
            schema = self._generate_mock_schema(name)
            self.schemas[name] = schema
            
            # Update metrics
            self.metrics[name].status = SubgraphStatus.HEALTHY
            self.metrics[name].last_check = datetime.utcnow()
            
            return schema
        
        except Exception as e:
            self.metrics[name].status = SubgraphStatus.UNHEALTHY
            self.metrics[name].error_count += 1
            return None
    
    def _generate_mock_schema(self, name: str) -> str:
        """Generate mock schema for subgraph."""
        base_schema = f"""
        # {name} subgraph schema
        
        directive @key(fields: String!) on OBJECT | INTERFACE
        directive @external on FIELD_DEFINITION
        directive @requires(fields: String!) on FIELD_DEFINITION
        directive @provides(fields: String!) on FIELD_DEFINITION
        
        type Query {{
            {name.lower()}Health: String
        }}
        """
        
        if name == "users":
            return base_schema + """
            extend type Query {
                users: [User!]!
                user(id: ID!): User
            }
            
            type User @key(fields: "id") {
                id: ID!
                email: String!
                name: String!
                organization: Organization @external
            }
            """
        elif name == "organizations":
            return base_schema + """
            extend type Query {
                organizations: [Organization!]!
                organization(id: ID!): Organization
            }
            
            type Organization @key(fields: "id") {
                id: ID!
                name: String!
                domain: String!
                users: [User!]! @external
            }
            """
        elif name == "tasks":
            return base_schema + """
            extend type Query {
                tasks: [Task!]!
                task(id: ID!): Task
            }
            
            type Task @key(fields: "id") {
                id: ID!
                title: String!
                description: String
                assignee: User @external
                project: Project @external
            }
            """
        
        return base_schema
    
    @monitor_performance("graphql.federation.compose_schema")
    async def compose_federated_schema(self) -> Optional[str]:
        """Compose federated schema from all subgraphs."""
        # Check cache validity
        if (self.composition_cache and self.last_composition and
            (datetime.utcnow() - self.last_composition).total_seconds() < self.config.composition_cache_ttl):
            return self.composition_cache
        
        # Fetch all subgraph schemas
        schemas = {}
        for name in self.subgraphs:
            schema = await self.fetch_subgraph_schema(name)
            if schema:
                schemas[name] = schema
        
        if not schemas:
            return None
        
        # Compose federated schema (simplified)
        composed_schema = self._compose_schemas(schemas)
        
        # Cache result
        self.composition_cache = composed_schema
        self.last_composition = datetime.utcnow()
        
        return composed_schema
    
    def _compose_schemas(self, schemas: Dict[str, str]) -> str:
        """Compose multiple schemas into a federated schema."""
        # This is a simplified composition - production would use proper federation tools
        
        composed_types = set()
        composed_queries = []
        composed_mutations = []
        
        header = """
        # Federated GraphQL Schema
        # Generated at: """ + datetime.utcnow().isoformat() + """
        
        directive @key(fields: String!) on OBJECT | INTERFACE
        directive @external on FIELD_DEFINITION
        directive @requires(fields: String!) on FIELD_DEFINITION
        directive @provides(fields: String!) on FIELD_DEFINITION
        
        """
        
        # Extract and merge types
        for name, schema in schemas.items():
            lines = schema.split('\n')
            in_type = False
            current_type = []
            
            for line in lines:
                stripped = line.strip()
                
                if stripped.startswith('type ') and not stripped.startswith('type Query'):
                    in_type = True
                    current_type = [line]
                elif in_type and stripped == '}':
                    current_type.append(line)
                    type_def = '\n'.join(current_type)
                    composed_types.add(type_def)
                    in_type = False
                    current_type = []
                elif in_type:
                    current_type.append(line)
                elif 'extend type Query' in stripped or stripped.startswith('Query {'):
                    # Extract query fields
                    pass  # Simplified for this mock
        
        # Combine everything
        composed_schema = header + '\n'.join(composed_types) + """
        
        type Query {
            _service: _Service!
            _entities(representations: [_Any!]!): [_Entity]!
            health: String!
        }
        
        type _Service {
            sdl: String
        }
        
        scalar _Any
        union _Entity = User | Organization | Task
        """
        
        return composed_schema
    
    async def health_check_subgraph(self, name: str) -> SubgraphMetrics:
        """Perform health check on a specific subgraph."""
        subgraph = self.subgraphs.get(name)
        if not subgraph:
            raise ValueError(f"Subgraph {name} not found")
        
        start_time = datetime.utcnow()
        
        try:
            # Simulate health check
            await asyncio.sleep(0.05)
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Update metrics
            metrics = self.metrics[name]
            metrics.status = SubgraphStatus.HEALTHY
            metrics.response_time_ms = response_time
            metrics.last_check = end_time
            metrics.success_rate = min(100.0, metrics.success_rate + 1.0)
            
            return metrics
        
        except Exception as e:
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            metrics = self.metrics[name]
            metrics.status = SubgraphStatus.UNHEALTHY
            metrics.response_time_ms = response_time
            metrics.last_check = end_time
            metrics.error_count += 1
            metrics.success_rate = max(0.0, metrics.success_rate - 5.0)
            
            return metrics
    
    async def health_check_all_subgraphs(self) -> Dict[str, SubgraphMetrics]:
        """Perform health check on all subgraphs."""
        tasks = [
            self.health_check_subgraph(name)
            for name in self.subgraphs
            if self.subgraphs[name].enabled
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_status = {}
        for i, result in enumerate(results):
            name = list(self.subgraphs.keys())[i]
            if isinstance(result, Exception):
                # Create error metrics
                metrics = self.metrics[name]
                metrics.status = SubgraphStatus.UNHEALTHY
                metrics.error_count += 1
                health_status[name] = metrics
            else:
                health_status[name] = result
        
        return health_status
    
    def get_federation_status(self) -> Dict[str, Any]:
        """Get overall federation status."""
        total_subgraphs = len(self.subgraphs)
        healthy_subgraphs = len([
            m for m in self.metrics.values()
            if m.status == SubgraphStatus.HEALTHY
        ])
        
        overall_status = "healthy"
        if healthy_subgraphs == 0:
            overall_status = "unhealthy"
        elif healthy_subgraphs < total_subgraphs:
            overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "total_subgraphs": total_subgraphs,
            "healthy_subgraphs": healthy_subgraphs,
            "federation_version": self.config.federation_version,
            "last_composition": self.last_composition.isoformat() if self.last_composition else None,
            "schema_cached": self.composition_cache is not None,
            "subgraph_metrics": {
                name: {
                    "status": metrics.status.value,
                    "response_time_ms": metrics.response_time_ms,
                    "success_rate": metrics.success_rate,
                    "error_count": metrics.error_count,
                    "uptime_percentage": metrics.uptime_percentage
                }
                for name, metrics in self.metrics.items()
            }
        }


# Global federation registry instance
federation_config = FederationConfig(
    subgraphs=[
        SubgraphConfig(
            name="users",
            url="http://localhost:8001/graphql",
            schema_url="http://localhost:8001/graphql/schema"
        ),
        SubgraphConfig(
            name="organizations", 
            url="http://localhost:8002/graphql",
            schema_url="http://localhost:8002/graphql/schema"
        ),
        SubgraphConfig(
            name="tasks",
            url="http://localhost:8003/graphql", 
            schema_url="http://localhost:8003/graphql/schema"
        )
    ]
)

federation_registry = SubgraphRegistry(federation_config)


# Health check for federation system
async def check_graphql_federation_health() -> Dict[str, Any]:
    """Check GraphQL federation system health."""
    health_status = await federation_registry.health_check_all_subgraphs()
    federation_status = federation_registry.get_federation_status()
    
    return {
        "status": federation_status["overall_status"],
        "federation_info": federation_status,
        "composition_cached": federation_status["schema_cached"],
        "subgraph_count": federation_status["total_subgraphs"],
        "healthy_subgraphs": federation_status["healthy_subgraphs"]
    }