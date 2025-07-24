# Web Application Infrastructure Module
# Provides containerized web application infrastructure with auto-scaling, load balancing, and monitoring

terraform {
  required_version = ">= 1.5.0"
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
}

# Local values for computed configurations
locals {
  common_tags = merge(var.tags, {
    Module      = "web-app"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  })
  
  container_port = var.container_port
  health_check_path = var.health_check_path
  
  # Auto-scaling configuration
  min_capacity = var.auto_scaling.min_capacity
  max_capacity = var.auto_scaling.max_capacity
  desired_capacity = var.auto_scaling.desired_capacity
}

# VPC Configuration
resource "aws_vpc" "main" {
  count = var.create_vpc ? 1 : 0
  
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  count = var.create_vpc ? 1 : 0
  
  vpc_id = aws_vpc.main[0].id
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-igw"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = var.create_vpc ? length(var.availability_zones) : 0
  
  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-public-${count.index + 1}"
    Type = "public"
  })
}

# Private Subnets
resource "aws_subnet" "private" {
  count = var.create_vpc ? length(var.availability_zones) : 0
  
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.availability_zones[count.index]
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-private-${count.index + 1}"
    Type = "private"
  })
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  count = var.create_vpc ? 1 : 0
  
  vpc_id = aws_vpc.main[0].id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-public-rt"
  })
}

# Route Table Associations for Public Subnets
resource "aws_route_table_association" "public" {
  count = var.create_vpc ? length(aws_subnet.public) : 0
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

# Security Group for Load Balancer
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-${var.environment}-alb-"
  vpc_id      = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  })
  
  lifecycle {
    create_before_destroy = true
  }
}

# Security Group for Application
resource "aws_security_group" "app" {
  name_prefix = "${var.project_name}-${var.environment}-app-"
  vpc_id      = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  
  ingress {
    description     = "Application Port"
    from_port       = local.container_port
    to_port         = local.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-app-sg"
  })
  
  lifecycle {
    create_before_destroy = true
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = var.create_vpc ? aws_subnet.public[*].id : var.public_subnet_ids
  
  enable_deletion_protection = var.environment == "prod" ? true : false
  
  tags = local.common_tags
}

# Target Group
resource "aws_lb_target_group" "app" {
  name     = "${var.project_name}-${var.environment}-tg"
  port     = local.container_port
  protocol = "HTTP"
  vpc_id   = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = local.health_check_path
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }
  
  tags = local.common_tags
  
  lifecycle {
    create_before_destroy = true
  }
}

# Load Balancer Listener
resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
  
  tags = local.common_tags
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }
  
  tags = local.common_tags
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([
    {
      name      = var.container_name
      image     = var.container_image
      cpu       = var.task_cpu
      memory    = var.task_memory
      essential = true
      
      portMappings = [
        {
          containerPort = local.container_port
          protocol      = "tcp"
        }
      ]
      
      environment = [
        for key, value in var.environment_variables : {
          name  = key
          value = value
        }
      ]
      
      secrets = [
        for key, value in var.secrets : {
          name      = key
          valueFrom = value
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${local.container_port}${local.health_check_path} || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
  
  tags = local.common_tags
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "${var.project_name}-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = local.desired_capacity
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.create_vpc ? aws_subnet.private[*].id : var.private_subnet_ids
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = var.container_name
    container_port   = local.container_port
  }
  
  depends_on = [aws_lb_listener.app]
  
  tags = local.common_tags
  
  lifecycle {
    ignore_changes = [desired_count]
  }
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "ecs_target" {
  count = var.enable_auto_scaling ? 1 : 0
  
  max_capacity       = local.max_capacity
  min_capacity       = local.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
  
  tags = local.common_tags
}

# Auto Scaling Policy - CPU
resource "aws_appautoscaling_policy" "ecs_cpu_policy" {
  count = var.enable_auto_scaling ? 1 : 0
  
  name               = "${var.project_name}-${var.environment}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = var.auto_scaling.cpu_target_value
  }
}

# Auto Scaling Policy - Memory
resource "aws_appautoscaling_policy" "ecs_memory_policy" {
  count = var.enable_auto_scaling ? 1 : 0
  
  name               = "${var.project_name}-${var.environment}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = var.auto_scaling.memory_target_value
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days
  
  tags = local.common_tags
}

# IAM Role for ECS Execution
resource "aws_iam_role" "ecs_execution" {
  name = "${var.project_name}-${var.environment}-ecs-execution"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-${var.environment}-ecs-task"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# Data source for current AWS region
data "aws_region" "current" {}

# Data source for current AWS caller identity
data "aws_caller_identity" "current" {}