# ITDO ERP Infrastructure as Code (Terraform)

This directory contains Terraform modules and configurations for deploying the ITDO ERP system infrastructure on AWS.

## 📁 Directory Structure

```
terraform/
├── modules/
│   └── web-app/           # Reusable web application module
│       ├── main.tf        # Main infrastructure resources
│       ├── variables.tf   # Input variables
│       └── outputs.tf     # Output values
├── environments/
│   ├── dev/              # Development environment
│   ├── staging/          # Staging environment (template)
│   └── prod/             # Production environment (template)
└── README.md             # This file
```

## 🏗️ Architecture Overview

The infrastructure follows a modular approach with:

- **VPC**: Virtual Private Cloud with public/private subnets
- **ECS Fargate**: Containerized application hosting
- **Application Load Balancer**: Load balancing and SSL termination
- **RDS PostgreSQL**: Managed database service
- **ElastiCache Redis**: Managed caching service
- **CloudWatch**: Logging and monitoring
- **Auto Scaling**: Automatic scaling based on CPU/Memory

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.5.0 installed
3. **Docker** for building container images

### Environment Setup

#### Development Environment

1. Navigate to the development environment:
   ```bash
   cd environments/dev
   ```

2. Copy and customize the variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your configuration
   ```

3. Initialize Terraform:
   ```bash
   terraform init
   ```

4. Plan the deployment:
   ```bash
   terraform plan
   ```

5. Apply the configuration:
   ```bash
   terraform apply
   ```

### Configuration Variables

Create a `terraform.tfvars` file in the environment directory:

```hcl
# AWS Configuration
aws_region = "us-west-2"

# Container Images
backend_image  = "ghcr.io/itdojp/itdo-erp-backend:latest"
frontend_image = "ghcr.io/itdojp/itdo-erp-frontend:latest"

# Database Configuration
db_name     = "itdo_erp_dev"
db_username = "itdo_user"
db_password = "secure-password-here"

# Application Configuration
secret_key = "your-secret-key-32-chars-minimum"

# Development Settings
enable_debug_mode = true
log_level         = "DEBUG"

# Alerts
alert_email = "your-email@example.com"
```

## 📦 Module: web-app

The `web-app` module provides a complete containerized web application infrastructure.

### Features

- **Auto Scaling**: CPU and memory-based scaling
- **High Availability**: Multi-AZ deployment
- **Load Balancing**: Application Load Balancer with health checks
- **Security**: Security groups and IAM roles
- **Monitoring**: CloudWatch logs and Container Insights
- **Networking**: VPC with public/private subnets

### Usage

```hcl
module "my_app" {
  source = "../../modules/web-app"
  
  project_name = "my-project"
  environment  = "dev"
  
  container_image   = "my-app:latest"
  container_port    = 8000
  health_check_path = "/health"
  
  task_cpu    = 512
  task_memory = 1024
  
  auto_scaling = {
    min_capacity        = 1
    max_capacity        = 10
    desired_capacity    = 2
    cpu_target_value    = 70.0
    memory_target_value = 80.0
  }
  
  environment_variables = {
    NODE_ENV = "production"
    API_URL  = "https://api.example.com"
  }
  
  tags = {
    Component = "backend"
    Service   = "api"
  }
}
```

## 🌍 Multi-Environment Strategy

### Environment Isolation

Each environment (dev, staging, prod) has:
- Separate AWS accounts or regions
- Independent state files
- Environment-specific configurations
- Appropriate resource sizing

### Promotion Strategy

1. **Development**: Fast iteration, cost-optimized
2. **Staging**: Production-like for testing
3. **Production**: High availability, performance optimized

## 🔐 Security Best Practices

### State Management

- **Remote State**: Use S3 backend with DynamoDB locking
- **Encryption**: Enable state encryption
- **Versioning**: Enable S3 versioning for state files

### Access Control

- **IAM Roles**: Use least-privilege IAM roles
- **MFA**: Require MFA for production deployments
- **VPC**: Private subnets for application and database

### Secrets Management

- **AWS Systems Manager**: Store secrets in Parameter Store
- **Encryption**: Encrypt secrets at rest and in transit
- **Rotation**: Implement secret rotation policies

## 📊 Monitoring and Alerting

### CloudWatch Integration

- **Container Insights**: ECS cluster and service metrics
- **Custom Metrics**: Application-specific metrics
- **Log Aggregation**: Centralized logging
- **Alarms**: CPU, memory, and error rate alerts

### Dashboard Setup

```hcl
# Example CloudWatch dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", module.backend.ecs_service_name],
            [".", "MemoryUtilization", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ECS Service Metrics"
        }
      }
    ]
  })
}
```

## 💰 Cost Optimization

### Development Environment

- **Instance Sizing**: Use smaller instances (t3.micro, t3.small)
- **Auto Shutdown**: Schedule stop/start for non-business hours
- **Resource Limits**: Lower auto-scaling maximums
- **Short Retention**: Reduce log retention periods

### Monitoring Costs

```hcl
# Cost budgets
resource "aws_budgets_budget" "dev_cost" {
  name         = "itdo-erp-dev-monthly"
  budget_type  = "COST"
  limit_amount = "100"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  
  cost_filters = {
    TagKey = ["Environment"]
    TagValues = ["dev"]
  }
}
```

## 🔧 Maintenance and Updates

### Infrastructure Updates

1. **Plan Changes**: Always run `terraform plan` first
2. **Test in Dev**: Apply changes to development first
3. **Gradual Rollout**: Apply to staging, then production
4. **Backup**: Ensure backups before major changes

### Container Updates

```bash
# Update container images
terraform apply -var="backend_image=ghcr.io/itdojp/itdo-erp-backend:v1.2.0"
```

### Database Migrations

```hcl
# Database migration job
resource "aws_ecs_task_definition" "migration" {
  family = "${var.project_name}-${var.environment}-migration"
  # ... configuration for migration task
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Service Not Starting**
   - Check CloudWatch logs
   - Verify container image exists
   - Check environment variables and secrets

2. **Load Balancer Health Checks Failing**
   - Verify health check path
   - Check security group rules
   - Ensure application responds on correct port

3. **Database Connection Issues**
   - Verify security group rules
   - Check database endpoint and credentials
   - Ensure database is in correct subnet group

### Debugging Commands

```bash
# View ECS service events
aws ecs describe-services --cluster <cluster-name> --services <service-name>

# View task logs
aws logs tail /ecs/<project>-<environment> --follow

# Check load balancer health
aws elbv2 describe-target-health --target-group-arn <target-group-arn>
```

## 📚 Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## 🤝 Contributing

1. Create feature branch
2. Test changes in development environment
3. Update documentation
4. Submit pull request with infrastructure changes

## 📞 Support

For infrastructure-related issues:
- Check CloudWatch logs and metrics
- Review Terraform plan output
- Consult AWS documentation
- Contact the DevOps team