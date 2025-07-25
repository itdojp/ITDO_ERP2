# ITDO ERP v2 - Production Operations Guide

CC03 v59.0 - Practical Production Infrastructure

## Overview

This guide covers the production deployment and operations of ITDO ERP v2 system. The infrastructure is designed for high availability, security, and scalability.

## Architecture

### Components

- **NGINX**: Reverse proxy and load balancer with SSL termination
- **Backend**: FastAPI application server with auto-scaling
- **Frontend**: React SPA served through NGINX
- **PostgreSQL**: Primary database with backup and replication
- **Redis**: Cache and session storage
- **Keycloak**: Authentication and authorization server
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notification

### Network Architecture

```
Internet -> NGINX (443/80) -> Backend (8000) -> PostgreSQL (5432)
                           -> Frontend (3000) -> Redis (6379)
                           -> Keycloak (8080)
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Minimum 8GB RAM, 4 CPU cores
- 50GB available disk space
- SSL certificates for production domains

### Initial Setup

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd ITDO_ERP2
   ```

2. **Security setup**:
   ```bash
   cd infra/scripts
   ./security-setup.sh
   ```

3. **Review configuration**:
   ```bash
   # Edit the secure environment file
   nano ../../../infra/.env.production.secure
   
   # Add your SSL certificates
   cp your-cert.pem ../nginx/ssl/cert.pem
   cp your-key.pem ../nginx/ssl/key.pem
   ```

4. **Deploy**:
   ```bash
   ./deploy.sh standard
   ```

## Deployment

### Standard Deployment

```bash
# Standard deployment (recommended for most cases)
./infra/scripts/deploy.sh standard
```

### Zero-Downtime Deployment

```bash
# Blue-Green deployment
./infra/scripts/deploy.sh blue-green

# Rolling update deployment
./infra/scripts/deploy.sh rolling
```

### Deployment Options

- **Standard**: Stop and start all services
- **Blue-Green**: Deploy to new environment, switch traffic, stop old
- **Rolling**: Update services incrementally with health checks

## Monitoring

### Access Points

- **Grafana Dashboard**: https://your-domain:3001
  - Username: admin
  - Password: (from .env.production.secure)

- **Prometheus**: https://your-domain:9090
- **Alertmanager**: https://your-domain:9093

### Key Metrics

- **Availability**: Target 99.9% uptime
- **Response Time**: Target < 500ms for API calls
- **Error Rate**: Target < 1% for HTTP 5xx errors
- **Resource Usage**: CPU < 80%, Memory < 85%, Disk < 90%

### Alerts

Critical alerts are sent to:
- Email: ops-team@itdo-erp.com
- Slack: #alerts-critical channel

## Backup & Recovery

### Automated Backups

Backups run automatically at 2:00 AM daily:

```bash
# Manual backup
./infra/scripts/backup.sh backup

# List available backups
./infra/scripts/backup.sh list

# Restore from latest backup
./infra/scripts/backup.sh restore

# Restore from specific date
./infra/scripts/backup.sh restore 20231225
```

### Backup Contents

- **Database**: Full PostgreSQL dump
- **Redis**: Data persistence files
- **Application**: Logs and user data
- **Configuration**: Environment and config files

### Recovery Procedures

1. **Database Recovery**:
   ```bash
   # Stop application
   docker compose -f infra/docker-compose.production.yml stop backend frontend
   
   # Restore database
   ./infra/scripts/backup.sh restore
   
   # Start application
   docker compose -f infra/docker-compose.production.yml start backend frontend
   ```

2. **Full System Recovery**:
   ```bash
   # Complete system restore
   ./infra/scripts/backup.sh restore
   ./infra/scripts/deploy.sh standard
   ```

## Security

### SSL/TLS Configuration

- **Certificates**: Place in `infra/nginx/ssl/`
- **Protocols**: TLS 1.2 and 1.3 only
- **Ciphers**: Strong cipher suites configured
- **HSTS**: Enabled with 1-year max-age

### Access Control

- **Firewall**: UFW configured for minimal exposure
- **Authentication**: Keycloak with SCRAM-SHA-256 for database
- **Network**: Internal Docker networks for service communication
- **Monitoring**: Access restricted to internal networks

### Security Monitoring

- **Failed logins**: Monitored and alerted
- **Suspicious traffic**: 404/403 error monitoring
- **Intrusion detection**: Fail2ban configured
- **Vulnerability scanning**: Regular container scanning

## Troubleshooting

### Common Issues

1. **Service Won't Start**:
   ```bash
   # Check logs
   docker compose -f infra/docker-compose.production.yml logs <service>
   
   # Check health
   docker compose -f infra/docker-compose.production.yml ps
   
   # Restart service
   docker compose -f infra/docker-compose.production.yml restart <service>
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database status
   docker compose -f infra/docker-compose.production.yml exec postgres pg_isready -U itdo_user
   
   # Check connections
   docker compose -f infra/docker-compose.production.yml exec postgres psql -U itdo_user -d itdo_erp -c "SELECT count(*) FROM pg_stat_activity;"
   ```

3. **High Memory Usage**:
   ```bash
   # Check container resource usage
   docker stats
   
   # Restart memory-intensive services
   docker compose -f infra/docker-compose.production.yml restart redis backend
   ```

### Log Locations

- **NGINX**: `/var/log/nginx/` (in container)
- **Backend**: `/app/logs/` (in container)
- **Database**: PostgreSQL logs via `docker logs`
- **System**: Use `docker logs <container>`

### Health Checks

```bash
# API health
curl -f https://api.your-domain.com/api/v1/health

# Frontend health
curl -f https://your-domain.com/health

# Database health
docker compose -f infra/docker-compose.production.yml exec postgres pg_isready

# Redis health
docker compose -f infra/docker-compose.production.yml exec redis redis-cli ping
```

## Maintenance

### Regular Tasks

- **Daily**: Review monitoring dashboards and alerts
- **Weekly**: Check backup integrity and test restore
- **Monthly**: Update containers and review security
- **Quarterly**: Performance review and capacity planning

### Updates

1. **Application Updates**:
   ```bash
   # Pull latest images
   docker compose -f infra/docker-compose.production.yml pull
   
   # Deploy with zero downtime
   ./infra/scripts/deploy.sh blue-green
   ```

2. **Security Updates**:
   ```bash
   # Update base system
   sudo apt update && sudo apt upgrade
   
   # Update containers
   docker compose -f infra/docker-compose.production.yml pull
   ./infra/scripts/deploy.sh rolling
   ```

### Performance Tuning

- **Database**: Adjust PostgreSQL configuration based on usage
- **Cache**: Monitor Redis memory usage and eviction
- **Web Server**: Tune NGINX worker processes and connections
- **Application**: Scale backend replicas based on load

## Support

### Emergency Contacts

- **System Administrator**: ops-team@itdo-erp.com
- **On-call Engineer**: +81-XX-XXXX-XXXX
- **Escalation**: management@itdo-erp.com

### Runbooks

- **Incident Response**: docs/runbooks/incident-response.md
- **Disaster Recovery**: docs/runbooks/disaster-recovery.md
- **Performance Issues**: docs/runbooks/performance-troubleshooting.md

### Monitoring URLs

- **Status Page**: https://status.itdo-erp.com
- **Grafana**: https://monitoring.itdo-erp.com:3001
- **Documentation**: https://docs.itdo-erp.com

---

**Last Updated**: $(date)
**Version**: CC03 v59.0
**Environment**: Production