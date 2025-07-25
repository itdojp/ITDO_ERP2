# ITDO ERP v2 - Clean Production Infrastructure

**CC03 v60.0 - Clean Production Implementation**

## 🎯 Overview

This is a clean, streamlined production infrastructure for ITDO ERP v2, designed with simplicity, security, and maintainability in mind. Unlike complex enterprise setups, this implementation focuses on essential components with clear, understandable configurations.

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Internet  │────│    NGINX    │────│  Application│
│   Traffic   │    │ (SSL + LB)  │    │   Services  │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                   ┌─────────────┐    ┌─────────────┐
                   │  Frontend   │    │  Database   │
                   │   React     │    │   Layer     │
                   └─────────────┘    └─────────────┘
                           │                   │
                   ┌─────────────┐    ┌─────────────┐
                   │ Monitoring  │    │   Backup    │
                   │   Stack     │    │   System    │
                   └─────────────┘    └─────────────┘
```

### Core Services

- **NGINX**: Reverse proxy with SSL termination and load balancing
- **Frontend**: React application served via optimized container
- **Backend**: FastAPI application with health checks
- **PostgreSQL**: Primary database with security hardening
- **Redis**: Cache and session storage
- **Keycloak**: Authentication and authorization server
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Visualization dashboards
- **Alertmanager**: Alert routing and notifications

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Minimum 4GB RAM, 2 CPU cores
- 20GB available disk space

### 1. Security Setup

```bash
cd infra-clean/security
./setup-ssl.sh
```

This will:
- Generate SSL certificates (replace with production certificates)
- Create secure environment configuration
- Set up strong passwords for all services

### 2. Deploy Production Stack

```bash
cd infra-clean/scripts
./deploy.sh standard
```

### 3. Access Services

- **Main Application**: https://itdo-erp.com
- **API Endpoints**: https://api.itdo-erp.com
- **Authentication**: https://auth.itdo-erp.com
- **Monitoring**: https://monitoring.itdo-erp.com (internal networks only)

## 📁 Directory Structure

```
infra-clean/
├── compose/
│   ├── docker-compose.production.yml  # Main production stack
│   ├── .env.production                # Environment template
│   └── .env.production.secure         # Generated secure config
├── nginx/
│   ├── nginx.conf                     # NGINX configuration
│   └── ssl/                           # SSL certificates
├── monitoring/
│   ├── prometheus.yml                 # Metrics collection
│   ├── rules.yml                      # Alert rules
│   ├── alertmanager.yml               # Alert routing
│   └── grafana/                       # Dashboard provisioning
├── security/
│   ├── postgres.conf                  # Database security
│   ├── redis.conf                     # Cache security
│   └── setup-ssl.sh                   # Security setup script
├── scripts/
│   ├── deploy.sh                      # Deployment automation
│   └── backup.sh                      # Backup management
└── README.md                          # This file
```

## 🔧 Deployment Strategies

### Standard Deployment
Quick deployment with brief downtime:
```bash
./deploy.sh standard
```

### Rolling Deployment
Zero-downtime deployment updating services incrementally:
```bash
./deploy.sh rolling
```

### Blue-Green Deployment
Zero-downtime deployment with complete environment switch:
```bash
./deploy.sh blue-green
```

## 📊 Monitoring & Alerting

### Access Points
- **Grafana**: Port 3001 - Visualization dashboards
- **Prometheus**: Port 9090 - Metrics and queries
- **Alertmanager**: Port 9093 - Alert management

### Key Metrics Monitored
- Application availability and response times
- Database connections and performance
- Resource usage (CPU, memory, disk)
- Security events and failed logins
- Infrastructure health and capacity

### Alert Categories
- **Critical**: Service down, security incidents
- **Warning**: High resource usage, performance degradation
- **Info**: Deployment events, routine maintenance

## 🔒 Security Features

### Network Security
- SSL/TLS encryption with strong ciphers
- HSTS enabled with 1-year max-age
- Security headers (CSP, XSS protection, etc.)
- Rate limiting and DDoS protection

### Authentication & Authorization
- Keycloak OAuth2/OpenID Connect integration
- SCRAM-SHA-256 database authentication
- Strong password generation for all services
- Network isolation between service layers

### Data Protection
- Database connection encryption
- Redis authentication and command restrictions
- Firewall rules limiting access to monitoring ports
- Regular security log monitoring

## 💾 Backup & Recovery

### Automated Backups
```bash
# Create full backup
./backup.sh backup

# List available backups
./backup.sh list

# Restore from backup
./backup.sh restore /path/to/backup.sql.gz

# Cleanup old backups (30+ days)
./backup.sh cleanup
```

### Backup Contents
- **Database**: Full PostgreSQL dump with compression
- **Redis**: Data persistence files
- **Logs**: Application and system logs
- **Configuration**: Environment and config files

### Retention Policy
- Daily automated backups
- 30-day retention period
- Backup integrity verification
- Compressed storage to minimize space usage

## 🛠️ Operations

### Health Checks
```bash
# Check deployment status
./deploy.sh status

# Validate current deployment
./deploy.sh validate

# View service logs
docker compose -f ../compose/docker-compose.production.yml logs -f
```

### Scaling
```bash
# Scale backend services
docker compose -f ../compose/docker-compose.production.yml up -d --scale backend=3

# Resource monitoring
docker stats
```

### Troubleshooting

#### Service Won't Start
1. Check logs: `docker compose logs <service>`
2. Verify environment file exists and is properly configured
3. Ensure SSL certificates are present
4. Check disk space and memory availability

#### Performance Issues
1. Monitor resource usage: `docker stats`
2. Check database connections: Monitor PostgreSQL metrics
3. Review NGINX access logs for traffic patterns
4. Scale services horizontally if needed

#### Security Alerts
1. Review Alertmanager notifications
2. Check authentication logs in Keycloak
3. Monitor failed login attempts via Prometheus metrics
4. Verify firewall rules and network access

## 🔄 Maintenance

### Regular Tasks
- **Daily**: Review monitoring dashboards and alerts
- **Weekly**: Check backup integrity and test restore process
- **Monthly**: Update containers and review security configurations
- **Quarterly**: Performance review and capacity planning

### Updates
```bash
# Pull latest container images
docker compose -f ../compose/docker-compose.production.yml pull

# Deploy with zero downtime
./deploy.sh rolling
```

## 📈 Performance Targets

- **Availability**: 99.9% uptime (8.77 hours downtime/year max)
- **API Response Time**: < 500ms for most endpoints
- **Database Response**: < 100ms for typical queries
- **SSL Handshake**: < 200ms
- **Page Load Time**: < 2 seconds for frontend

## 🆘 Support & Escalation

### Emergency Contacts
- **Operations Team**: ops-team@itdo-erp.com
- **Critical Issues**: alerts-critical@itdo-erp.com
- **Security Incidents**: security@itdo-erp.com

### Rollback Procedure
```bash
# Emergency rollback
./deploy.sh rollback

# Restore from backup if needed
./backup.sh restore <backup-file>
```

## 📝 Configuration Notes

### Environment Variables
All sensitive configuration is stored in `.env.production.secure`. Key variables:
- Database credentials and connection strings
- Authentication secrets and API keys
- SSL certificate paths
- Monitoring and alerting endpoints

### SSL Certificates
- Self-signed certificates are generated for development
- Replace with production certificates before deployment
- Certificates are automatically included in NGINX configuration
- Strong cipher suites and protocols enforced

### Resource Limits
Services have defined resource limits to prevent resource exhaustion:
- PostgreSQL: 2GB memory, 1 CPU
- Redis: 512MB memory, 0.5 CPU
- Other services: Reasonable defaults based on expected load

## 🎉 Features

✅ **Production Ready**: Immediate deployment capability  
✅ **Zero Downtime**: Multiple deployment strategies  
✅ **Comprehensive Monitoring**: Prometheus + Grafana + Alertmanager  
✅ **Security Hardened**: SSL, authentication, network isolation  
✅ **Automated Backups**: Daily backups with restore capability  
✅ **Easy Maintenance**: Clear documentation and automation scripts  
✅ **Scalable Architecture**: Horizontal scaling support

---

**CC03 v60.0 - Clean Production Implementation**  
*Simple, Secure, Reliable*