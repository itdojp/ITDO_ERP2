"""Advanced settings management system with hot-reload and validation."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, validator
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.core.config import settings
from app.core.monitoring import monitor_performance


class SettingSchema(BaseModel):
    """Schema for individual settings."""
    
    key: str
    value: Any
    data_type: str = "string"  # string, int, float, bool, json, list
    category: str = "general"
    description: Optional[str] = None
    is_sensitive: bool = False
    requires_restart: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    @validator('data_type')
    def validate_data_type(cls, v):
        """Validate data type."""
        allowed_types = ['string', 'int', 'float', 'bool', 'json', 'list']
        if v not in allowed_types:
            raise ValueError(f'Data type must be one of: {allowed_types}')
        return v


class SettingsWatcher(FileSystemEventHandler):
    """File system watcher for settings changes."""

    def __init__(self, settings_manager):
        """Initialize settings watcher."""
        self.settings_manager = settings_manager
        super().__init__()

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith('.json'):
            self.settings_manager.reload_settings()


class AdvancedSettingsManager:
    """Advanced settings management with hot-reload and validation."""

    def __init__(self, settings_file: Optional[str] = None):
        """Initialize settings manager."""
        self.settings_file = settings_file or str(Path("config/settings.json"))
        self.settings_cache: Dict[str, SettingSchema] = {}
        self.observers: List[Observer] = []
        self.watchers_enabled = False
        self.validation_enabled = True
        
        # Create settings directory if it doesn't exist
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        
        # Load initial settings
        self.load_settings()

    @monitor_performance("settings.load")
    def load_settings(self) -> None:
        """Load settings from file."""
        if not os.path.exists(self.settings_file):
            self._create_default_settings()
            return

        try:
            with open(self.settings_file, 'r') as f:
                data = json.load(f)
            
            self.settings_cache.clear()
            for key, value in data.items():
                if isinstance(value, dict) and 'value' in value:
                    # New format with metadata
                    setting = SettingSchema(**value)
                    self.settings_cache[key] = setting
                else:
                    # Legacy format - convert
                    setting = SettingSchema(
                        key=key,
                        value=value,
                        data_type=self._infer_data_type(value),
                        category="legacy"
                    )
                    self.settings_cache[key] = setting
        
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._create_default_settings()

    @monitor_performance("settings.save")
    def save_settings(self) -> bool:
        """Save settings to file."""
        try:
            data = {}
            for key, setting in self.settings_cache.items():
                data[key] = setting.dict()
            
            # Atomic write
            temp_file = f"{self.settings_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            os.replace(temp_file, self.settings_file)
            return True
        
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    @monitor_performance("settings.get")
    def get(self, key: str, default: Any = None, category: Optional[str] = None) -> Any:
        """Get setting value with optional category filter."""
        setting = self.settings_cache.get(key)
        
        if setting is None:
            return default
        
        if category and setting.category != category:
            return default
        
        return setting.value

    @monitor_performance("settings.set")
    def set(
        self, 
        key: str, 
        value: Any, 
        data_type: Optional[str] = None,
        category: str = "general",
        description: Optional[str] = None,
        is_sensitive: bool = False,
        requires_restart: bool = False,
        validation_rules: Optional[Dict[str, Any]] = None,
        save_immediately: bool = True
    ) -> bool:
        """Set setting value with metadata."""
        try:
            # Validate value if rules provided
            if validation_rules and self.validation_enabled:
                if not self._validate_value(value, validation_rules):
                    raise ValueError(f"Value validation failed for key: {key}")
            
            # Infer data type if not provided
            if data_type is None:
                data_type = self._infer_data_type(value)
            
            # Convert value to correct type
            converted_value = self._convert_value(value, data_type)
            
            # Create or update setting
            existing = self.settings_cache.get(key)
            if existing:
                existing.value = converted_value
                existing.data_type = data_type
                existing.category = category
                existing.description = description or existing.description
                existing.is_sensitive = is_sensitive
                existing.requires_restart = requires_restart
                existing.validation_rules = validation_rules or existing.validation_rules
                existing.updated_at = datetime.utcnow()
            else:
                setting = SettingSchema(
                    key=key,
                    value=converted_value,
                    data_type=data_type,
                    category=category,
                    description=description,
                    is_sensitive=is_sensitive,
                    requires_restart=requires_restart,
                    validation_rules=validation_rules
                )
                self.settings_cache[key] = setting
            
            if save_immediately:
                return self.save_settings()
            
            return True
        
        except Exception as e:
            print(f"Error setting value for key {key}: {e}")
            return False

    def delete(self, key: str, save_immediately: bool = True) -> bool:
        """Delete a setting."""
        if key in self.settings_cache:
            del self.settings_cache[key]
            if save_immediately:
                return self.save_settings()
            return True
        return False

    def get_by_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category."""
        return {
            key: setting.value 
            for key, setting in self.settings_cache.items() 
            if setting.category == category
        }

    def get_categories(self) -> List[str]:
        """Get all setting categories."""
        return list(set(setting.category for setting in self.settings_cache.values()))

    def get_settings_requiring_restart(self) -> List[str]:
        """Get settings that require application restart."""
        return [
            key for key, setting in self.settings_cache.items() 
            if setting.requires_restart
        ]

    def export_settings(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Export settings for backup or transfer."""
        result = {}
        for key, setting in self.settings_cache.items():
            if setting.is_sensitive and not include_sensitive:
                continue
            result[key] = setting.dict()
        return result

    def import_settings(self, settings_data: Dict[str, Any], overwrite: bool = False) -> int:
        """Import settings from exported data."""
        imported_count = 0
        
        for key, data in settings_data.items():
            if key in self.settings_cache and not overwrite:
                continue
            
            try:
                if isinstance(data, dict) and 'value' in data:
                    setting = SettingSchema(**data)
                    self.settings_cache[key] = setting
                    imported_count += 1
            except Exception as e:
                print(f"Error importing setting {key}: {e}")
        
        self.save_settings()
        return imported_count

    def enable_hot_reload(self) -> bool:
        """Enable hot-reload of settings file."""
        try:
            if self.watchers_enabled:
                return True
            
            watcher = SettingsWatcher(self)
            observer = Observer()
            observer.schedule(
                watcher, 
                os.path.dirname(self.settings_file), 
                recursive=False
            )
            observer.start()
            
            self.observers.append(observer)
            self.watchers_enabled = True
            return True
        
        except Exception as e:
            print(f"Error enabling hot-reload: {e}")
            return False

    def disable_hot_reload(self) -> None:
        """Disable hot-reload of settings file."""
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        self.observers.clear()
        self.watchers_enabled = False

    def reload_settings(self) -> None:
        """Manually reload settings from file."""
        print("Reloading settings from file...")
        self.load_settings()

    def validate_all_settings(self) -> Dict[str, List[str]]:
        """Validate all settings against their rules."""
        validation_errors = {}
        
        for key, setting in self.settings_cache.items():
            if setting.validation_rules:
                errors = []
                if not self._validate_value(setting.value, setting.validation_rules):
                    errors.append("Value validation failed")
                
                if errors:
                    validation_errors[key] = errors
        
        return validation_errors

    def _create_default_settings(self) -> None:
        """Create default settings file."""
        default_settings = {
            "app_name": SettingSchema(
                key="app_name",
                value="ITDO ERP System v2",
                data_type="string",
                category="application",
                description="Application display name"
            ),
            "max_page_size": SettingSchema(
                key="max_page_size",
                value=1000,
                data_type="int",
                category="api",
                description="Maximum page size for API responses",
                validation_rules={"min": 1, "max": 10000}
            ),
            "enable_debug_mode": SettingSchema(
                key="enable_debug_mode",
                value=False,
                data_type="bool",
                category="application",
                description="Enable debug mode",
                requires_restart=True
            ),
            "cache_ttl_seconds": SettingSchema(
                key="cache_ttl_seconds",
                value=300,
                data_type="int",
                category="performance",
                description="Default cache TTL in seconds",
                validation_rules={"min": 1, "max": 86400}
            )
        }
        
        self.settings_cache = default_settings
        self.save_settings()

    def _infer_data_type(self, value: Any) -> str:
        """Infer data type from value."""
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, (list, tuple)):
            return "list"
        elif isinstance(value, dict):
            return "json"
        else:
            return "string"

    def _convert_value(self, value: Any, data_type: str) -> Any:
        """Convert value to specified data type."""
        if data_type == "int":
            return int(value)
        elif data_type == "float":
            return float(value)
        elif data_type == "bool":
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        elif data_type == "list":
            if isinstance(value, str):
                return json.loads(value)
            return list(value)
        elif data_type == "json":
            if isinstance(value, str):
                return json.loads(value)
            return value
        else:
            return str(value)

    def _validate_value(self, value: Any, rules: Dict[str, Any]) -> bool:
        """Validate value against rules."""
        try:
            if "min" in rules and value < rules["min"]:
                return False
            if "max" in rules and value > rules["max"]:
                return False
            if "pattern" in rules:
                import re
                if not re.match(rules["pattern"], str(value)):
                    return False
            if "choices" in rules and value not in rules["choices"]:
                return False
            
            return True
        except Exception:
            return False


# Global settings manager instance
settings_manager = AdvancedSettingsManager()


def get_setting(key: str, default: Any = None, category: Optional[str] = None) -> Any:
    """Get setting value (convenience function)."""
    return settings_manager.get(key, default, category)


def set_setting(
    key: str, 
    value: Any, 
    category: str = "general",
    **kwargs
) -> bool:
    """Set setting value (convenience function)."""
    return settings_manager.set(key, value, category=category, **kwargs)


def reload_settings() -> None:
    """Reload settings (convenience function)."""
    settings_manager.reload_settings()


# Health check for settings
def check_settings_health() -> Dict[str, Any]:
    """Check settings system health."""
    health_info = {
        "status": "healthy",
        "settings_count": len(settings_manager.settings_cache),
        "categories": len(settings_manager.get_categories()),
        "hot_reload_enabled": settings_manager.watchers_enabled,
        "validation_errors": {}
    }
    
    try:
        # Validate all settings
        validation_errors = settings_manager.validate_all_settings()
        if validation_errors:
            health_info["status"] = "degraded"
            health_info["validation_errors"] = validation_errors
        
        # Check file accessibility
        if not os.path.exists(settings_manager.settings_file):
            health_info["status"] = "unhealthy"
            health_info["error"] = "Settings file not found"
        
    except Exception as e:
        health_info["status"] = "unhealthy"
        health_info["error"] = str(e)
    
    return health_info