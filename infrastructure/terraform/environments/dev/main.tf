# Development Environment Infrastructure
# This configuration deploys the ITDO ERP system to the development environment

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration for state management
  backend "s3" {
    # bucket         = "itdo-erp-terraform-state-dev"
    # key            = "environments/dev/terraform.tfstate"
    # region         = "us-west-2"
    # encrypt        = true
    # dynamodb_table = "itdo-erp-terraform-locks"
    
    # Uncomment and configure the above when ready to use remote state
    # For development, local state is acceptable
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment   = "dev"
      Project       = "itdo-erp"
      Owner         = "development-team"
      ManagedBy     = "terraform"
      CostCenter    = "development"
      BackupPolicy  = "dev-backup"
      CreatedBy     = "cc03-terraform-automation"
    }
  }
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Backend Application
module "backend" {
  source = "../../modules/web-app"
  
  project_name = "itdo-erp-backend"
  environment  = "dev"
  
  # Container configuration
  container_image   = var.backend_image
  container_name    = "backend"
  container_port    = 8000
  health_check_path = "/health"
  
  # ECS configuration
  task_cpu    = 512   # 0.5 vCPU for dev
  task_memory = 1024  # 1GB for dev
  
  # Auto scaling configuration (lighter for dev)
  enable_auto_scaling = true
  auto_scaling = {
    min_capacity        = 1
    max_capacity        = 3  # Lower for dev
    desired_capacity    = 1  # Start with 1 for dev
    cpu_target_value    = 80.0
    memory_target_value = 85.0
  }
  
  # Network configuration
  create_vpc         = true
  vpc_cidr          = "10.1.0.0/16"  # Different CIDR for dev
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)
  
  # Environment variables for backend
  environment_variables = {
    ENVIRONMENT                = "development"
    DEBUG                     = "true"
    LOG_LEVEL                 = "DEBUG"
    DATABASE_URL              = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${var.db_name}"
    REDIS_URL                 = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
    BACKEND_CORS_ORIGINS      = "http://localhost:3000,https://${module.frontend.load_balancer_dns_name}"
    SECRET_KEY                = var.secret_key
    PYTHONPATH                = "/app"
    TESTING                   = "false"
  }
  
  # Secrets (using AWS Systems Manager Parameter Store)
  secrets = {
    DATABASE_PASSWORD = "/itdo-erp/dev/database/password"
    SECRET_KEY_SECURE = "/itdo-erp/dev/app/secret-key"
  }
  
  # Monitoring configuration
  enable_container_insights = true
  log_retention_days       = 7  # Shorter retention for dev
  
  # Tags
  tags = {
    Component     = "backend"
    Service       = "api"
    Database      = "postgresql"
    Cache         = "redis"
  }
}

# Frontend Application
module "frontend" {
  source = "../../modules/web-app"
  
  project_name = "itdo-erp-frontend"
  environment  = "dev"
  
  # Container configuration
  container_image   = var.frontend_image
  container_name    = "frontend"
  container_port    = 3000
  health_check_path = "/"
  
  # ECS configuration (lighter for frontend)
  task_cpu    = 256   # 0.25 vCPU for dev frontend
  task_memory = 512   # 512MB for dev frontend
  
  # Auto scaling configuration
  enable_auto_scaling = true
  auto_scaling = {
    min_capacity        = 1
    max_capacity        = 2  # Lower for dev
    desired_capacity    = 1
    cpu_target_value    = 70.0
    memory_target_value = 80.0
  }
  
  # Use existing VPC from backend
  create_vpc           = false
  vpc_id              = module.backend.vpc_id
  public_subnet_ids   = module.backend.public_subnet_ids
  private_subnet_ids  = module.backend.private_subnet_ids
  
  # Environment variables for frontend
  environment_variables = {
    NODE_ENV              = "development"
    VITE_API_URL         = "https://${module.backend.load_balancer_dns_name}"
    VITE_API_BASE_URL    = "https://${module.backend.load_balancer_dns_name}/api/v1"
    VITE_APP_NAME        = "ITDO ERP - Development"
    VITE_ENVIRONMENT     = "development"
  }
  
  # Monitoring configuration
  enable_container_insights = true
  log_retention_days       = 7
  
  # Tags
  tags = {
    Component = "frontend"
    Service   = "web"
    Framework = "react"
  }
  
  depends_on = [module.backend]
}

# PostgreSQL Database
resource "aws_db_subnet_group" "postgres" {
  name       = "itdo-erp-dev-postgres"
  subnet_ids = module.backend.private_subnet_ids
  
  tags = {
    Name        = "itdo-erp-dev-postgres-subnet-group"
    Environment = "dev"
    Service     = "database"
  }
}

resource "aws_security_group" "postgres" {
  name_prefix = "itdo-erp-dev-postgres-"
  vpc_id      = module.backend.vpc_id
  
  ingress {
    description     = "PostgreSQL"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.backend.app_security_group_id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name        = "itdo-erp-dev-postgres-sg"
    Environment = "dev"
    Service     = "database"
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_db_instance" "postgres" {
  identifier = "itdo-erp-dev-postgres"
  
  # Engine configuration
  engine         = "postgres"
  engine_version = "15.7"
  instance_class = "db.t3.micro"  # Small instance for dev
  
  # Storage configuration
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type         = "gp2"
  storage_encrypted    = true
  
  # Database configuration
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 5432
  
  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.postgres.id]
  publicly_accessible    = false
  
  # Backup configuration (minimal for dev)
  backup_retention_period = 1  # 1 day for dev
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Performance configuration
  multi_az               = false  # Single AZ for dev
  performance_insights_enabled = false
  
  # Deletion configuration
  skip_final_snapshot       = true  # Allow deletion without snapshot in dev
  deletion_protection       = false
  delete_automated_backups  = true
  
  tags = {
    Name        = "itdo-erp-dev-postgres"
    Environment = "dev"
    Service     = "database"
    Engine      = "postgresql"
  }
}

# Redis Cache
resource "aws_elasticache_subnet_group" "redis" {
  name       = "itdo-erp-dev-redis"
  subnet_ids = module.backend.private_subnet_ids
  
  tags = {
    Name        = "itdo-erp-dev-redis-subnet-group"
    Environment = "dev"
    Service     = "cache"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "itdo-erp-dev-redis-"
  vpc_id      = module.backend.vpc_id
  
  ingress {
    description     = "Redis"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.backend.app_security_group_id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name        = "itdo-erp-dev-redis-sg"
    Environment = "dev"
    Service     = "cache"
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "itdo-erp-dev-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"  # Small instance for dev
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  
  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]
  
  # Backup configuration (minimal for dev)
  snapshot_retention_limit = 1
  snapshot_window         = "03:00-05:00"
  maintenance_window      = "sun:05:00-sun:06:00"
  
  tags = {
    Name        = "itdo-erp-dev-redis"
    Environment = "dev"
    Service     = "cache"
    Engine      = "redis"
  }
}