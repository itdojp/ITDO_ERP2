# Outputs for Web Application Infrastructure Module

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = var.create_vpc ? aws_vpc.main[0].cidr_block : null
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = var.create_vpc ? aws_subnet.public[*].id : var.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = var.create_vpc ? aws_subnet.private[*].id : var.private_subnet_ids
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = var.create_vpc ? aws_internet_gateway.main[0].id : null
}

# Load Balancer Outputs
output "load_balancer_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "load_balancer_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "load_balancer_hosted_zone_id" {
  description = "Hosted zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "target_group_arn" {
  description = "ARN of the Target Group"
  value       = aws_lb_target_group.app.arn
}

# ECS Outputs
output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_service_id" {
  description = "ID of the ECS service"
  value       = aws_ecs_service.app.id
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}

output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = aws_ecs_task_definition.app.arn
}

output "ecs_task_definition_family" {
  description = "Family of the ECS task definition"
  value       = aws_ecs_task_definition.app.family
}

output "ecs_task_definition_revision" {
  description = "Revision of the ECS task definition"
  value       = aws_ecs_task_definition.app.revision
}

# Security Group Outputs
output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "app_security_group_id" {
  description = "ID of the application security group"
  value       = aws_security_group.app.id
}

# IAM Outputs
output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

# CloudWatch Outputs
output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.app.name
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.app.arn
}

# Auto Scaling Outputs
output "autoscaling_target_resource_id" {
  description = "Resource ID of the auto scaling target"
  value       = var.enable_auto_scaling ? aws_appautoscaling_target.ecs_target[0].resource_id : null
}

output "autoscaling_cpu_policy_arn" {
  description = "ARN of the CPU auto scaling policy"
  value       = var.enable_auto_scaling ? aws_appautoscaling_policy.ecs_cpu_policy[0].arn : null
}

output "autoscaling_memory_policy_arn" {
  description = "ARN of the memory auto scaling policy"
  value       = var.enable_auto_scaling ? aws_appautoscaling_policy.ecs_memory_policy[0].arn : null
}

# Application URLs
output "application_url" {
  description = "URL of the application (HTTP)"
  value       = "http://${aws_lb.main.dns_name}"
}

output "application_https_url" {
  description = "URL of the application (HTTPS)"
  value       = var.enable_https ? "https://${aws_lb.main.dns_name}" : null
}

# Monitoring URLs
output "cloudwatch_logs_url" {
  description = "URL to CloudWatch logs"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.app.name, "/", "$252F")}"
}

output "ecs_service_url" {
  description = "URL to ECS service in AWS console"
  value       = "https://console.aws.amazon.com/ecs/home?region=${data.aws_region.current.name}#/clusters/${aws_ecs_cluster.main.name}/services/${aws_ecs_service.app.name}/details"
}

# Resource Tags
output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

# Configuration Summary
output "configuration_summary" {
  description = "Summary of the deployed configuration"
  value = {
    project_name        = var.project_name
    environment         = var.environment
    container_image     = var.container_image
    container_port      = var.container_port
    task_cpu           = var.task_cpu
    task_memory        = var.task_memory
    auto_scaling_enabled = var.enable_auto_scaling
    min_capacity       = var.enable_auto_scaling ? var.auto_scaling.min_capacity : null
    max_capacity       = var.enable_auto_scaling ? var.auto_scaling.max_capacity : null
    desired_capacity   = var.auto_scaling.desired_capacity
    health_check_path  = var.health_check_path
    vpc_created        = var.create_vpc
    availability_zones = var.availability_zones
  }
}