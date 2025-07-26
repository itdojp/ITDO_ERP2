# ITDO ERP Terraform Outputs
# Output values for infrastructure components

# ============================================================================
# Cluster Information
# ============================================================================

output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = aws_iam_role.eks_cluster.name
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN associated with EKS cluster"
  value       = aws_iam_role.eks_cluster.arn
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_version" {
  description = "The Kubernetes version for the EKS cluster"
  value       = aws_eks_cluster.main.version
}

# ============================================================================
# Node Group Information
# ============================================================================

output "node_groups" {
  description = "EKS node groups"
  value = {
    system = {
      arn           = aws_eks_node_group.system.arn
      status        = aws_eks_node_group.system.status
      capacity_type = aws_eks_node_group.system.capacity_type
      instance_types = aws_eks_node_group.system.instance_types
      scaling_config = aws_eks_node_group.system.scaling_config
    }
    application = {
      arn           = aws_eks_node_group.application.arn
      status        = aws_eks_node_group.application.status
      capacity_type = aws_eks_node_group.application.capacity_type
      instance_types = aws_eks_node_group.application.instance_types
      scaling_config = aws_eks_node_group.application.scaling_config
    }
  }
}

output "node_security_group_id" {
  description = "ID of the EKS node shared security group"
  value       = aws_security_group.eks_nodes.id
}

output "node_iam_role_name" {
  description = "IAM role name associated with EKS node group"
  value       = aws_iam_role.eks_nodes.name
}

output "node_iam_role_arn" {
  description = "IAM role ARN associated with EKS node group"
  value       = aws_iam_role.eks_nodes.arn
}

# ============================================================================
# Networking Information
# ============================================================================

output "vpc_id" {
  description = "ID of the VPC where the cluster and workers are deployed"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "nat_gateway_ids" {
  description = "List of IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

# ============================================================================
# Database Information
# ============================================================================

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.db_name
}

output "rds_username" {
  description = "RDS database username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "rds_security_group_id" {
  description = "Security group ID for RDS"
  value       = aws_security_group.rds.id
}

# ============================================================================
# Cache Information
# ============================================================================

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
  sensitive   = true
}

output "redis_port" {
  description = "Redis cluster port"
  value       = aws_elasticache_replication_group.main.port
}

output "redis_auth_token_enabled" {
  description = "Whether Redis auth token is enabled"
  value       = aws_elasticache_replication_group.main.auth_token != null
}

output "redis_security_group_id" {
  description = "Security group ID for Redis"
  value       = aws_security_group.elasticache.id
}

# ============================================================================
# Storage Information
# ============================================================================

output "s3_app_storage_bucket" {
  description = "Name of the S3 bucket for application storage"
  value       = aws_s3_bucket.app_storage.id
}

output "s3_app_storage_bucket_arn" {
  description = "ARN of the S3 bucket for application storage"
  value       = aws_s3_bucket.app_storage.arn
}

output "s3_backups_bucket" {
  description = "Name of the S3 bucket for backups"
  value       = aws_s3_bucket.backups.id
}

output "s3_backups_bucket_arn" {
  description = "ARN of the S3 bucket for backups"
  value       = aws_s3_bucket.backups.arn
}

# ============================================================================
# Security Information
# ============================================================================

output "kms_key_id" {
  description = "The globally unique identifier for the KMS key"
  value       = aws_kms_key.eks.key_id
}

output "kms_key_arn" {
  description = "The Amazon Resource Name (ARN) of the KMS key"
  value       = aws_kms_key.eks.arn
}

output "security_groups" {
  description = "Security groups created for the cluster and services"
  value = {
    cluster     = aws_security_group.eks_cluster.id
    nodes       = aws_security_group.eks_nodes.id
    rds         = aws_security_group.rds.id
    elasticache = aws_security_group.elasticache.id
  }
}

# ============================================================================
# Configuration Information
# ============================================================================

output "region" {
  description = "AWS region"
  value       = var.aws_region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

# ============================================================================
# Kubernetes Configuration
# ============================================================================

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}

output "kubectl_config" {
  description = "kubectl config as generated by the module"
  value = {
    cluster_name                     = aws_eks_cluster.main.name
    endpoint                        = aws_eks_cluster.main.endpoint
    region                          = var.aws_region
    certificate_authority_data      = aws_eks_cluster.main.certificate_authority[0].data
  }
  sensitive = true
}

# ============================================================================
# Monitoring and Logging
# ============================================================================

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for EKS cluster logs"
  value       = aws_cloudwatch_log_group.eks.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group for EKS cluster logs"
  value       = aws_cloudwatch_log_group.eks.arn
}

# ============================================================================
# Load Balancer Information
# ============================================================================

output "load_balancer_dns_name" {
  description = "DNS name of the load balancer (available after deployment)"
  value       = "Will be available after Kubernetes ingress deployment"
}

# ============================================================================
# Connection Information
# ============================================================================

output "connection_info" {
  description = "Information for connecting to the infrastructure"
  value = {
    cluster_name = aws_eks_cluster.main.name
    region       = var.aws_region
    environment  = var.environment
    
    # Database connection (for applications)
    database = {
      host     = aws_db_instance.main.endpoint
      port     = aws_db_instance.main.port
      database = aws_db_instance.main.db_name
      # Note: credentials should be managed via Kubernetes secrets
    }
    
    # Cache connection (for applications)
    redis = {
      host = aws_elasticache_replication_group.main.primary_endpoint_address
      port = aws_elasticache_replication_group.main.port
      # Note: auth token should be managed via Kubernetes secrets
    }
    
    # Storage information
    storage = {
      app_bucket     = aws_s3_bucket.app_storage.id
      backups_bucket = aws_s3_bucket.backups.id
    }
  }
  sensitive = true
}

# ============================================================================
# Helm Values Override
# ============================================================================

output "helm_values_override" {
  description = "Helm values to override for ITDO ERP deployment"
  value = {
    global = {
      environment = var.environment
      region      = var.aws_region
    }
    
    postgresql = {
      external = {
        enabled  = true
        host     = aws_db_instance.main.endpoint
        port     = aws_db_instance.main.port
        database = aws_db_instance.main.db_name
      }
    }
    
    redis = {
      external = {
        enabled = true
        host    = aws_elasticache_replication_group.main.primary_endpoint_address
        port    = aws_elasticache_replication_group.main.port
      }
    }
    
    external = {
      objectStorage = {
        enabled = true
        bucket  = aws_s3_bucket.app_storage.id
        region  = var.aws_region
      }
    }
  }
  sensitive = true
}

# ============================================================================
# Cost Estimation
# ============================================================================

output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (USD)"
  value = {
    eks_cluster    = "73.00"  # $0.10/hour
    system_nodes   = "146.00" # 2 x t3.medium
    app_nodes      = "438.00" # 3 x m5.large (spot pricing)
    rds           = "146.00" # db.t3.medium
    redis         = "73.00"  # cache.t3.medium
    storage       = "50.00"  # S3 + EBS volumes
    data_transfer = "100.00"
    total         = "~1026.00"
    note          = "Actual costs may vary based on usage patterns and spot instance availability"
  }
}

# ============================================================================
# Next Steps Information
# ============================================================================

output "next_steps" {
  description = "Next steps for completing the deployment"
  value = [
    "1. Configure kubectl: ${aws_eks_cluster.main.name}",
    "2. Install AWS Load Balancer Controller",
    "3. Install cert-manager for SSL certificates",
    "4. Deploy ITDO ERP using Helm chart",
    "5. Configure DNS records for your domain",
    "6. Set up monitoring and alerting",
    "7. Configure backup procedures",
    "8. Review security configurations"
  ]
}