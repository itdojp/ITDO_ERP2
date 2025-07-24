#!/bin/bash
echo "=== CC03 DevOps Progress ==="
echo "Containers running: $(podman ps -q 2>/dev/null | wc -l)"
echo "Workflows created: $(ls .github/workflows/*.yml 2>/dev/null | wc -l)"
echo "Scripts created: $(ls scripts/*.sh 2>/dev/null | wc -l)"
echo "Log entries: $(wc -l < CC03_devops_log_v27.txt)"
echo "Docker compose files: $(ls docker-compose*.yml 2>/dev/null | wc -l)"
echo "Monitoring configs: $(find monitoring -name "*.yml" 2>/dev/null | wc -l)"