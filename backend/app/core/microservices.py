"""Microservices foundation with service discovery and circuit breaker patterns."""

import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from uuid import uuid4

import httpx
import consul
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.monitoring import monitor_performance


class ServiceStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class ServiceInstance:
    """Represents a service instance in the registry."""
    service_id: str
    service_name: str
    host: str
    port: int
    version: str
    health_check_url: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    last_heartbeat: Optional[datetime] = None
    registration_time: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def address(self) -> str:
        """Get full service address."""
        return f"http://{self.host}:{self.port}"
    
    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status == ServiceStatus.HEALTHY
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "host": self.host,
            "port": self.port,
            "version": self.version,
            "health_check_url": self.health_check_url,
            "status": self.status,
            "metadata": self.metadata,
            "tags": self.tags,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "registration_time": self.registration_time.isoformat(),
            "address": self.address
        }


class ServiceRegistry(ABC):
    """Abstract service registry interface."""
    
    @abstractmethod
    async def register_service(self, service: ServiceInstance) -> bool:
        """Register a service instance."""
        pass
    
    @abstractmethod
    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service instance."""
        pass
    
    @abstractmethod
    async def discover_services(self, service_name: str) -> List[ServiceInstance]:
        """Discover healthy instances of a service."""
        pass
    
    @abstractmethod
    async def get_service(self, service_id: str) -> Optional[ServiceInstance]:
        """Get specific service instance."""
        pass
    
    @abstractmethod
    async def update_health(self, service_id: str, status: ServiceStatus) -> bool:
        """Update service health status."""
        pass
    
    @abstractmethod
    async def heartbeat(self, service_id: str) -> bool:
        """Send heartbeat for service."""
        pass


class InMemoryServiceRegistry(ServiceRegistry):
    """In-memory service registry for development/testing."""
    
    def __init__(self):
        """Initialize in-memory registry."""
        self.services: Dict[str, ServiceInstance] = {}
        self.service_names: Dict[str, Set[str]] = {}  # service_name -> set of service_ids
        self._lock = asyncio.Lock()
    
    async def register_service(self, service: ServiceInstance) -> bool:
        """Register a service instance."""
        async with self._lock:
            self.services[service.service_id] = service
            
            if service.service_name not in self.service_names:
                self.service_names[service.service_name] = set()
            self.service_names[service.service_name].add(service.service_id)
            
            return True
    
    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service instance."""
        async with self._lock:
            if service_id in self.services:
                service = self.services[service_id]
                del self.services[service_id]
                
                if service.service_name in self.service_names:
                    self.service_names[service.service_name].discard(service_id)
                    if not self.service_names[service.service_name]:
                        del self.service_names[service.service_name]
                
                return True
            return False
    
    async def discover_services(self, service_name: str) -> List[ServiceInstance]:
        """Discover healthy instances of a service."""
        async with self._lock:
            if service_name not in self.service_names:
                return []
            
            healthy_services = []
            for service_id in self.service_names[service_name]:
                if service_id in self.services:
                    service = self.services[service_id]
                    if service.is_healthy:
                        healthy_services.append(service)
            
            return healthy_services
    
    async def get_service(self, service_id: str) -> Optional[ServiceInstance]:
        """Get specific service instance."""
        async with self._lock:
            return self.services.get(service_id)
    
    async def update_health(self, service_id: str, status: ServiceStatus) -> bool:
        """Update service health status."""
        async with self._lock:
            if service_id in self.services:
                self.services[service_id].status = status
                return True
            return False
    
    async def heartbeat(self, service_id: str) -> bool:
        """Send heartbeat for service."""
        async with self._lock:
            if service_id in self.services:
                self.services[service_id].last_heartbeat = datetime.utcnow()
                return True
            return False
    
    async def get_all_services(self) -> List[ServiceInstance]:
        """Get all registered services."""
        async with self._lock:
            return list(self.services.values())


class ConsulServiceRegistry(ServiceRegistry):
    """Consul-based service registry."""
    
    def __init__(self, consul_host: str = "localhost", consul_port: int = 8500):
        """Initialize Consul registry."""
        self.consul = consul.Consul(host=consul_host, port=consul_port)
    
    async def register_service(self, service: ServiceInstance) -> bool:
        """Register a service with Consul."""
        try:
            check = consul.Check.http(
                url=f"{service.address}{service.health_check_url}",
                interval="10s",
                timeout="5s"
            )
            
            success = self.consul.agent.service.register(
                name=service.service_name,
                service_id=service.service_id,
                address=service.host,
                port=service.port,
                tags=service.tags,
                check=check,
                meta=service.metadata
            )
            
            return success
        except Exception as e:
            print(f"Failed to register service with Consul: {e}")
            return False
    
    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service from Consul."""
        try:
            success = self.consul.agent.service.deregister(service_id)
            return success
        except Exception as e:
            print(f"Failed to deregister service from Consul: {e}")
            return False
    
    async def discover_services(self, service_name: str) -> List[ServiceInstance]:
        """Discover healthy services from Consul."""
        try:
            _, services = self.consul.health.service(service_name, passing=True)
            
            instances = []
            for service_data in services:
                service_info = service_data['Service']
                
                instance = ServiceInstance(
                    service_id=service_info['ID'],
                    service_name=service_info['Service'],
                    host=service_info['Address'],
                    port=service_info['Port'],
                    version=service_info.get('Meta', {}).get('version', '1.0.0'),
                    health_check_url="/health",
                    status=ServiceStatus.HEALTHY,
                    metadata=service_info.get('Meta', {}),
                    tags=service_info.get('Tags', [])
                )
                instances.append(instance)
            
            return instances
        except Exception as e:
            print(f"Failed to discover services from Consul: {e}")
            return []
    
    async def get_service(self, service_id: str) -> Optional[ServiceInstance]:
        """Get specific service from Consul."""
        try:
            services = self.consul.agent.services()
            if service_id in services:
                service_info = services[service_id]
                
                return ServiceInstance(
                    service_id=service_id,
                    service_name=service_info['Service'],
                    host=service_info['Address'],
                    port=service_info['Port'],
                    version=service_info.get('Meta', {}).get('version', '1.0.0'),
                    health_check_url="/health",
                    metadata=service_info.get('Meta', {}),
                    tags=service_info.get('Tags', [])
                )
            return None
        except Exception as e:
            print(f"Failed to get service from Consul: {e}")
            return None
    
    async def update_health(self, service_id: str, status: ServiceStatus) -> bool:
        """Update service health in Consul."""
        # Consul manages health through checks, so this is a no-op
        # In a real implementation, you might update service metadata
        return True
    
    async def heartbeat(self, service_id: str) -> bool:
        """Send heartbeat to Consul."""
        # Consul handles heartbeats through health checks
        return True


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout: int = 10  # Request timeout in seconds


class CircuitBreaker:
    """Circuit breaker implementation for service resilience."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        """Initialize circuit breaker."""
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_request_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            self.last_request_time = datetime.utcnow()
            
            # Check if circuit is open
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=f"Circuit breaker {self.name} is OPEN"
                    )
            
            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
                else:
                    result = func(*args, **kwargs)
                
                # Record success
                await self._on_success()
                return result
                
            except Exception as e:
                # Record failure
                await self._on_failure()
                raise e
    
    async def _on_success(self) -> None:
        """Handle successful request."""
        self.failure_count = 0
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.success_count = 0
    
    async def _on_failure(self) -> None:
        """Handle failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt to reset circuit breaker."""
        if not self.last_failure_time:
            return False
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None
        }


class LoadBalancer:
    """Load balancer for distributing requests across service instances."""
    
    def __init__(self, strategy: str = "round_robin"):
        """Initialize load balancer."""
        self.strategy = strategy
        self._counters: Dict[str, int] = {}
    
    def select_instance(self, instances: List[ServiceInstance], service_name: str) -> Optional[ServiceInstance]:
        """Select a service instance based on load balancing strategy."""
        if not instances:
            return None
        
        healthy_instances = [i for i in instances if i.is_healthy]
        if not healthy_instances:
            return None
        
        if self.strategy == "round_robin":
            return self._round_robin_select(healthy_instances, service_name)
        elif self.strategy == "random":
            return self._random_select(healthy_instances)
        elif self.strategy == "least_connections":
            return self._least_connections_select(healthy_instances)
        else:
            return healthy_instances[0]  # Default to first available
    
    def _round_robin_select(self, instances: List[ServiceInstance], service_name: str) -> ServiceInstance:
        """Round-robin selection."""
        if service_name not in self._counters:
            self._counters[service_name] = 0
        
        index = self._counters[service_name] % len(instances)
        self._counters[service_name] += 1
        
        return instances[index]
    
    def _random_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Random selection."""
        import random
        return random.choice(instances)
    
    def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Least connections selection (simplified)."""
        # In a real implementation, this would track active connections
        # For now, just return the first instance
        return instances[0]


class ServiceDiscovery:
    """Service discovery client with load balancing and circuit breakers."""
    
    def __init__(self, registry: ServiceRegistry, load_balancer: LoadBalancer):
        """Initialize service discovery."""
        self.registry = registry
        self.load_balancer = load_balancer
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.http_client = httpx.AsyncClient()
    
    async def call_service(
        self,
        service_name: str,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10
    ) -> Any:
        """Call a service with automatic discovery, load balancing, and circuit breaking."""
        
        # Discover service instances
        instances = await self.registry.discover_services(service_name)
        if not instances:
            raise HTTPException(
                status_code=503,
                detail=f"No healthy instances found for service: {service_name}"
            )
        
        # Select instance using load balancer
        instance = self.load_balancer.select_instance(instances, service_name)
        if not instance:
            raise HTTPException(
                status_code=503,
                detail=f"No healthy instances available for service: {service_name}"
            )
        
        # Get or create circuit breaker for this instance
        cb_name = f"{service_name}_{instance.service_id}"
        if cb_name not in self.circuit_breakers:
            config = CircuitBreakerConfig(timeout=timeout)
            self.circuit_breakers[cb_name] = CircuitBreaker(cb_name, config)
        
        circuit_breaker = self.circuit_breakers[cb_name]
        
        # Make request through circuit breaker
        async def make_request():
            url = f"{instance.address}{endpoint}"
            response = await self.http_client.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        
        return await circuit_breaker.call(make_request)
    
    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status of all instances of a service."""
        instances = await self.registry.discover_services(service_name)
        
        health_status = {
            "service_name": service_name,
            "total_instances": len(instances),
            "healthy_instances": len([i for i in instances if i.is_healthy]),
            "instances": [i.to_dict() for i in instances]
        }
        
        return health_status
    
    async def get_circuit_breaker_status(self) -> List[Dict[str, Any]]:
        """Get status of all circuit breakers."""
        return [cb.get_state() for cb in self.circuit_breakers.values()]
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()


class HealthChecker:
    """Health checker for service instances."""
    
    def __init__(self, registry: ServiceRegistry, check_interval: int = 30):
        """Initialize health checker."""
        self.registry = registry
        self.check_interval = check_interval
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.http_client = httpx.AsyncClient()
    
    async def start(self) -> None:
        """Start health checking."""
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._health_check_loop())
    
    async def stop(self) -> None:
        """Stop health checking."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.http_client.aclose()
    
    async def _health_check_loop(self) -> None:
        """Health check loop."""
        while self.running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Health check error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _check_all_services(self) -> None:
        """Check health of all registered services."""
        if hasattr(self.registry, 'get_all_services'):
            services = await self.registry.get_all_services()
            
            tasks = []
            for service in services:
                task = asyncio.create_task(self._check_service_health(service))
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_service_health(self, service: ServiceInstance) -> None:
        """Check health of a single service."""
        try:
            url = f"{service.address}{service.health_check_url}"
            response = await self.http_client.get(url, timeout=5.0)
            
            if response.status_code == 200:
                await self.registry.update_health(service.service_id, ServiceStatus.HEALTHY)
                await self.registry.heartbeat(service.service_id)
            else:
                await self.registry.update_health(service.service_id, ServiceStatus.UNHEALTHY)
        
        except Exception:
            await self.registry.update_health(service.service_id, ServiceStatus.UNHEALTHY)


class ServiceManager:
    """High-level service manager for microservices foundation."""
    
    def __init__(self, use_consul: bool = False):
        """Initialize service manager."""
        if use_consul:
            self.registry = ConsulServiceRegistry()
        else:
            self.registry = InMemoryServiceRegistry()
        
        self.load_balancer = LoadBalancer("round_robin")
        self.discovery = ServiceDiscovery(self.registry, self.load_balancer)
        self.health_checker = HealthChecker(self.registry)
        self.current_service: Optional[ServiceInstance] = None
    
    async def register_current_service(
        self,
        service_name: str,
        host: str = "localhost",
        port: int = 8000,
        version: str = "1.0.0",
        health_check_url: str = "/health",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> ServiceInstance:
        """Register the current service instance."""
        service_id = f"{service_name}-{hashlib.md5(f'{host}:{port}'.encode()).hexdigest()[:8]}"
        
        self.current_service = ServiceInstance(
            service_id=service_id,
            service_name=service_name,
            host=host,
            port=port,
            version=version,
            health_check_url=health_check_url,
            status=ServiceStatus.HEALTHY,
            metadata=metadata or {},
            tags=tags or []
        )
        
        success = await self.registry.register_service(self.current_service)
        if success:
            await self.health_checker.start()
        
        return self.current_service
    
    async def deregister_current_service(self) -> bool:
        """Deregister the current service instance."""
        if self.current_service:
            await self.health_checker.stop()
            return await self.registry.deregister_service(self.current_service.service_id)
        return False
    
    async def call_service(self, service_name: str, endpoint: str, **kwargs) -> Any:
        """Call another service."""
        return await self.discovery.call_service(service_name, endpoint, **kwargs)
    
    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get service health information."""
        return await self.discovery.get_service_health(service_name)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        circuit_breakers = await self.discovery.get_circuit_breaker_status()
        
        # Get all services if registry supports it
        all_services = []
        if hasattr(self.registry, 'get_all_services'):
            services = await self.registry.get_all_services()
            all_services = [s.to_dict() for s in services]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "current_service": self.current_service.to_dict() if self.current_service else None,
            "registered_services": all_services,
            "circuit_breakers": circuit_breakers,
            "health_checker_running": self.health_checker.running
        }
    
    async def shutdown(self) -> None:
        """Shutdown service manager."""
        await self.deregister_current_service()
        await self.discovery.close()


# Global service manager instance
service_manager = ServiceManager(use_consul=getattr(settings, 'USE_CONSUL', False))


# Health check function for microservices
async def check_microservices_health() -> Dict[str, Any]:
    """Check microservices infrastructure health."""
    return await service_manager.get_system_status()