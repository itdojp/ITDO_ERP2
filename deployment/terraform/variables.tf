# ITDO ERP Terraform Variables
# Configuration variables for cloud infrastructure deployment

# ============================================================================
# General Configuration
# ============================================================================

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "itdo-erp"
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be one of: production, staging, development."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

# ============================================================================
# Network Configuration
# ============================================================================

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "List of CIDR blocks that can access the EKS cluster endpoint publicly"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# ============================================================================
# EKS Cluster Configuration
# ============================================================================

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.28"
}

# System Node Group Configuration
variable "system_node_instance_types" {
  description = "Instance types for system node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "system_node_desired_size" {
  description = "Desired number of nodes in system node group"
  type        = number
  default     = 2
}

variable "system_node_min_size" {
  description = "Minimum number of nodes in system node group"
  type        = number
  default     = 1
}

variable "system_node_max_size" {
  description = "Maximum number of nodes in system node group"
  type        = number
  default     = 5
}

# Application Node Group Configuration
variable "app_node_instance_types" {
  description = "Instance types for application node group"
  type        = list(string)
  default     = ["m5.large", "m5.xlarge", "c5.large", "c5.xlarge"]
}

variable "app_node_desired_size" {
  description = "Desired number of nodes in application node group"
  type        = number
  default     = 3
}

variable "app_node_min_size" {
  description = "Minimum number of nodes in application node group"
  type        = number
  default     = 2
}

variable "app_node_max_size" {
  description = "Maximum number of nodes in application node group"
  type        = number
  default     = 20
}

# ============================================================================
# Database Configuration (RDS PostgreSQL)
# ============================================================================

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15.4"
}

variable "postgres_instance_class" {
  description = "RDS instance class for PostgreSQL"
  type        = string
  default     = "db.t3.medium"
}

variable "postgres_allocated_storage" {
  description = "Initial allocated storage for RDS instance (GB)"
  type        = number
  default     = 100
}

variable "postgres_max_allocated_storage" {
  description = "Maximum allocated storage for RDS instance (GB)"
  type        = number
  default     = 1000
}

variable "postgres_database_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "itdo_erp"
}

variable "postgres_username" {
  description = "Username for PostgreSQL database"
  type        = string
  default     = "itdo_erp_user"
}

variable "postgres_password" {
  description = "Password for PostgreSQL database"
  type        = string
  sensitive   = true
  default     = null
}

variable "postgres_backup_retention_period" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 30
}

# ============================================================================
# Cache Configuration (ElastiCache Redis)
# ============================================================================

variable "redis_version" {
  description = "Redis version"
  type        = string
  default     = "7.0"
}

variable "redis_node_type" {
  description = "ElastiCache node type for Redis"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes in Redis cluster"
  type        = number
  default     = 2
}

variable "redis_auth_token" {
  description = "Auth token for Redis cluster"
  type        = string
  sensitive   = true
  default     = null
}

variable "redis_snapshot_retention_limit" {
  description = "Number of days to retain Redis snapshots"
  type        = number
  default     = 7
}

# ============================================================================
# Storage Configuration
# ============================================================================

variable "backup_retention_days" {
  description = "Number of days to retain backups in S3"
  type        = number
  default     = 90
}

variable "cloudwatch_log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30
}

# ============================================================================
# Security Configuration
# ============================================================================

variable "enable_encryption" {
  description = "Enable encryption at rest for all resources"
  type        = bool
  default     = true
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = true
}

# ============================================================================
# Monitoring and Alerting Configuration
# ============================================================================

variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  type        = string
  default     = null
}

# ============================================================================
# Cost Optimization Configuration
# ============================================================================

variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = true
}

variable "enable_autoscaling" {
  description = "Enable cluster autoscaling"
  type        = bool
  default     = true
}

# ============================================================================
# Feature Flags
# ============================================================================

variable "enable_service_mesh" {
  description = "Enable service mesh (Istio)"
  type        = bool
  default     = false
}

variable "enable_gpu_nodes" {
  description = "Enable GPU nodes for ML workloads"
  type        = bool
  default     = false
}

variable "enable_managed_prometheus" {
  description = "Enable Amazon Managed Service for Prometheus"
  type        = bool
  default     = true
}

variable "enable_managed_grafana" {
  description = "Enable Amazon Managed Grafana"
  type        = bool
  default     = true
}

# ============================================================================
# Domain and SSL Configuration
# ============================================================================

variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string
  default     = "itdo-erp.com"
}

variable "create_route53_zone" {
  description = "Create Route53 hosted zone for the domain"
  type        = bool
  default     = true
}

variable "ssl_certificate_arn" {
  description = "ARN of existing SSL certificate in ACM"
  type        = string
  default     = null
}

# ============================================================================
# Backup and Disaster Recovery Configuration
# ============================================================================

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup replication"
  type        = bool
  default     = true
}

variable "backup_region" {
  description = "AWS region for backup replication"
  type        = string
  default     = "us-east-1"
}

variable "rpo_hours" {
  description = "Recovery Point Objective in hours"
  type        = number
  default     = 4
}

variable "rto_hours" {
  description = "Recovery Time Objective in hours"
  type        = number
  default     = 2
}

# ============================================================================
# Compliance and Governance Configuration
# ============================================================================

variable "enable_config_rules" {
  description = "Enable AWS Config rules for compliance monitoring"
  type        = bool
  default     = true
}

variable "enable_cloudtrail" {
  description = "Enable CloudTrail for audit logging"
  type        = bool
  default     = true
}

variable "enable_guardduty" {
  description = "Enable GuardDuty for threat detection"
  type        = bool
  default     = true
}

variable "compliance_frameworks" {
  description = "List of compliance frameworks to implement"
  type        = list(string)
  default     = ["SOC2", "ISO27001"]
}

# ============================================================================
# Development and Testing Configuration
# ============================================================================

variable "enable_dev_tools" {
  description = "Enable development and debugging tools"
  type        = bool
  default     = false
}

variable "enable_test_data" {
  description = "Enable test data seeding"
  type        = bool
  default     = false
}

variable "dev_access_cidrs" {
  description = "CIDR blocks for development access"
  type        = list(string)
  default     = []
}

# ============================================================================
# Resource Tagging Configuration
# ============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "cost_center" {
  description = "Cost center for billing allocation"
  type        = string
  default     = "IT-Operations"
}

variable "owner" {
  description = "Owner of the infrastructure"
  type        = string
  default     = "ITDO-DevOps-Team"
}

# ============================================================================
# Environment Specific Overrides
# ============================================================================

variable "environment_config" {
  description = "Environment specific configuration overrides"
  type = object({
    postgres_instance_class = optional(string)
    redis_node_type        = optional(string)
    node_instance_types    = optional(list(string))
    enable_high_availability = optional(bool)
    enable_performance_insights = optional(bool)
  })
  default = {}
}