# Outputs for Development Environment

# Application URLs
output "backend_url" {
  description = "Backend application URL"
  value       = module.backend.application_url
}

output "frontend_url" {
  description = "Frontend application URL"
  value       = module.frontend.application_url
}

output "backend_dns_name" {
  description = "Backend load balancer DNS name"
  value       = module.backend.load_balancer_dns_name
}

output "frontend_dns_name" {
  description = "Frontend load balancer DNS name"
  value       = module.frontend.load_balancer_dns_name
}

# Database Information
output "database_endpoint" {
  description = "PostgreSQL database endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = false
}

output "database_port" {
  description = "PostgreSQL database port"
  value       = aws_db_instance.postgres.port
}

output "database_name" {
  description = "PostgreSQL database name"
  value       = aws_db_instance.postgres.db_name
}

# Cache Information
output "redis_endpoint" {
  description = "Redis cache endpoint"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
}

output "redis_address" {
  description = "Redis cache address"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis cache port"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].port
}

# Infrastructure Information
output "vpc_id" {
  description = "VPC ID"
  value       = module.backend.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.backend.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.backend.private_subnet_ids
}

# ECS Information
output "backend_ecs_cluster_name" {
  description = "Backend ECS cluster name"
  value       = module.backend.ecs_cluster_name
}

output "frontend_ecs_cluster_name" {
  description = "Frontend ECS cluster name"
  value       = module.frontend.ecs_cluster_name
}

output "backend_ecs_service_name" {
  description = "Backend ECS service name"
  value       = module.backend.ecs_service_name
}

output "frontend_ecs_service_name" {
  description = "Frontend ECS service name"
  value       = module.frontend.ecs_service_name
}

# Security Group Information
output "backend_security_group_id" {
  description = "Backend application security group ID"
  value       = module.backend.app_security_group_id
}

output "frontend_security_group_id" {
  description = "Frontend application security group ID"
  value       = module.frontend.app_security_group_id
}

output "database_security_group_id" {
  description = "Database security group ID"
  value       = aws_security_group.postgres.id
}

output "redis_security_group_id" {
  description = "Redis security group ID"
  value       = aws_security_group.redis.id
}

# Monitoring and Logging
output "backend_log_group_name" {
  description = "Backend CloudWatch log group name"
  value       = module.backend.log_group_name
}

output "frontend_log_group_name" {
  description = "Frontend CloudWatch log group name"
  value       = module.frontend.log_group_name
}

output "cloudwatch_logs_url" {
  description = "CloudWatch logs URL"
  value       = module.backend.cloudwatch_logs_url
}

# AWS Console URLs
output "backend_ecs_console_url" {
  description = "Backend ECS service console URL"
  value       = module.backend.ecs_service_url
}

output "frontend_ecs_console_url" {
  description = "Frontend ECS service console URL"
  value       = module.frontend.ecs_service_url
}

output "rds_console_url" {
  description = "RDS console URL"
  value       = "https://console.aws.amazon.com/rds/home?region=${var.aws_region}#database:id=${aws_db_instance.postgres.id};is-cluster=false"
}

output "elasticache_console_url" {
  description = "ElastiCache console URL"
  value       = "https://console.aws.amazon.com/elasticache/home?region=${var.aws_region}#redis-node:id=${aws_elasticache_cluster.redis.cluster_id}"
}

# Configuration Summary
output "deployment_summary" {
  description = "Summary of the deployed development environment"
  value = {
    environment     = "development"
    region         = var.aws_region
    backend_image  = var.backend_image
    frontend_image = var.frontend_image
    database_engine = aws_db_instance.postgres.engine
    database_version = aws_db_instance.postgres.engine_version
    cache_engine   = aws_elasticache_cluster.redis.engine
    vpc_cidr       = module.backend.vpc_cidr_block
    availability_zones = data.aws_availability_zones.available.names
    created_at     = timestamp()
  }
}

# Environment Variables for Local Development
output "development_env_vars" {
  description = "Environment variables for local development"
  value = {
    DATABASE_URL              = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${var.db_name}"
    REDIS_URL                 = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
    BACKEND_URL               = module.backend.application_url
    FRONTEND_URL              = module.frontend.application_url
    VITE_API_URL             = module.backend.application_url
    VITE_API_BASE_URL        = "${module.backend.application_url}/api/v1"
    ENVIRONMENT               = "development"
    LOG_LEVEL                 = var.log_level
  }
  sensitive = true
}

# Connection Strings
output "connection_info" {
  description = "Connection information for development"
  value = {
    database = {
      host     = aws_db_instance.postgres.address
      port     = aws_db_instance.postgres.port
      database = aws_db_instance.postgres.db_name
      username = var.db_username
    }
    redis = {
      host = aws_elasticache_cluster.redis.cache_nodes[0].address
      port = aws_elasticache_cluster.redis.cache_nodes[0].port
    }
    backend = {
      url = module.backend.application_url
      dns = module.backend.load_balancer_dns_name
    }
    frontend = {
      url = module.frontend.application_url
      dns = module.frontend.load_balancer_dns_name
    }
  }
  sensitive = false
}