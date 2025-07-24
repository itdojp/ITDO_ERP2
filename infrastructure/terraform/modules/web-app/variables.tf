# Variables for Web Application Infrastructure Module

variable "project_name" {
  description = "Name of the project"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# VPC Configuration
variable "create_vpc" {
  description = "Whether to create a new VPC"
  type        = bool
  default     = true
}

variable "vpc_id" {
  description = "VPC ID to use when create_vpc is false"
  type        = string
  default     = ""
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b"]
  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones must be specified for high availability."
  }
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs (used when create_vpc is false)"
  type        = list(string)
  default     = []
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs (used when create_vpc is false)"
  type        = list(string)
  default     = []
}

# Container Configuration
variable "container_name" {
  description = "Name of the container"
  type        = string
  default     = "app"
}

variable "container_image" {
  description = "Container image URI"
  type        = string
  validation {
    condition     = can(regex("^.+:.+$", var.container_image))
    error_message = "Container image must include a tag (e.g., nginx:latest)."
  }
}

variable "container_port" {
  description = "Port that the container listens on"
  type        = number
  default     = 8000
  validation {
    condition     = var.container_port > 0 && var.container_port < 65536
    error_message = "Container port must be between 1 and 65535."
  }
}

variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/health"
  validation {
    condition     = can(regex("^/.*", var.health_check_path))
    error_message = "Health check path must start with '/'."
  }
}

# ECS Configuration
variable "task_cpu" {
  description = "CPU units for the task (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.task_cpu)
    error_message = "Task CPU must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "task_memory" {
  description = "Memory (MB) for the task"
  type        = number
  default     = 1024
  validation {
    condition     = var.task_memory >= 512 && var.task_memory <= 30720
    error_message = "Task memory must be between 512 and 30720 MB."
  }
}

# Auto Scaling Configuration
variable "enable_auto_scaling" {
  description = "Enable auto scaling for the ECS service"
  type        = bool
  default     = true
}

variable "auto_scaling" {
  description = "Auto scaling configuration"
  type = object({
    min_capacity        = number
    max_capacity        = number
    desired_capacity    = number
    cpu_target_value    = number
    memory_target_value = number
  })
  default = {
    min_capacity        = 1
    max_capacity        = 10
    desired_capacity    = 2
    cpu_target_value    = 70.0
    memory_target_value = 80.0
  }
  validation {
    condition = (
      var.auto_scaling.min_capacity >= 1 &&
      var.auto_scaling.max_capacity >= var.auto_scaling.min_capacity &&
      var.auto_scaling.desired_capacity >= var.auto_scaling.min_capacity &&
      var.auto_scaling.desired_capacity <= var.auto_scaling.max_capacity &&
      var.auto_scaling.cpu_target_value > 0 && var.auto_scaling.cpu_target_value <= 100 &&
      var.auto_scaling.memory_target_value > 0 && var.auto_scaling.memory_target_value <= 100
    )
    error_message = "Auto scaling configuration values must be valid ranges."
  }
}

# Environment Variables and Secrets
variable "environment_variables" {
  description = "Environment variables for the container"
  type        = map(string)
  default     = {}
  sensitive   = false
}

variable "secrets" {
  description = "Secrets for the container (key = env var name, value = SSM parameter name)"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# Monitoring and Logging
variable "enable_container_insights" {
  description = "Enable CloudWatch Container Insights"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period."
  }
}

# Load Balancer Configuration
variable "enable_deletion_protection" {
  description = "Enable deletion protection for the load balancer"
  type        = bool
  default     = false
}

variable "ssl_certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS listener"
  type        = string
  default     = ""
}

variable "enable_https" {
  description = "Enable HTTPS listener"
  type        = bool
  default     = false
}

# Database Configuration (Optional)
variable "database_config" {
  description = "Database configuration"
  type = object({
    engine                = string
    engine_version        = string
    instance_class        = string
    allocated_storage     = number
    max_allocated_storage = number
    database_name         = string
    username              = string
    backup_retention_days = number
    backup_window         = string
    maintenance_window    = string
    multi_az              = bool
    publicly_accessible   = bool
    storage_encrypted     = bool
  })
  default = null
}

# Redis Configuration (Optional)
variable "redis_config" {
  description = "Redis configuration"
  type = object({
    node_type               = string
    num_cache_nodes         = number
    parameter_group_name    = string
    port                    = number
    engine_version          = string
    apply_immediately       = bool
    maintenance_window      = string
    snapshot_retention_limit = number
    snapshot_window         = string
  })
  default = null
}

# Backup Configuration
variable "backup_config" {
  description = "Backup configuration"
  type = object({
    backup_vault_name     = string
    backup_plan_name      = string
    schedule              = string
    delete_after_days     = number
    cold_storage_after    = number
    backup_resources      = list(string)
  })
  default = null
}