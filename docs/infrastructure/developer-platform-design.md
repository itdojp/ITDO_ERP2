# Developer Platform Design for ITDO ERP v2

## 🎯 Overview

This document outlines the comprehensive Developer Platform design for ITDO ERP v2, creating a self-service, cloud-native development environment that empowers engineers with modern tools, automated workflows, and streamlined development experiences while maintaining security and compliance.

## 🏗️ Platform Architecture

### Developer Platform Stack

```
┌─────────────────────────────────────────────────────────────┐
│                   Developer Portal (Web UI)                 │
│              (React + TypeScript + Backstage)               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Platform APIs & Services                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Service   │ │  Resource   │ │  Pipeline   │           │
│  │  Catalog    │ │  Manager    │ │  Orchestrator│           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Development Tools Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  CI/CD      │ │  IDE/Code   │ │  Testing    │           │
│  │  Pipelines  │ │  Spaces     │ │  Framework  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│             Infrastructure Automation                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Kubernetes  │ │  Terraform  │ │  GitOps     │           │
│  │  Operators  │ │  Modules    │ │  ArgoCD     │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### Core Platform Components

#### 1. Developer Portal (Backstage)
```yaml
# developer-platform/backstage/app-config.yaml
app:
  title: ITDO ERP Developer Platform
  baseUrl: https://developer.itdo-erp.com

organization:
  name: ITDO Technologies

backend:
  baseUrl: https://developer.itdo-erp.com
  listen:
    port: 7007
    host: 0.0.0.0
  cors:
    origin: https://developer.itdo-erp.com
  database:
    client: pg
    connection:
      host: ${POSTGRES_HOST}
      port: ${POSTGRES_PORT}
      user: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
      database: backstage_catalog

catalog:
  rules:
    - allow: [Component, System, API, Resource, Location, User, Group, Domain]
  locations:
    # Service catalog locations
    - type: url
      target: https://github.com/company/itdo-erp-services/blob/main/catalog-info.yaml
    - type: url
      target: https://github.com/company/itdo-erp-infrastructure/blob/main/systems.yaml
    - type: url
      target: https://github.com/company/itdo-erp-apis/blob/main/api-catalog.yaml

integrations:
  github:
    - host: github.com
      token: ${GITHUB_TOKEN}
  
  gitlab:
    - host: gitlab.company.com
      token: ${GITLAB_TOKEN}
  
  kubernetes:
    - url: https://kubernetes.default.svc
      authProvider: serviceAccount
      serviceAccountToken: ${K8S_SERVICE_ACCOUNT_TOKEN}

auth:
  environment: production
  providers:
    github:
      production:
        clientId: ${GITHUB_CLIENT_ID}
        clientSecret: ${GITHUB_CLIENT_SECRET}
    
    oauth2:
      production:
        clientId: ${KEYCLOAK_CLIENT_ID}
        clientSecret: ${KEYCLOAK_CLIENT_SECRET}
        authorizationUrl: https://auth.itdo-erp.com/auth/realms/itdo-erp/protocol/openid_connect/auth
        tokenUrl: https://auth.itdo-erp.com/auth/realms/itdo-erp/protocol/openid_connect/token

techdocs:
  builder: 'local'
  generator:
    runIn: 'local'
  publisher:
    type: 'awsS3'
    awsS3:
      bucketName: 'itdo-erp-techdocs'
      region: 'us-west-2'

kubernetes:
  serviceLocatorMethod:
    type: 'multiTenant'
  clusterLocatorMethods:
    - type: 'config'
      clusters:
        - url: https://k8s-prod.company.com
          name: production
          authProvider: serviceAccount
          serviceAccountToken: ${K8S_PROD_TOKEN}
        - url: https://k8s-staging.company.com
          name: staging
          authProvider: serviceAccount
          serviceAccountToken: ${K8S_STAGING_TOKEN}

scaffolder:
  defaultAuthor:
    name: ITDO Platform Team
    email: platform@company.com
  defaultCommitMessage: 'Initial commit from ITDO Developer Platform'

lighthouse:
  baseUrl: https://lighthouse.itdo-erp.com
```

#### 2. Service Templates
```yaml
# developer-platform/templates/fastapi-service/template.yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: fastapi-service
  title: FastAPI Service Template
  description: Create a new FastAPI microservice with best practices
  tags:
    - recommended
    - python
    - fastapi
    - microservice
spec:
  owner: platform-team
  type: service
  parameters:
    - title: Service Information
      required:
        - name
        - description
        - owner
      properties:
        name:
          title: Name
          type: string
          description: Unique name for the service
          pattern: '^[a-z0-9-]+$'
        description:
          title: Description
          type: string
          description: Brief description of the service
        owner:
          title: Owner
          type: string
          description: Team or individual owning this service
          ui:field: OwnerPicker
          ui:options:
            catalogFilter:
              kind: [Group, User]
    
    - title: Technical Configuration
      required:
        - python_version
        - database_required
      properties:
        python_version:
          title: Python Version
          type: string
          description: Python version to use
          default: "3.13"
          enum:
            - "3.11"
            - "3.12"
            - "3.13"
        database_required:
          title: Database Required
          type: boolean
          description: Does this service need a database?
          default: true
        cache_required:
          title: Redis Cache Required
          type: boolean
          description: Does this service need Redis cache?
          default: false
    
    - title: Repository Information
      required:
        - repo_name
      properties:
        repo_name:
          title: Repository Name
          type: string
          description: Name of the GitHub repository
          pattern: '^[a-z0-9-]+$'
        
  steps:
    - id: fetch
      name: Fetch Base Template
      action: fetch:template
      input:
        url: ./content
        values:
          name: ${{ parameters.name }}
          description: ${{ parameters.description }}
          owner: ${{ parameters.owner }}
          python_version: ${{ parameters.python_version }}
          database_required: ${{ parameters.database_required }}
          cache_required: ${{ parameters.cache_required }}
          repo_name: ${{ parameters.repo_name }}
          destination: ${{ parameters.repo_name }}

    - id: publish
      name: Publish to GitHub
      action: publish:github
      input:
        allowedHosts: ['github.com']
        description: ${{ parameters.description }}
        repoUrl: github.com?owner=company&repo=${{ parameters.repo_name }}
        defaultBranch: main
        gitCommitMessage: 'Initial commit from ITDO Developer Platform'

    - id: register
      name: Register in Catalog
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps.publish.output.repoContentsUrl }}
        catalogInfoPath: '/catalog-info.yaml'

    - id: create-pr-pipeline
      name: Create CI/CD Pipeline
      action: github:actions:create
      input:
        repoUrl: github.com?owner=company&repo=${{ parameters.repo_name }}
        workflowPath: .github/workflows/ci.yml
        workflowContent: |
          name: CI/CD Pipeline
          on:
            push:
              branches: [main, develop]
            pull_request:
              branches: [main]
          
          jobs:
            test:
              runs-on: ubuntu-latest
              steps:
                - uses: actions/checkout@v4
                - uses: actions/setup-python@v4
                  with:
                    python-version: ${{ parameters.python_version }}
                - name: Install dependencies
                  run: |
                    pip install uv
                    uv sync
                - name: Run tests
                  run: uv run pytest
                - name: Run linting
                  run: uv run ruff check .
                - name: Run type checking
                  run: uv run mypy .

  output:
    links:
      - title: Repository
        url: ${{ steps.publish.output.remoteUrl }}
      - title: Open in catalog
        icon: catalog
        entityRef: ${{ steps.register.output.entityRef }}
```

#### 3. Development Environment Manager
```python
# developer-platform/environment-manager/manager.py
import asyncio
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from kubernetes import client, config
from dataclasses import dataclass
import logging

@dataclass
class DevelopmentEnvironment:
    name: str
    namespace: str
    owner: str
    team: str
    services: List[str]
    ttl_hours: int
    status: str
    created_at: datetime
    last_accessed: datetime
    resource_limits: Dict[str, str]

class DevelopmentEnvironmentManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        config.load_incluster_config()
        self.k8s_client = client.CoreV1Api()
        self.apps_client = client.AppsV1Api()
        self.networking_client = client.NetworkingV1Api()
        
    async def create_environment(self, env_request: Dict) -> DevelopmentEnvironment:
        """Create a new development environment"""
        try:
            env_name = f"dev-{env_request['name']}-{env_request['owner']}"
            namespace = f"dev-{env_name}"
            
            # Create namespace
            await self.create_namespace(namespace, env_request)
            
            # Deploy services
            services = await self.deploy_services(namespace, env_request['services'])
            
            # Setup networking
            await self.setup_networking(namespace, env_name)
            
            # Configure monitoring
            await self.setup_monitoring(namespace)
            
            # Create environment record
            environment = DevelopmentEnvironment(
                name=env_name,
                namespace=namespace,
                owner=env_request['owner'],
                team=env_request['team'],
                services=services,
                ttl_hours=env_request.get('ttl_hours', 48),
                status='active',
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                resource_limits=env_request.get('resource_limits', {
                    'cpu': '4',
                    'memory': '8Gi',
                    'storage': '50Gi'
                })
            )
            
            await self.save_environment_metadata(environment)
            
            self.logger.info(f"Development environment created: {env_name}")
            return environment
            
        except Exception as e:
            self.logger.error(f"Failed to create environment: {e}")
            raise
    
    async def create_namespace(self, namespace: str, env_request: Dict):
        """Create Kubernetes namespace with proper configuration"""
        namespace_manifest = client.V1Namespace(
            metadata=client.V1ObjectMeta(
                name=namespace,
                labels={
                    'platform.itdo-erp.com/type': 'development',
                    'platform.itdo-erp.com/owner': env_request['owner'],
                    'platform.itdo-erp.com/team': env_request['team'],
                    'platform.itdo-erp.com/created-at': datetime.utcnow().isoformat(),
                    'platform.itdo-erp.com/ttl-hours': str(env_request.get('ttl_hours', 48))
                },
                annotations={
                    'platform.itdo-erp.com/description': env_request.get('description', ''),
                    'platform.itdo-erp.com/contact': env_request.get('contact', env_request['owner'])
                }
            )
        )
        
        self.k8s_client.create_namespace(namespace_manifest)
        
        # Create resource quota
        resource_quota = client.V1ResourceQuota(
            metadata=client.V1ObjectMeta(name='dev-quota'),
            spec=client.V1ResourceQuotaSpec(
                hard={
                    'requests.cpu': env_request.get('resource_limits', {}).get('cpu', '4'),
                    'requests.memory': env_request.get('resource_limits', {}).get('memory', '8Gi'),
                    'persistentvolumeclaims': '10',
                    'services': '20',
                    'pods': '50'
                }
            )
        )
        
        self.k8s_client.create_namespaced_resource_quota(
            namespace=namespace,
            body=resource_quota
        )
        
        # Create network policy for isolation
        network_policy = client.V1NetworkPolicy(
            metadata=client.V1ObjectMeta(name='dev-isolation'),
            spec=client.V1NetworkPolicySpec(
                pod_selector=client.V1LabelSelector(),
                policy_types=['Ingress', 'Egress'],
                ingress=[
                    client.V1NetworkPolicyIngressRule(
                        from_=[
                            client.V1NetworkPolicyPeer(
                                namespace_selector=client.V1LabelSelector(
                                    match_labels={'platform.itdo-erp.com/type': 'development'}
                                )
                            )
                        ]
                    )
                ],
                egress=[
                    client.V1NetworkPolicyEgressRule(
                        to=[],
                        ports=[
                            client.V1NetworkPolicyPort(protocol='TCP', port=80),
                            client.V1NetworkPolicyPort(protocol='TCP', port=443),
                            client.V1NetworkPolicyPort(protocol='TCP', port=53),
                            client.V1NetworkPolicyPort(protocol='UDP', port=53)
                        ]
                    )
                ]
            )
        )
        
        self.networking_client.create_namespaced_network_policy(
            namespace=namespace,
            body=network_policy
        )
    
    async def deploy_services(self, namespace: str, services: List[Dict]) -> List[str]:
        """Deploy requested services to the development environment"""
        deployed_services = []
        
        for service in services:
            service_name = service['name']
            service_type = service['type']
            
            if service_type == 'database':
                await self.deploy_database(namespace, service)
            elif service_type == 'cache':
                await self.deploy_cache(namespace, service)
            elif service_type == 'api':
                await self.deploy_api_service(namespace, service)
            elif service_type == 'frontend':
                await self.deploy_frontend_service(namespace, service)
            
            deployed_services.append(service_name)
        
        return deployed_services
    
    async def deploy_database(self, namespace: str, service: Dict):
        """Deploy PostgreSQL database for development"""
        db_deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': f"{service['name']}-db",
                'namespace': namespace,
                'labels': {
                    'app': f"{service['name']}-db",
                    'component': 'database'
                }
            },
            'spec': {
                'replicas': 1,
                'selector': {
                    'matchLabels': {'app': f"{service['name']}-db"}
                },
                'template': {
                    'metadata': {
                        'labels': {'app': f"{service['name']}-db"}
                    },
                    'spec': {
                        'containers': [{
                            'name': 'postgres',
                            'image': 'postgres:15-alpine',
                            'env': [
                                {'name': 'POSTGRES_DB', 'value': service.get('database_name', 'app_db')},
                                {'name': 'POSTGRES_USER', 'value': 'app_user'},
                                {'name': 'POSTGRES_PASSWORD', 'value': 'dev_password_123'}
                            ],
                            'ports': [{'containerPort': 5432}],
                            'resources': {
                                'requests': {'cpu': '250m', 'memory': '512Mi'},
                                'limits': {'cpu': '1', 'memory': '2Gi'}
                            },
                            'volumeMounts': [{
                                'name': 'postgres-data',
                                'mountPath': '/var/lib/postgresql/data'
                            }]
                        }],
                        'volumes': [{
                            'name': 'postgres-data',
                            'emptyDir': {}
                        }]
                    }
                }
            }
        }
        
        # Apply deployment
        self.apps_client.create_namespaced_deployment(
            namespace=namespace,
            body=db_deployment
        )
        
        # Create service
        db_service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=f"{service['name']}-db",
                namespace=namespace
            ),
            spec=client.V1ServiceSpec(
                selector={'app': f"{service['name']}-db"},
                ports=[client.V1ServicePort(port=5432, target_port=5432)]
            )
        )
        
        self.k8s_client.create_namespaced_service(
            namespace=namespace,
            body=db_service
        )
    
    async def setup_networking(self, namespace: str, env_name: str):
        """Setup ingress and networking for the development environment"""
        ingress = client.V1Ingress(
            metadata=client.V1ObjectMeta(
                name=f"{env_name}-ingress",
                namespace=namespace,
                annotations={
                    'nginx.ingress.kubernetes.io/rewrite-target': '/',
                    'nginx.ingress.kubernetes.io/ssl-redirect': 'false',
                    'nginx.ingress.kubernetes.io/force-ssl-redirect': 'false'
                }
            ),
            spec=client.V1IngressSpec(
                rules=[
                    client.V1IngressRule(
                        host=f"{env_name}.dev.itdo-erp.com",
                        http=client.V1HTTPIngressRuleValue(
                            paths=[
                                client.V1HTTPIngressPath(
                                    path='/',
                                    path_type='Prefix',
                                    backend=client.V1IngressBackend(
                                        service=client.V1IngressServiceBackend(
                                            name='frontend',
                                            port=client.V1ServiceBackendPort(number=3000)
                                        )
                                    )
                                ),
                                client.V1HTTPIngressPath(
                                    path='/api',
                                    path_type='Prefix',
                                    backend=client.V1IngressBackend(
                                        service=client.V1IngressServiceBackend(
                                            name='backend-api',
                                            port=client.V1ServiceBackendPort(number=8000)
                                        )
                                    )
                                )
                            ]
                        )
                    )
                ]
            )
        )
        
        self.networking_client.create_namespaced_ingress(
            namespace=namespace,
            body=ingress
        )
    
    async def cleanup_expired_environments(self):
        """Clean up expired development environments"""
        try:
            namespaces = self.k8s_client.list_namespace(
                label_selector='platform.itdo-erp.com/type=development'
            )
            
            for namespace in namespaces.items:
                ttl_hours = int(namespace.metadata.labels.get('platform.itdo-erp.com/ttl-hours', '48'))
                created_at_str = namespace.metadata.labels.get('platform.itdo-erp.com/created-at')
                
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    expiry_time = created_at + timedelta(hours=ttl_hours)
                    
                    if datetime.utcnow().replace(tzinfo=created_at.tzinfo) > expiry_time:
                        self.logger.info(f"Cleaning up expired environment: {namespace.metadata.name}")
                        await self.delete_environment(namespace.metadata.name)
        
        except Exception as e:
            self.logger.error(f"Error cleaning up environments: {e}")
    
    async def delete_environment(self, namespace: str):
        """Delete a development environment"""
        try:
            # Delete namespace (this will delete all resources within it)
            self.k8s_client.delete_namespace(name=namespace)
            self.logger.info(f"Deleted environment namespace: {namespace}")
            
        except Exception as e:
            self.logger.error(f"Error deleting environment {namespace}: {e}")
    
    async def save_environment_metadata(self, environment: DevelopmentEnvironment):
        """Save environment metadata to ConfigMap"""
        metadata = {
            'name': environment.name,
            'namespace': environment.namespace,
            'owner': environment.owner,
            'team': environment.team,
            'services': environment.services,
            'ttl_hours': environment.ttl_hours,
            'status': environment.status,
            'created_at': environment.created_at.isoformat(),
            'last_accessed': environment.last_accessed.isoformat(),
            'resource_limits': environment.resource_limits
        }
        
        config_map = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(
                name='environment-metadata',
                namespace=environment.namespace
            ),
            data={'metadata.json': yaml.dump(metadata)}
        )
        
        self.k8s_client.create_namespaced_config_map(
            namespace=environment.namespace,
            body=config_map
        )

# Environment cleanup scheduler
async def main():
    manager = DevelopmentEnvironmentManager()
    
    while True:
        try:
            await manager.cleanup_expired_environments()
            # Run cleanup every hour
            await asyncio.sleep(3600)
        except Exception as e:
            logging.error(f"Cleanup scheduler error: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error

if __name__ == "__main__":
    asyncio.run(main())
```

## 🚀 CI/CD Pipeline Templates

### Universal Pipeline Template
```yaml
# developer-platform/pipelines/universal-pipeline.yaml
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: universal-service-pipeline
  namespace: tekton-pipelines
spec:
  description: Universal CI/CD pipeline for ITDO ERP services
  params:
  - name: repo-url
    type: string
    description: Git repository URL
  - name: revision
    type: string
    description: Git revision to build
    default: main
  - name: service-name
    type: string
    description: Name of the service
  - name: dockerfile-path
    type: string
    description: Path to Dockerfile
    default: ./Dockerfile
  - name: image-registry
    type: string
    description: Container image registry
    default: ghcr.io/company
  - name: deploy-environment
    type: string
    description: Deployment environment
    default: staging
  
  workspaces:
  - name: shared-data
  - name: docker-credentials
  - name: git-credentials
  
  tasks:
  # 1. Git Clone
  - name: fetch-source
    taskRef:
      name: git-clone
    workspaces:
    - name: output
      workspace: shared-data
    - name: ssh-directory
      workspace: git-credentials
    params:
    - name: url
      value: $(params.repo-url)
    - name: revision
      value: $(params.revision)
  
  # 2. Code Quality Checks
  - name: code-quality
    runAfter: ["fetch-source"]
    taskRef:
      name: code-quality-check
    workspaces:
    - name: source
      workspace: shared-data
    params:
    - name: service-name
      value: $(params.service-name)
  
  # 3. Unit Tests
  - name: unit-tests
    runAfter: ["code-quality"]
    taskRef:
      name: unit-test
    workspaces:
    - name: source
      workspace: shared-data
    params:
    - name: service-name
      value: $(params.service-name)
  
  # 4. Security Scan
  - name: security-scan
    runAfter: ["unit-tests"]
    taskRef:
      name: security-scan
    workspaces:
    - name: source
      workspace: shared-data
    params:
    - name: service-name
      value: $(params.service-name)
  
  # 5. Build Container Image
  - name: build-image
    runAfter: ["security-scan"]
    taskRef:
      name: buildah
    workspaces:
    - name: source
      workspace: shared-data
    - name: dockerconfig
      workspace: docker-credentials
    params:
    - name: IMAGE
      value: $(params.image-registry)/$(params.service-name):$(params.revision)
    - name: DOCKERFILE
      value: $(params.dockerfile-path)
  
  # 6. Image Security Scan
  - name: image-scan
    runAfter: ["build-image"]
    taskRef:
      name: trivy-scan
    params:
    - name: IMAGE
      value: $(params.image-registry)/$(params.service-name):$(params.revision)
  
  # 7. Deploy to Environment
  - name: deploy
    runAfter: ["image-scan"]
    taskRef:
      name: argocd-sync
    params:
    - name: application-name
      value: $(params.service-name)-$(params.deploy-environment)
    - name: image-tag
      value: $(params.revision)
  
  # 8. Integration Tests
  - name: integration-tests
    runAfter: ["deploy"]
    taskRef:
      name: integration-test
    params:
    - name: service-name
      value: $(params.service-name)
    - name: environment
      value: $(params.deploy-environment)
  
  # 9. Performance Tests
  - name: performance-tests
    runAfter: ["integration-tests"]
    taskRef:
      name: k6-performance-test
    when:
    - input: "$(params.deploy-environment)"
      operator: in
      values: ["staging", "production"]
    params:
    - name: service-name
      value: $(params.service-name)
    - name: environment
      value: $(params.deploy-environment)
  
  # 10. Promote to Production (if staging successful)
  - name: promote-to-production
    runAfter: ["performance-tests"]
    taskRef:
      name: production-promotion
    when:
    - input: "$(params.deploy-environment)"
      operator: in
      values: ["staging"]
    params:
    - name: service-name
      value: $(params.service-name)
    - name: image-tag
      value: $(params.revision)
```

### Task Definitions
```yaml
# developer-platform/pipelines/tasks/code-quality-check.yaml
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: code-quality-check
  namespace: tekton-pipelines
spec:
  description: Perform code quality checks
  params:
  - name: service-name
    type: string
  workspaces:
  - name: source
  steps:
  - name: detect-language
    image: alpine/git:latest
    workingDir: $(workspaces.source.path)
    script: |
      #!/bin/sh
      if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
        echo "python" > /tmp/language
      elif [ -f "package.json" ]; then
        echo "nodejs" > /tmp/language
      elif [ -f "go.mod" ]; then
        echo "golang" > /tmp/language
      elif [ -f "Cargo.toml" ]; then
        echo "rust" > /tmp/language
      else
        echo "unknown" > /tmp/language
      fi
  
  - name: python-quality
    image: python:3.13-slim
    workingDir: $(workspaces.source.path)
    when:
    - input: "$(cat /tmp/language)"
      operator: in
      values: ["python"]
    script: |
      #!/bin/bash
      set -e
      echo "Running Python code quality checks..."
      
      # Install uv if not present
      pip install uv
      
      # Install dependencies
      uv sync
      
      # Run linting
      echo "Running ruff linting..."
      uv run ruff check . --output-format=github
      
      # Run formatting check
      echo "Running ruff formatting check..."
      uv run ruff format --check .
      
      # Run type checking
      echo "Running mypy type checking..."
      uv run mypy --strict .
      
      echo "✅ Python code quality checks passed"
  
  - name: nodejs-quality
    image: node:20-alpine
    workingDir: $(workspaces.source.path)
    when:
    - input: "$(cat /tmp/language)"
      operator: in
      values: ["nodejs"]
    script: |
      #!/bin/sh
      set -e
      echo "Running Node.js code quality checks..."
      
      # Install dependencies
      npm ci
      
      # Run linting
      echo "Running ESLint..."
      npm run lint
      
      # Run type checking
      echo "Running TypeScript type checking..."
      npm run typecheck
      
      # Run formatting check
      echo "Running Prettier check..."
      npm run format:check
      
      echo "✅ Node.js code quality checks passed"
---
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: unit-test
  namespace: tekton-pipelines
spec:
  description: Run unit tests
  params:
  - name: service-name
    type: string
  workspaces:
  - name: source
  steps:
  - name: python-tests
    image: python:3.13-slim
    workingDir: $(workspaces.source.path)
    script: |
      #!/bin/bash
      set -e
      
      if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
        echo "Running Python unit tests..."
        pip install uv
        uv sync
        uv run pytest --cov=. --cov-report=xml --cov-report=term-missing -v
        echo "✅ Python unit tests passed"
      fi
  
  - name: nodejs-tests
    image: node:20-alpine
    workingDir: $(workspaces.source.path)
    script: |
      #!/bin/sh
      set -e
      
      if [ -f "package.json" ]; then
        echo "Running Node.js unit tests..."
        npm ci
        npm test
        echo "✅ Node.js unit tests passed"
      fi
---
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: security-scan
  namespace: tekton-pipelines
spec:
  description: Perform security scanning
  params:
  - name: service-name
    type: string
  workspaces:
  - name: source
  steps:
  - name: dependency-scan
    image: owasp/dependency-check:latest
    workingDir: $(workspaces.source.path)
    script: |
      #!/bin/bash
      set -e
      echo "Running dependency vulnerability scan..."
      
      # Create reports directory
      mkdir -p reports
      
      # Run dependency check
      /usr/share/dependency-check/bin/dependency-check.sh \
        --project "$(params.service-name)" \
        --scan . \
        --format HTML \
        --format JSON \
        --out reports/
      
      # Check for high/critical vulnerabilities
      if [ -f "reports/dependency-check-report.json" ]; then
        high_vulns=$(jq '.dependencies[].vulnerabilities[]? | select(.severity == "HIGH" or .severity == "CRITICAL") | .severity' reports/dependency-check-report.json | wc -l)
        
        if [ "$high_vulns" -gt 0 ]; then
          echo "❌ Found $high_vulns high/critical vulnerabilities"
          exit 1
        else
          echo "✅ No high/critical vulnerabilities found"
        fi
      fi
  
  - name: secret-scan
    image: zricethezav/gitleaks:latest
    workingDir: $(workspaces.source.path)
    script: |
      #!/bin/sh
      set -e
      echo "Scanning for secrets..."
      
      gitleaks detect --source . --verbose
      
      echo "✅ No secrets detected"
```

## 📊 Developer Metrics and Analytics

### Developer Experience Metrics
```python
# developer-platform/metrics/dx_metrics.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

@dataclass
class DeveloperMetrics:
    developer_id: str
    team: str
    period_start: datetime
    period_end: datetime
    
    # Velocity Metrics
    commits_count: int
    pull_requests_created: int
    pull_requests_merged: int
    lines_of_code_added: int
    lines_of_code_deleted: int
    
    # Quality Metrics
    code_review_participation: float
    test_coverage_average: float
    bug_fix_time_hours: float
    code_review_time_hours: float
    
    # Platform Usage
    environments_created: int
    pipeline_runs: int
    pipeline_success_rate: float
    documentation_contributions: int
    
    # Developer Experience
    build_time_average_minutes: float
    deployment_frequency: float
    lead_time_hours: float
    mttr_hours: float

class DeveloperExperienceAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def calculate_team_metrics(self, team: str, period_days: int = 30) -> Dict:
        """Calculate comprehensive metrics for a development team"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Get all developers in team
        developers = await self.get_team_developers(team)
        
        team_metrics = {
            'team': team,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': period_days
            },
            'developers': len(developers),
            'aggregate_metrics': await self.calculate_aggregate_metrics(team, start_date, end_date),
            'individual_metrics': {},
            'trends': await self.calculate_trends(team, start_date, end_date),
            'benchmarks': await self.get_industry_benchmarks()
        }
        
        # Calculate metrics for each developer
        for developer in developers:
            dev_metrics = await self.calculate_developer_metrics(developer, start_date, end_date)
            team_metrics['individual_metrics'][developer] = dev_metrics
        
        return team_metrics
    
    async def calculate_aggregate_metrics(self, team: str, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate aggregate metrics for the team"""
        # Mock implementation - in reality would query git, CI/CD systems, etc.
        return {
            'velocity': {
                'total_commits': 245,
                'total_prs': 87,
                'total_prs_merged': 82,
                'average_pr_size_lines': 156,
                'commits_per_developer_per_day': 2.1
            },
            'quality': {
                'average_test_coverage': 84.5,
                'code_review_participation': 92.3,
                'average_review_time_hours': 8.2,
                'bug_escape_rate': 0.03
            },
            'performance': {
                'average_build_time_minutes': 12.5,
                'deployment_frequency_per_day': 3.2,
                'lead_time_hours': 18.4,
                'mttr_hours': 2.1,
                'change_failure_rate': 0.08
            },
            'platform_adoption': {
                'developers_using_platform': 8,
                'total_developers': 10,
                'adoption_rate': 80.0,
                'environments_created': 23,
                'pipeline_usage_rate': 95.6
            }
        }
    
    async def calculate_developer_metrics(self, developer: str, start_date: datetime, end_date: datetime) -> DeveloperMetrics:
        """Calculate metrics for individual developer"""
        # Mock implementation
        return DeveloperMetrics(
            developer_id=developer,
            team="platform-team",
            period_start=start_date,
            period_end=end_date,
            commits_count=45,
            pull_requests_created=12,
            pull_requests_merged=11,
            lines_of_code_added=1840,
            lines_of_code_deleted=920,
            code_review_participation=0.89,
            test_coverage_average=87.2,
            bug_fix_time_hours=4.5,
            code_review_time_hours=6.8,
            environments_created=3,
            pipeline_runs=24,
            pipeline_success_rate=0.92,
            documentation_contributions=5,
            build_time_average_minutes=11.8,
            deployment_frequency=2.8,
            lead_time_hours=16.2,
            mttr_hours=1.8
        )
    
    async def calculate_trends(self, team: str, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate trend analysis"""
        return {
            'velocity_trend': 'increasing',  # +15% compared to previous period
            'quality_trend': 'stable',       # -2% compared to previous period
            'performance_trend': 'improving', # +23% improvement in metrics
            'satisfaction_trend': 'increasing', # Based on developer surveys
            'key_improvements': [
                "Build time reduced by 30% due to pipeline optimization",
                "Code review time improved by 25% with automated tools",
                "Test coverage increased by 12% this period"
            ],
            'areas_for_improvement': [
                "Increase platform adoption by remaining 20% of developers",
                "Reduce lead time by improving environment provisioning",
                "Standardize deployment practices across all services"
            ]
        }
    
    async def get_industry_benchmarks(self) -> Dict:
        """Get industry benchmark data for comparison"""
        return {
            'elite_performers': {
                'deployment_frequency': 'On-demand (multiple per day)',
                'lead_time': '< 1 hour',
                'mttr': '< 1 hour',
                'change_failure_rate': '0-15%'
            },
            'high_performers': {
                'deployment_frequency': 'Between once per day and once per week',
                'lead_time': '< 1 day',
                'mttr': '< 1 day',
                'change_failure_rate': '0-15%'
            },
            'medium_performers': {
                'deployment_frequency': 'Between once per week and once per month',
                'lead_time': '< 1 week',
                'mttr': '< 1 day',
                'change_failure_rate': '0-15%'
            },
            'current_performance_tier': 'high_performer'
        }
    
    async def get_team_developers(self, team: str) -> List[str]:
        """Get list of developers in team"""
        # Mock implementation - would integrate with identity provider
        team_members = {
            'platform-team': ['alice', 'bob', 'charlie', 'diana'],
            'backend-team': ['eve', 'frank', 'grace', 'henry'],
            'frontend-team': ['iris', 'jack', 'karen', 'liam']
        }
        return team_members.get(team, [])
    
    async def generate_weekly_report(self, team: str) -> str:
        """Generate weekly developer experience report"""
        metrics = await self.calculate_team_metrics(team, 7)
        
        report = f"""
# Weekly Developer Experience Report - {team}

## 📊 Key Metrics
- **Deployment Frequency**: {metrics['aggregate_metrics']['performance']['deployment_frequency_per_day']:.1f} per day
- **Lead Time**: {metrics['aggregate_metrics']['performance']['lead_time_hours']:.1f} hours
- **MTTR**: {metrics['aggregate_metrics']['performance']['mttr_hours']:.1f} hours
- **Test Coverage**: {metrics['aggregate_metrics']['quality']['average_test_coverage']:.1f}%

## 🚀 Achievements
- {len(metrics['individual_metrics'])} active developers
- {metrics['aggregate_metrics']['velocity']['total_prs_merged']} PRs merged
- {metrics['aggregate_metrics']['platform_adoption']['environments_created']} development environments created

## 📈 Trends
- Velocity: {metrics['trends']['velocity_trend']}
- Quality: {metrics['trends']['quality_trend']}
- Performance: {metrics['trends']['performance_trend']}

## 🎯 Recommendations
"""
        
        for improvement in metrics['trends']['areas_for_improvement']:
            report += f"- {improvement}\n"
        
        return report

# Usage example
async def main():
    analyzer = DeveloperExperienceAnalyzer()
    
    # Generate team report
    report = await analyzer.generate_weekly_report('platform-team')
    print(report)
    
    # Calculate detailed metrics
    metrics = await analyzer.calculate_team_metrics('platform-team')
    print(f"Team performance tier: {metrics['benchmarks']['current_performance_tier']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🎯 Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
1. **Backstage Platform Setup**
   - Deploy Backstage instance
   - Configure authentication with Keycloak
   - Setup basic service catalog
   - Create initial service templates

2. **Development Environment Manager**
   - Deploy environment provisioning system
   - Configure namespace isolation
   - Implement automated cleanup
   - Setup resource quotas

### Phase 2: CI/CD Integration (Week 3-4)
1. **Pipeline Templates**
   - Create universal pipeline templates
   - Implement language-specific tasks
   - Configure security scanning
   - Setup automated testing

2. **GitOps Integration**
   - Connect with ArgoCD
   - Implement automated deployments
   - Configure promotion workflows
   - Setup rollback mechanisms

### Phase 3: Developer Experience (Week 5-6)
1. **Self-Service Capabilities**
   - Implement service scaffolding
   - Configure environment provisioning
   - Setup monitoring integration
   - Create documentation templates

2. **Metrics and Analytics**
   - Deploy metrics collection
   - Implement dashboard
   - Configure automated reporting
   - Setup trend analysis

### Phase 4: Advanced Features (Week 7-8)
1. **AI-Powered Assistance**
   - Implement code suggestions
   - Configure automated code review
   - Setup intelligent alerting
   - Deploy optimization recommendations

2. **Integration and Polish**
   - Complete platform integration
   - Optimize performance
   - Enhance user experience
   - Conduct training sessions

## ✅ Success Metrics

### Developer Productivity
- **Deployment Frequency**: Achieve "High Performer" tier (daily deployments)
- **Lead Time**: Reduce to <24 hours (currently ~3 days)
- **Environment Provisioning**: <5 minutes (currently ~2 hours)
- **Build Time**: <15 minutes for all services

### Platform Adoption
- **Developer Onboarding**: <2 hours for new developers
- **Platform Usage**: 90% of developers using platform within 3 months
- **Self-Service**: 80% of development tasks self-serviced
- **Developer Satisfaction**: >4.5/5.0 in quarterly surveys

### Quality and Reliability
- **Code Coverage**: >80% across all services
- **Security Scan**: 100% of code passes security scans
- **Change Failure Rate**: <15% (industry high performer standard)
- **MTTR**: <2 hours for platform issues

---

**Document Status**: Design Phase Complete  
**Next Phase**: Phase 2 Implementation  
**Implementation Risk**: LOW (Design Only)  
**Production Impact**: NONE (Design Phase)**