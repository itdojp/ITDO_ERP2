# Variables for Development Environment

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

# Container Images
variable "backend_image" {
  description = "Backend container image"
  type        = string
  default     = "ghcr.io/itdojp/itdo-erp-backend:latest"
  validation {
    condition     = can(regex("^.+:.+$", var.backend_image))
    error_message = "Backend image must include a tag."
  }
}

variable "frontend_image" {
  description = "Frontend container image"
  type        = string
  default     = "ghcr.io/itdojp/itdo-erp-frontend:latest"
  validation {
    condition     = can(regex("^.+:.+$", var.frontend_image))
    error_message = "Frontend image must include a tag."
  }
}

# Database Configuration
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "itdo_erp_dev"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_name))
    error_message = "Database name must start with a letter and contain only letters, numbers, and underscores."
  }
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "itdo_user"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_username))
    error_message = "Database username must start with a letter and contain only letters, numbers, and underscores."
  }
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Database password must be at least 8 characters long."
  }
}

# Application Configuration
variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.secret_key) >= 32
    error_message = "Secret key must be at least 32 characters long."
  }
}

# Development-specific settings
variable "enable_debug_mode" {
  description = "Enable debug mode for development"
  type        = bool
  default     = true
}

variable "auto_apply_migrations" {
  description = "Automatically apply database migrations on startup"
  type        = bool
  default     = true
}

variable "enable_hot_reload" {
  description = "Enable hot reload for development"
  type        = bool
  default     = true
}

# Cost optimization for development
variable "schedule_stop_start" {
  description = "Schedule to stop/start resources for cost optimization"
  type = object({
    enabled    = bool
    stop_time  = string  # e.g., "18:00"
    start_time = string  # e.g., "09:00"
    timezone   = string  # e.g., "Asia/Tokyo"
    weekdays_only = bool
  })
  default = {
    enabled       = false
    stop_time     = "18:00"
    start_time    = "09:00"
    timezone      = "UTC"
    weekdays_only = true
  }
}

# Monitoring and alerting
variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring for development debugging"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
  validation {
    condition = var.alert_email == "" || can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_email))
    error_message = "Alert email must be a valid email address."
  }
}

# Security settings
variable "enable_vpc_flow_logs" {
  description = "Enable VPC flow logs for security monitoring"
  type        = bool
  default     = false  # Disabled by default in dev to reduce costs
}

variable "enable_security_groups_logging" {
  description = "Enable security groups logging"
  type        = bool
  default     = false  # Disabled by default in dev to reduce costs
}

# Backup configuration
variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 3
  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 30
    error_message = "Backup retention days must be between 1 and 30."
  }
}

# Resource tagging
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default = {
    Team            = "development"
    Purpose         = "development-testing"
    AutoShutdown    = "true"
    CostOptimized   = "true"
    TemporaryEnvironment = "true"
  }
}

# Development features
variable "enable_debug_endpoints" {
  description = "Enable debug endpoints for development"
  type        = bool
  default     = true
}

variable "enable_test_data" {
  description = "Enable test data seeding"
  type        = bool
  default     = true
}

variable "log_level" {
  description = "Log level for applications"
  type        = string
  default     = "DEBUG"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}