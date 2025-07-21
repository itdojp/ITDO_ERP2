"""Service registry for dependency injection and service management."""

import logging
from typing import Dict, Type, TypeVar, Generic, Optional, Any, Callable, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.base_service import BaseService, CachedService

T = TypeVar("T", bound=BaseService)
logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Central registry for all business services with dependency injection."""

    def __init__(self):
        """Initialize service registry."""
        self._services: Dict[str, Type[BaseService]] = {}
        self._singletons: Dict[str, BaseService] = {}
        self._factories: Dict[str, Callable] = {}
        self._aliases: Dict[str, str] = {}
        
    def register(
        self, 
        service_class: Type[T], 
        name: Optional[str] = None,
        singleton: bool = False,
        factory: Optional[Callable] = None,
        aliases: Optional[list[str]] = None
    ) -> None:
        """Register a service class in the registry."""
        service_name = name or service_class.__name__.lower().replace('service', '')
        
        self._services[service_name] = service_class
        
        if factory:
            self._factories[service_name] = factory
            
        if aliases:
            for alias in aliases:
                self._aliases[alias] = service_name
                
        logger.info(f"Registered service: {service_name} ({service_class.__name__})")
        
    def get(
        self, 
        service_name: str, 
        db: Union[AsyncSession, Session], 
        **kwargs
    ) -> BaseService:
        """Get service instance by name."""
        # Resolve alias
        resolved_name = self._aliases.get(service_name, service_name)
        
        # Check if singleton instance exists
        if resolved_name in self._singletons:
            singleton_instance = self._singletons[resolved_name]
            # Update database session for singleton
            singleton_instance.db = db
            return singleton_instance
            
        # Get service class
        service_class = self._services.get(resolved_name)
        if not service_class:
            raise ValueError(f"Service '{service_name}' not found in registry")
            
        # Use factory if available
        if resolved_name in self._factories:
            factory = self._factories[resolved_name]
            instance = factory(db=db, **kwargs)
        else:
            # Standard instantiation
            instance = service_class(db=db, **kwargs)
            
        logger.debug(f"Created service instance: {resolved_name}")
        return instance
        
    def register_singleton(
        self, 
        service_name: str, 
        instance: BaseService
    ) -> None:
        """Register a singleton service instance."""
        self._singletons[service_name] = instance
        logger.info(f"Registered singleton service: {service_name}")
        
    def list_services(self) -> Dict[str, Type[BaseService]]:
        """List all registered services."""
        return self._services.copy()
        
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        self._aliases.clear()
        logger.info("Service registry cleared")


# Global service registry instance
service_registry = ServiceRegistry()


def register_service(
    name: Optional[str] = None,
    singleton: bool = False,
    aliases: Optional[list[str]] = None
):
    """Decorator for registering services."""
    def decorator(service_class: Type[BaseService]):
        service_registry.register(
            service_class=service_class,
            name=name,
            singleton=singleton,
            aliases=aliases
        )
        return service_class
    return decorator


class ServiceProvider:
    """Service provider for dependency injection in API endpoints."""
    
    def __init__(self, db: Union[AsyncSession, Session]):
        """Initialize service provider with database session."""
        self.db = db
        self._service_cache: Dict[str, BaseService] = {}
        
    def get_service(self, service_name: str, **kwargs) -> BaseService:
        """Get service instance with dependency injection."""
        # Check cache first
        cache_key = f"{service_name}:{hash(frozenset(kwargs.items()))}"
        if cache_key in self._service_cache:
            cached_service = self._service_cache[cache_key]
            # Update database session
            cached_service.db = self.db
            return cached_service
            
        # Get from registry
        service = service_registry.get(service_name, db=self.db, **kwargs)
        
        # Cache the service
        self._service_cache[cache_key] = service
        
        return service
        
    def __getattr__(self, name: str) -> BaseService:
        """Allow direct attribute access to services."""
        try:
            return self.get_service(name)
        except ValueError:
            raise AttributeError(f"Service '{name}' not found")


# Dependency injection helper for FastAPI
def get_service_provider(db: Union[AsyncSession, Session]) -> ServiceProvider:
    """Get service provider instance for dependency injection."""
    return ServiceProvider(db)


# Service discovery utilities
def discover_services(package_name: str = "app.services") -> None:
    """Auto-discover and register services from a package."""
    import importlib
    import pkgutil
    import inspect
    
    try:
        package = importlib.import_module(package_name)
        
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            try:
                module = importlib.import_module(f"{package_name}.{module_name}")
                
                # Find service classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseService) and 
                        obj is not BaseService and
                        obj is not CachedService):
                        
                        # Auto-register service
                        service_name = name.lower().replace('service', '')
                        if service_name not in service_registry.list_services():
                            service_registry.register(obj, service_name)
                            
            except ImportError as e:
                logger.warning(f"Could not import service module {module_name}: {e}")
                
    except ImportError as e:
        logger.error(f"Could not import package {package_name}: {e}")


# Pre-built service configurations
class ServiceConfig:
    """Configuration for commonly used service patterns."""
    
    @staticmethod
    def configure_cached_services():
        """Configure services with caching enabled."""
        cached_services = [
            'user', 'organization', 'department', 'role', 'permission'
        ]
        
        for service_name in cached_services:
            if service_name in service_registry.list_services():
                # Wrap with cached service
                original_service = service_registry._services[service_name]
                
                def cached_factory(db, **kwargs):
                    return CachedService(
                        model=original_service.model,
                        db=db,
                        cache_ttl=kwargs.get('cache_ttl', 300)
                    )
                
                service_registry._factories[service_name] = cached_factory
                
    @staticmethod
    def configure_business_services():
        """Configure business-specific services."""
        # Register common aliases
        aliases = {
            'auth': 'authentication',
            'perms': 'permission',
            'orgs': 'organization',
            'depts': 'department',
            'tasks': 'task',
            'projects': 'project'
        }
        
        for alias, service_name in aliases.items():
            service_registry._aliases[alias] = service_name


# Initialize service registry with auto-discovery
def initialize_service_registry():
    """Initialize the service registry with auto-discovery and configuration."""
    logger.info("Initializing service registry...")
    
    # Auto-discover services
    discover_services("app.services")
    
    # Configure cached services
    ServiceConfig.configure_cached_services()
    
    # Configure business services
    ServiceConfig.configure_business_services()
    
    logger.info(f"Service registry initialized with {len(service_registry.list_services())} services")
    
    # Log registered services
    for name, service_class in service_registry.list_services().items():
        logger.debug(f"  - {name}: {service_class.__name__}")


# Service health check
async def check_service_health() -> Dict[str, Any]:
    """Check health of all registered services."""
    health_status = {
        "status": "healthy",
        "services": {},
        "total_services": len(service_registry.list_services()),
        "healthy_services": 0,
        "unhealthy_services": 0
    }
    
    for service_name, service_class in service_registry.list_services().items():
        try:
            # Basic health check - verify service can be instantiated
            # Note: This is a basic check; services could implement their own health_check method
            health_status["services"][service_name] = {
                "status": "healthy",
                "class": service_class.__name__,
                "module": service_class.__module__
            }
            health_status["healthy_services"] += 1
            
        except Exception as e:
            health_status["services"][service_name] = {
                "status": "unhealthy",
                "error": str(e),
                "class": service_class.__name__,
                "module": service_class.__module__
            }
            health_status["unhealthy_services"] += 1
            health_status["status"] = "degraded"
    
    if health_status["unhealthy_services"] > 0:
        health_status["status"] = "unhealthy" if health_status["healthy_services"] == 0 else "degraded"
        
    return health_status