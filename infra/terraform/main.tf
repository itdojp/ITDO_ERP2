# ITDO ERP v2 - Production Infrastructure (Terraform)
# CC03 v58.0 - Day 2 Infrastructure Automation

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
  
  backend "s3" {
    # Configure with your S3 backend
    # bucket = "itdo-erp-terraform-state"
    # key    = "production/terraform.tfstate" 
    # region = "ap-northeast-1"
  }
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "itdo-erp"
}

variable "availability_target" {
  description = "Availability target percentage"
  type        = number
  default     = 99.9
}

variable "recovery_time_minutes" {
  description = "Maximum recovery time in minutes"
  type        = number
  default     = 15
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "itdo-erp.com"
}

# Local values
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "ITDO-DevOps"
    CostCenter  = "Production"
    Backup      = "Required"
    Monitoring  = "Critical"
  }
  
  availability_zones = ["ap-northeast-1a", "ap-northeast-1c", "ap-northeast-1d"]
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr          = var.vpc_cidr
  availability_zones = local.availability_zones
  
  tags = local.common_tags
}

# ECS Cluster Module  
module "ecs_cluster" {
  source = "./modules/ecs"
  
  project_name    = var.project_name
  environment     = var.environment
  vpc_id         = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids
  
  tags = local.common_tags
}

# RDS Module
module "database" {
  source = "./modules/rds"
  
  project_name       = var.project_name
  environment        = var.environment
  vpc_id            = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  
  # High availability configuration
  multi_az               = true
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  tags = local.common_tags
}

# ElastiCache Module
module "cache" {
  source = "./modules/elasticache"
  
  project_name       = var.project_name
  environment        = var.environment
  vpc_id            = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  
  tags = local.common_tags
}

# Application Load Balancer Module
module "load_balancer" {
  source = "./modules/alb"
  
  project_name      = var.project_name
  environment       = var.environment
  vpc_id           = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  domain_name      = var.domain_name
  
  tags = local.common_tags
}

# Auto Scaling Module
module "auto_scaling" {
  source = "./modules/autoscaling"
  
  project_name    = var.project_name
  environment     = var.environment
  ecs_cluster_name = module.ecs_cluster.cluster_name
  
  # 99.9% availability targets
  min_capacity = 2
  max_capacity = 10
  desired_capacity = 2
  
  tags = local.common_tags
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"
  
  project_name         = var.project_name
  environment          = var.environment
  availability_target  = var.availability_target
  recovery_time_minutes = var.recovery_time_minutes
  
  # Resources to monitor
  load_balancer_arn = module.load_balancer.load_balancer_arn
  ecs_cluster_name  = module.ecs_cluster.cluster_name
  rds_instance_id   = module.database.instance_id
  
  tags = local.common_tags
}

# Backup Module
module "backup" {
  source = "./modules/backup"
  
  project_name = var.project_name
  environment  = var.environment
  
  # Resources to backup
  rds_instance_arn = module.database.instance_arn
  
  tags = local.common_tags
}

# Security Module  
module "security" {
  source = "./modules/security"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_id      = module.vpc.vpc_id
  
  tags = local.common_tags
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = module.load_balancer.dns_name
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = module.database.endpoint
  sensitive   = true
}

output "cache_endpoint" {
  description = "ElastiCache endpoint"
  value       = module.cache.endpoint
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs_cluster.cluster_name
}

output "monitoring_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.monitoring.dashboard_url
}