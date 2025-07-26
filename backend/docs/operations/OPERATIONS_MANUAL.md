# ITDO ERP System v2 - Operations & Maintenance Manual

## 📋 Overview

This manual provides comprehensive guidance for the daily operations, monitoring, maintenance, and troubleshooting of the ITDO ERP System v2. It is designed for system administrators, DevOps engineers, and technical support teams.

## 🎯 Target Audience

- **System Administrators**: Daily operations and monitoring
- **DevOps Engineers**: Deployment and infrastructure management
- **Technical Support**: Issue resolution and user support
- **Database Administrators**: Database maintenance and optimization

## 🔧 System Operations

### Daily Operations Checklist

#### Morning Startup Verification (9:00 AM)
```bash
# 1. Check system health
curl -f http://localhost:8000/health

# 2. Verify database connectivity
sudo -u postgres psql -d itdo_erp_db -c "SELECT 1;"

# 3. Check Redis status
redis-cli ping

# 4. Verify disk space
df -h

# 5. Check memory usage
free -m

# 6. Review overnight logs
sudo journalctl -u itdo-erp --since "yesterday" | grep -i error
```

#### Evening Maintenance (6:00 PM)
```bash
# 1. Backup database
./scripts/backup-database.sh

# 2. Analyze database performance
sudo -u postgres psql -d itdo_erp_db -c "ANALYZE;"

# 3. Rotate logs
sudo logrotate -f /etc/logrotate.d/itdo-erp

# 4. Check system updates
sudo apt list --upgradable
```

### Service Management

#### Backend Application Service
```bash
# Start service
sudo systemctl start itdo-erp

# Stop service
sudo systemctl stop itdo-erp

# Restart service
sudo systemctl restart itdo-erp

# Check status
sudo systemctl status itdo-erp

# View logs
sudo journalctl -u itdo-erp -f

# Reload configuration
sudo systemctl reload itdo-erp
```

#### Database Service (PostgreSQL)
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Stop PostgreSQL
sudo systemctl stop postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Check status
sudo systemctl status postgresql

# View logs
sudo journalctl -u postgresql -f
```

#### Cache Service (Redis)
```bash
# Start Redis
sudo systemctl start redis

# Stop Redis
sudo systemctl stop redis

# Restart Redis
sudo systemctl restart redis

# Check status
sudo systemctl status redis

# Monitor Redis
redis-cli monitor
```

#### Web Server (Nginx)
```bash
# Start Nginx
sudo systemctl start nginx

# Stop Nginx
sudo systemctl stop nginx

# Restart Nginx
sudo systemctl restart nginx

# Reload configuration
sudo systemctl reload nginx

# Test configuration
sudo nginx -t

# Check status
sudo systemctl status nginx
```

## 📊 Monitoring & Alerting

### System Health Monitoring

#### Automated Health Checks
```bash
#!/bin/bash
# File: /opt/itdo-erp/scripts/health-check.sh

LOG_FILE="/var/log/itdo-erp/health-check.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting health check..." >> $LOG_FILE

# Check backend service
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "[$DATE] Backend: OK" >> $LOG_FILE
else
    echo "[$DATE] Backend: FAILED" >> $LOG_FILE
    # Send alert
    echo "ITDO ERP Backend is down" | mail -s "ALERT: Backend Service Down" admin@itdo.com
fi

# Check database
if sudo -u postgres psql -d itdo_erp_db -c "SELECT 1;" > /dev/null 2>&1; then
    echo "[$DATE] Database: OK" >> $LOG_FILE
else
    echo "[$DATE] Database: FAILED" >> $LOG_FILE
    echo "ITDO ERP Database is down" | mail -s "ALERT: Database Down" admin@itdo.com
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "[$DATE] Redis: OK" >> $LOG_FILE
else
    echo "[$DATE] Redis: FAILED" >> $LOG_FILE
    echo "ITDO ERP Redis is down" | mail -s "ALERT: Redis Down" admin@itdo.com
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "[$DATE] Disk: WARNING - ${DISK_USAGE}% used" >> $LOG_FILE
    echo "Disk usage is at ${DISK_USAGE}%" | mail -s "WARNING: High Disk Usage" admin@itdo.com
else
    echo "[$DATE] Disk: OK - ${DISK_USAGE}% used" >> $LOG_FILE
fi

echo "[$DATE] Health check completed" >> $LOG_FILE
```

#### Crontab Configuration
```bash
# Add to crontab (crontab -e)
# Health check every 5 minutes
*/5 * * * * /opt/itdo-erp/scripts/health-check.sh

# Database backup daily at 2 AM
0 2 * * * /opt/itdo-erp/scripts/backup-database.sh

# Log rotation daily at 3 AM
0 3 * * * /usr/sbin/logrotate -f /etc/logrotate.d/itdo-erp

# System cleanup weekly on Sunday at 4 AM
0 4 * * 0 /opt/itdo-erp/scripts/cleanup.sh
```

### Performance Monitoring

#### Database Performance
```sql
-- Monitor active connections
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    tup_returned,
    tup_fetched,
    tup_inserted,
    tup_updated,
    tup_deleted
FROM pg_stat_database 
WHERE datname = 'itdo_erp_db';

-- Monitor slow queries
SELECT 
    query,
    mean_time,
    calls,
    total_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Monitor table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Application Performance
```bash
# Monitor API response times
curl -w "@curl-format.txt" -o /dev/null http://localhost:8000/health

# curl-format.txt content:
# time_namelookup:  %{time_namelookup}\n
# time_connect:     %{time_connect}\n
# time_appconnect:  %{time_appconnect}\n
# time_pretransfer: %{time_pretransfer}\n
# time_redirect:    %{time_redirect}\n
# time_starttransfer: %{time_starttransfer}\n
# time_total:       %{time_total}\n

# Monitor memory usage
ps aux | grep uvicorn | awk '{print $6/1024 " MB"}'

# Monitor CPU usage
top -p $(pgrep -f uvicorn) -b -n 1 | tail -n +8
```

### Log Management

#### Log Locations
```bash
# Application logs
/var/log/itdo-erp/app.log
/var/log/itdo-erp/error.log
/var/log/itdo-erp/access.log

# System logs
/var/log/syslog
/var/log/auth.log

# Service logs (systemd)
sudo journalctl -u itdo-erp
sudo journalctl -u postgresql
sudo journalctl -u redis
sudo journalctl -u nginx
```

#### Log Analysis Commands
```bash
# Count error logs by type
grep -i error /var/log/itdo-erp/app.log | awk '{print $4}' | sort | uniq -c

# Find top IP addresses
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -10

# Monitor real-time errors
tail -f /var/log/itdo-erp/error.log | grep -i "error\|warning\|critical"

# Search for specific error patterns
grep -r "500 Internal Server Error" /var/log/nginx/

# Analyze response times
awk '{print $NF}' /var/log/nginx/access.log | sort -n | tail -20
```

## 🔄 Backup & Recovery

### Database Backup

#### Automated Backup Script
```bash
#!/bin/bash
# File: /opt/itdo-erp/scripts/backup-database.sh

BACKUP_DIR="/opt/itdo-erp/backups"
DATE=$(date '+%Y%m%d_%H%M%S')
DB_NAME="itdo_erp_db"
DB_USER="itdo_user"
BACKUP_FILE="${BACKUP_DIR}/itdo_erp_backup_${DATE}.sql"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create database backup
echo "Starting database backup..."
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "Database backup completed: $BACKUP_FILE"
    
    # Compress backup
    gzip $BACKUP_FILE
    echo "Backup compressed: ${BACKUP_FILE}.gz"
    
    # Remove old backups
    find $BACKUP_DIR -name "itdo_erp_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned up"
    
    # Log success
    echo "$(date '+%Y-%m-%d %H:%M:%S') Backup completed successfully" >> /var/log/itdo-erp/backup.log
else
    echo "Database backup failed!"
    echo "$(date '+%Y-%m-%d %H:%M:%S') Backup failed" >> /var/log/itdo-erp/backup.log
    # Send alert
    echo "Database backup failed" | mail -s "ALERT: Backup Failed" admin@itdo.com
    exit 1
fi
```

#### Database Restore
```bash
#!/bin/bash
# File: /opt/itdo-erp/scripts/restore-database.sh

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

BACKUP_FILE=$1
DB_NAME="itdo_erp_db"
DB_USER="itdo_user"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Stop application
echo "Stopping application..."
sudo systemctl stop itdo-erp

# Create restoration database
echo "Creating restoration database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME}_restore;"
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME}_restore WITH OWNER $DB_USER;"

# Restore backup
echo "Restoring backup..."
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | psql -U $DB_USER -h localhost ${DB_NAME}_restore
else
    psql -U $DB_USER -h localhost ${DB_NAME}_restore < $BACKUP_FILE
fi

if [ $? -eq 0 ]; then
    echo "Backup restored successfully to ${DB_NAME}_restore"
    echo "To make it active, run: sudo -u postgres psql -c \"ALTER DATABASE $DB_NAME RENAME TO ${DB_NAME}_old; ALTER DATABASE ${DB_NAME}_restore RENAME TO $DB_NAME;\""
    echo "Then restart the application: sudo systemctl start itdo-erp"
else
    echo "Restore failed!"
    exit 1
fi
```

### Application Backup

#### Code and Configuration Backup
```bash
#!/bin/bash
# File: /opt/itdo-erp/scripts/backup-application.sh

BACKUP_DIR="/opt/itdo-erp/backups"
DATE=$(date '+%Y%m%d_%H%M%S')
APP_BACKUP_FILE="${BACKUP_DIR}/app_backup_${DATE}.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup application files
tar -czf $APP_BACKUP_FILE \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='*.log' \
    /opt/itdo-erp/

echo "Application backup completed: $APP_BACKUP_FILE"
```

## 🔧 Maintenance Tasks

### Daily Maintenance

#### Database Maintenance
```bash
#!/bin/bash
# File: /opt/itdo-erp/scripts/daily-maintenance.sh

DB_NAME="itdo_erp_db"

echo "Starting daily database maintenance..."

# Update table statistics
sudo -u postgres psql -d $DB_NAME -c "ANALYZE;"

# Vacuum tables
sudo -u postgres psql -d $DB_NAME -c "VACUUM;"

# Reindex if needed (weekly)
if [ $(date +%u) -eq 7 ]; then
    echo "Performing weekly reindex..."
    sudo -u postgres psql -d $DB_NAME -c "REINDEX DATABASE $DB_NAME;"
fi

echo "Daily maintenance completed"
```

#### Log Cleanup
```bash
#!/bin/bash
# File: /opt/itdo-erp/scripts/cleanup-logs.sh

LOG_DIR="/var/log/itdo-erp"
RETENTION_DAYS=30

echo "Cleaning up old log files..."

# Remove old application logs
find $LOG_DIR -name "*.log" -mtime +$RETENTION_DAYS -delete

# Clean up systemd journal
sudo journalctl --vacuum-time=30d

echo "Log cleanup completed"
```

### Weekly Maintenance

#### System Updates
```bash
#!/bin/bash
# File: /opt/itdo-erp/scripts/weekly-maintenance.sh

echo "Starting weekly maintenance..."

# Update system packages (non-interactive)
sudo apt update
sudo apt upgrade -y

# Update Python dependencies
cd /opt/itdo-erp/backend
uv sync --upgrade

# Update Node.js dependencies
cd /opt/itdo-erp/frontend
npm update

# Check for security updates
sudo apt list --upgradable | grep -i security

# Restart services if needed
if [ -f /var/run/reboot-required ]; then
    echo "System reboot required after updates"
    # Schedule reboot for maintenance window
    # sudo shutdown -r +60 "System reboot for maintenance"
fi

echo "Weekly maintenance completed"
```

### Monthly Maintenance

#### Performance Optimization
```bash
#!/bin/bash
# File: /opt/itdo-erp/scripts/monthly-maintenance.sh

DB_NAME="itdo_erp_db"

echo "Starting monthly maintenance..."

# Database performance analysis
sudo -u postgres psql -d $DB_NAME -c "
SELECT 
    schemaname, 
    tablename, 
    n_tup_ins + n_tup_upd + n_tup_del as total_writes,
    n_tup_ins, n_tup_upd, n_tup_del,
    seq_scan, seq_tup_read,
    idx_scan, idx_tup_fetch
FROM pg_stat_user_tables 
ORDER BY total_writes DESC;
"

# Check for unused indexes
sudo -u postgres psql -d $DB_NAME -c "
SELECT 
    indexrelname as index_name,
    relname as table_name,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE idx_scan = 0;
"

# Full vacuum (during maintenance window)
echo "Performing full vacuum..."
sudo -u postgres psql -d $DB_NAME -c "VACUUM FULL;"

echo "Monthly maintenance completed"
```

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Application Won't Start
**Symptoms:**
- Service fails to start
- Connection refused errors
- 502 Bad Gateway from Nginx

**Diagnosis:**
```bash
# Check service status
sudo systemctl status itdo-erp

# Check logs
sudo journalctl -u itdo-erp -n 50

# Check process
ps aux | grep uvicorn

# Check port usage
sudo netstat -tlnp | grep 8000
```

**Solutions:**
1. **Port conflict:**
   ```bash
   sudo lsof -i :8000
   # Kill conflicting process or change port
   ```

2. **Permission issues:**
   ```bash
   sudo chown -R itdo:itdo /opt/itdo-erp
   sudo chmod +x /opt/itdo-erp/backend/.venv/bin/uvicorn
   ```

3. **Environment issues:**
   ```bash
   # Check environment variables
   sudo systemctl edit itdo-erp
   # Add missing environment variables
   ```

#### Issue 2: Database Connection Errors
**Symptoms:**
- "connection refused" errors
- "could not connect to server" messages
- Slow database responses

**Diagnosis:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Check configuration
sudo -u postgres psql -c "SHOW all;" | grep -E "max_connections|shared_buffers"
```

**Solutions:**
1. **PostgreSQL not running:**
   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

2. **Too many connections:**
   ```bash
   # Edit postgresql.conf
   sudo nano /etc/postgresql/15/main/postgresql.conf
   # Increase max_connections
   max_connections = 200
   sudo systemctl restart postgresql
   ```

3. **Connection pooling:**
   ```bash
   # Install and configure pgbouncer
   sudo apt install pgbouncer
   # Configure connection pooling
   ```

#### Issue 3: High Memory Usage
**Symptoms:**
- System running slowly
- Out of memory errors
- Application crashes

**Diagnosis:**
```bash
# Check memory usage
free -m
htop

# Check application memory
ps aux --sort=-%mem | head

# Check for memory leaks
valgrind --tool=memcheck python app/main.py
```

**Solutions:**
1. **Restart services:**
   ```bash
   sudo systemctl restart itdo-erp
   sudo systemctl restart postgresql
   ```

2. **Optimize database:**
   ```bash
   # Reduce shared_buffers if too high
   sudo nano /etc/postgresql/15/main/postgresql.conf
   shared_buffers = 256MB
   ```

3. **Add swap space:**
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

#### Issue 4: Slow Performance
**Symptoms:**
- Long response times
- Timeouts
- High CPU usage

**Diagnosis:**
```bash
# Check CPU usage
top
htop

# Check I/O wait
iostat -x 1

# Check database performance
sudo -u postgres psql -d itdo_erp_db -c "
SELECT 
    query,
    mean_time,
    calls,
    total_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

**Solutions:**
1. **Database optimization:**
   ```sql
   -- Add missing indexes
   CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
   
   -- Update statistics
   ANALYZE;
   
   -- Vacuum tables
   VACUUM VERBOSE;
   ```

2. **Application optimization:**
   ```bash
   # Increase worker processes
   sudo systemctl edit itdo-erp
   # Add:
   # ExecStart=
   # ExecStart=/opt/itdo-erp/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

3. **Redis caching:**
   ```bash
   # Verify Redis is running and configured
   redis-cli info memory
   redis-cli config get maxmemory-policy
   ```

## 📱 Emergency Procedures

### Critical System Failure

#### Emergency Contact List
- **Primary On-Call**: +1-555-ITDO-911
- **Backup On-Call**: +1-555-ITDO-912
- **System Administrator**: admin@itdo.com
- **Database Administrator**: dba@itdo.com
- **DevOps Team**: devops@itdo.com

#### Emergency Response Steps
1. **Assess the situation**
   - Identify affected services
   - Determine impact scope
   - Document timeline

2. **Immediate response**
   ```bash
   # Take snapshot of current state
   ./scripts/emergency-snapshot.sh
   
   # Attempt service restart
   sudo systemctl restart itdo-erp
   sudo systemctl restart postgresql
   sudo systemctl restart redis
   ```

3. **Communication**
   - Notify stakeholders
   - Update status page
   - Document actions taken

4. **Recovery procedures**
   ```bash
   # If restart fails, restore from backup
   ./scripts/restore-database.sh /opt/itdo-erp/backups/latest_backup.sql.gz
   ```

### Disaster Recovery

#### Data Center Failure
1. **Activate backup site**
2. **Restore from offsite backups**
3. **Update DNS records**
4. **Validate system functionality**
5. **Communicate status to users**

#### Security Incident
1. **Isolate affected systems**
   ```bash
   # Block suspicious IPs
   sudo ufw deny from <suspicious_ip>
   
   # Review access logs
   grep -i "suspicious_ip" /var/log/nginx/access.log
   ```

2. **Change all passwords**
3. **Review audit logs**
4. **Report to security team**

## 📊 Performance Baselines

### Normal Operating Parameters

#### System Resources
- **CPU Usage**: < 70% average
- **Memory Usage**: < 80% of available RAM
- **Disk Usage**: < 80% of available space
- **Network I/O**: < 100 Mbps

#### Application Performance
- **API Response Time**: < 200ms average
- **Database Query Time**: < 100ms average
- **Page Load Time**: < 2 seconds
- **Concurrent Users**: 1000+ supported

#### Database Performance
- **Connection Count**: < 80% of max_connections
- **Cache Hit Ratio**: > 95%
- **Transaction Rate**: < 1000 TPS normal load
- **Lock Wait Time**: < 50ms average

## 📋 Maintenance Schedules

### Daily Tasks (Automated)
- **02:00**: Database backup
- **03:00**: Log rotation
- **04:00**: Health checks summary
- **Every 5 min**: System health monitoring

### Weekly Tasks (Automated)
- **Sunday 04:00**: System cleanup
- **Sunday 05:00**: Security updates check
- **Sunday 06:00**: Performance report generation

### Monthly Tasks (Manual)
- **First Sunday**: Full system backup verification
- **Second Sunday**: Performance optimization review
- **Third Sunday**: Security audit
- **Fourth Sunday**: Disaster recovery test

### Quarterly Tasks (Manual)
- **January/April/July/October**: Complete system review
- **March/June/September/December**: Capacity planning review

## 📞 Support Procedures

### User Support Escalation

#### Level 1: Basic Issues
- Password resets
- Account lockouts
- Basic navigation help
- Simple data entry questions

#### Level 2: Technical Issues
- Application errors
- Performance problems
- Integration issues
- Complex workflow problems

#### Level 3: System Issues
- Database problems
- Infrastructure failures
- Security incidents
- Major performance degradation

### Issue Tracking

#### Severity Levels
- **Critical**: System down, data loss, security breach
- **High**: Major functionality impaired
- **Medium**: Minor functionality issues
- **Low**: Enhancement requests, documentation

#### Response Times
- **Critical**: 15 minutes
- **High**: 1 hour
- **Medium**: 4 hours
- **Low**: 1 business day

---

## 📝 Document Information

- **Version**: 1.0
- **Last Updated**: 2025-01-26
- **Maintained By**: ITDO Operations Team
- **Review Cycle**: Monthly
- **Emergency Contact**: +1-555-ITDO-911

---

*This document is part of the ITDO ERP System v2 technical documentation suite.*