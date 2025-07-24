# ITDO_ERP2 Multi-Environment Agent Setup

This directory contains the multi-environment agent deployment system for ITDO_ERP2.

## Overview

The system creates three isolated environments:
- **Development** (172.23.14.204): Latest development code
- **Staging** (172.23.14.205): Stable testing environment  
- **Production** (172.23.14.206): Production-ready environment

## Quick Start

```bash
# Start all environments
./scripts/multi-env/agent-controller.sh start

# Check status
./scripts/multi-env/agent-controller.sh status

# Monitor environments
./scripts/multi-env/monitor-environments.sh

# Stop all environments
./scripts/multi-env/agent-controller.sh stop
```

## Environment URLs

| Environment | Backend API | Frontend | Database | Keycloak |
|-------------|-------------|----------|----------|----------|
| Development | http://172.23.14.204:8000 | http://172.23.14.204:3000 | 172.23.14.204:5432 | http://172.23.14.204:8080 |
| Staging     | http://172.23.14.205:8000 | http://172.23.14.205:3000 | 172.23.14.205:5432 | http://172.23.14.205:8080 |
| Production  | http://172.23.14.206:8000 | http://172.23.14.206:3000 | 172.23.14.206:5432 | http://172.23.14.206:8080 |

## File Structure

```
scripts/multi-env/
├── setup-multi-env.sh          # Initial setup script
├── agent-controller.sh          # Master controller
├── monitor-environments.sh      # Monitoring script
├── agents/
│   ├── development/
│   │   ├── agent-config.json    # Environment configuration
│   │   ├── start-agent.sh       # Start script
│   │   └── stop-agent.sh        # Stop script
│   ├── staging/
│   └── production/
└── environments/
    ├── development/
    │   ├── docker-compose.yml   # Data layer services
    │   └── .env                 # Environment variables
    ├── staging/
    └── production/
```

## Features

- **Isolated Environments**: Each environment has its own IP address and data
- **Automated Deployment**: One-command setup and deployment
- **Health Monitoring**: Continuous health checks and status reporting
- **Log Management**: Centralized logging for each environment
- **Configuration Management**: Environment-specific configurations

## Commands

### Agent Controller
```bash
./scripts/multi-env/agent-controller.sh start     # Start all environments
./scripts/multi-env/agent-controller.sh stop      # Stop all environments
./scripts/multi-env/agent-controller.sh status    # Show status
./scripts/multi-env/agent-controller.sh health    # Health checks
./scripts/multi-env/agent-controller.sh logs dev  # Show logs
```

### Individual Environment
```bash
./scripts/multi-env/agents/development/start-agent.sh
./scripts/multi-env/agents/development/stop-agent.sh
```

### Monitoring
```bash
./scripts/multi-env/monitor-environments.sh       # Full status report
```

## Troubleshooting

### IP Address Issues
```bash
# Check configured IPs
ip addr show eth0

# Manually add IP (if needed)
sudo ip addr add 172.23.14.204/20 dev eth0
```

### Service Issues
```bash
# Check service status
./scripts/multi-env/agent-controller.sh status

# Check specific service health
curl http://172.23.14.204:8000/health
```

### Resource Usage
```bash
# Check system resources
free -h
df -h
ps aux | grep -E "(uvicorn|npm|node)"
```

## Implementation Details

This setup implements Issue #147 requirements:
- Multiple verification environments on single PC
- Port conflict resolution using IP address separation
- Automated agent deployment and management
- Resource monitoring and optimization
- Environment isolation with separate databases

