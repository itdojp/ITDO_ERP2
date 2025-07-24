# GitOps Workflow Design for ITDO ERP v2

## 🎯 Overview

This document defines the GitOps workflow architecture using ArgoCD for continuous deployment, configuration management, and infrastructure as code for the ITDO ERP system.

## 📐 GitOps Principles

### Core Principles
1. **Declarative Infrastructure**: Everything defined as code
2. **Version Control**: Git as single source of truth
3. **Automated Deployment**: Pull-based deployment model
4. **Observability**: Complete audit trail and monitoring
5. **Security**: Policy-driven with approval workflows

### Operational Benefits
- **Reduced MTTR**: Faster incident recovery
- **Compliance**: Complete audit trail
- **Consistency**: Identical environments
- **Rollback**: Easy version rollback
- **Collaboration**: Code review for infrastructure

## 🏗️ Repository Structure

### Multi-Repository Strategy

```
GitOps Repository Structure:
├── itdo-erp-infrastructure/          # Infrastructure configurations
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   ├── base/                         # Common configurations
│   ├── overlays/                     # Environment-specific overlays
│   └── policies/                     # Security and compliance policies
│
├── itdo-erp-applications/            # Application configurations
│   ├── backend/
│   ├── frontend/
│   ├── monitoring/
│   └── security/
│
└── itdo-erp-helm-charts/            # Custom Helm charts
    ├── backend-api/
    ├── frontend-app/
    ├── database/
    └── monitoring/
```

### Repository Configuration

#### Infrastructure Repository
```yaml
# .argocd/app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: itdo-erp-infrastructure
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: platform
  source:
    repoURL: https://github.com/company/itdo-erp-infrastructure
    targetRevision: HEAD
    path: environments/production
  destination:
    server: https://kubernetes.default.svc
    namespace: itdo-erp-infrastructure
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

#### Application Repository
```yaml
# applications/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: itdo-erp-prod

resources:
  - ../../base/backend
  - ../../base/frontend
  - ../../base/database
  - ../../base/monitoring

patchesStrategicMerge:
  - backend-prod-patch.yaml
  - frontend-prod-patch.yaml
  - database-prod-patch.yaml

images:
  - name: itdo-erp/backend
    newTag: v2.1.5
  - name: itdo-erp/frontend
    newTag: v2.1.3

configMapGenerator:
  - name: app-config
    files:
      - config/production.env
    options:
      disableNameSuffixHash: true

secretGenerator:
  - name: app-secrets
    env: secrets/production.env
    type: Opaque
```

## 🔄 ArgoCD Configuration

### ArgoCD Installation
```yaml
# argocd/install.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
---
apiVersion: argoproj.io/v1alpha1
kind: ArgoCD
metadata:
  name: argocd
  namespace: argocd
spec:
  server:
    replicas: 3
    ingress:
      enabled: true
      hostname: argocd.itdo-erp.com
      tls: true
      annotations:
        cert-manager.io/cluster-issuer: letsencrypt-prod
        nginx.ingress.kubernetes.io/ssl-redirect: "true"
  controller:
    replicas: 3
    env:
      - name: ARGOCD_CONTROLLER_REPLICAS
        value: "3"
  repoServer:
    replicas: 3
  redis:
    enabled: true
  applicationSet:
    enabled: true
  notifications:
    enabled: true
  dex:
    openShiftOAuth: false
  rbac:
    defaultPolicy: 'role:readonly'
    policy: |
      p, role:admin, applications, *, */*, allow
      p, role:admin, clusters, *, *, allow
      p, role:admin, repositories, *, *, allow
      p, role:developer, applications, get, itdo-erp-*/*, allow
      p, role:developer, applications, sync, itdo-erp-dev/*, allow
      g, itdo-erp:platform-team, role:admin
      g, itdo-erp:dev-team, role:developer
```

### App of Apps Pattern
```yaml
# apps/app-of-apps.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app-of-apps
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/itdo-erp-infrastructure
    targetRevision: HEAD
    path: argocd/applications
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Application Sets
```yaml
# argocd/applicationsets/environments.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: itdo-erp-environments
  namespace: argocd
spec:
  generators:
  - git:
      repoURL: https://github.com/company/itdo-erp-infrastructure
      revision: HEAD
      directories:
      - path: environments/*
  template:
    metadata:
      name: 'itdo-erp-{{path.basename}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/company/itdo-erp-infrastructure
        targetRevision: HEAD
        path: '{{path}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: 'itdo-erp-{{path.basename}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
        - CreateNamespace=true
```

## 🛠️ CI/CD Pipeline Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/gitops-deployment.yml
name: GitOps Deployment

on:
  push:
    branches: [main, develop]
    paths: ['src/**', 'Dockerfile', 'helm/**']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: itdo-erp

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ github.repository }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push Docker image
      id: build
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./backend/Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  update-gitops:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Checkout GitOps repository
      uses: actions/checkout@v4
      with:
        repository: company/itdo-erp-infrastructure
        token: ${{ secrets.GITOPS_TOKEN }}
        path: gitops
    
    - name: Update image tag
      run: |
        cd gitops
        NEW_TAG=$(echo "${{ needs.build-and-push.outputs.image-tag }}" | head -n1)
        
        # Update staging environment first
        yq eval ".images[0].newTag = \"${NEW_TAG}\"" -i environments/staging/kustomization.yaml
        
        # Commit changes
        git config user.name "GitOps Bot"
        git config user.email "gitops@company.com"
        git add environments/staging/kustomization.yaml
        git commit -m "Update staging image to ${NEW_TAG}"
        git push origin main

  promote-to-production:
    needs: [build-and-push, update-gitops]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - name: Checkout GitOps repository
      uses: actions/checkout@v4
      with:
        repository: company/itdo-erp-infrastructure
        token: ${{ secrets.GITOPS_TOKEN }}
        path: gitops
    
    - name: Promote to production
      run: |
        cd gitops
        NEW_TAG=$(echo "${{ needs.build-and-push.outputs.image-tag }}" | head -n1)
        
        # Update production environment
        yq eval ".images[0].newTag = \"${NEW_TAG}\"" -i environments/production/kustomization.yaml
        
        # Commit changes
        git config user.name "GitOps Bot"
        git config user.email "gitops@company.com"
        git add environments/production/kustomization.yaml
        git commit -m "Promote to production: ${NEW_TAG}"
        git push origin main
```

### Tekton Pipeline (Alternative)
```yaml
# tekton/pipeline.yaml
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: itdo-erp-gitops-pipeline
  namespace: tekton-pipelines
spec:
  params:
  - name: git-url
    type: string
    description: Git repository URL
  - name: git-revision
    type: string
    description: Git revision to build
    default: main
  - name: image-name
    type: string
    description: Container image name
  
  workspaces:
  - name: shared-data
  - name: git-credentials
  
  tasks:
  - name: git-clone
    taskRef:
      name: git-clone
    workspaces:
    - name: output
      workspace: shared-data
    - name: ssh-directory
      workspace: git-credentials
    params:
    - name: url
      value: $(params.git-url)
    - name: revision
      value: $(params.git-revision)
  
  - name: build-image
    taskRef:
      name: buildah
    runAfter:
    - git-clone
    workspaces:
    - name: source
      workspace: shared-data
    params:
    - name: IMAGE
      value: $(params.image-name):$(tasks.git-clone.results.commit)
    - name: DOCKERFILE
      value: ./backend/Dockerfile
  
  - name: update-gitops
    taskRef:
      name: git-cli
    runAfter:
    - build-image
    workspaces:
    - name: source
      workspace: shared-data
    - name: input
      workspace: git-credentials
    params:
    - name: GIT_USER_NAME
      value: "Tekton Pipeline"
    - name: GIT_USER_EMAIL
      value: "tekton@company.com"
    - name: GIT_SCRIPT
      value: |
        git clone https://github.com/company/itdo-erp-infrastructure
        cd itdo-erp-infrastructure
        NEW_TAG=$(tasks.git-clone.results.commit)
        yq eval ".images[0].newTag = \"${NEW_TAG}\"" -i environments/staging/kustomization.yaml
        git add environments/staging/kustomization.yaml
        git commit -m "Update staging image to ${NEW_TAG}"
        git push origin main
```

## 🔐 Security and Compliance

### Policy as Code
```yaml
# policies/security-policy.yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: gitops-security-policy
spec:
  validationFailureAction: enforce
  background: true
  rules:
  - name: require-non-root-user
    match:
      any:
      - resources:
          kinds:
          - Deployment
          - DaemonSet
          - StatefulSet
    validate:
      message: "Containers must run as non-root user"
      pattern:
        spec:
          template:
            spec:
              securityContext:
                runAsNonRoot: true
  
  - name: require-resource-limits
    match:
      any:
      - resources:
          kinds:
          - Deployment
          - DaemonSet
          - StatefulSet
    validate:
      message: "Resource limits are required"
      pattern:
        spec:
          template:
            spec:
              containers:
              - name: "*"
                resources:
                  limits:
                    memory: "?*"
                    cpu: "?*"
```

### Secret Management
```yaml
# sealed-secrets/database-secret.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: database-secret
  namespace: itdo-erp-prod
spec:
  encryptedData:
    POSTGRES_PASSWORD: AgBy3i4OJSWK+PiTySYZZA9rO43cGDEQAx...
    DATABASE_URL: AgBy3i4OJSWK+PiTySYZZA9rO43cGDEQAx...
  template:
    metadata:
      name: database-secret
      namespace: itdo-erp-prod
    type: Opaque
```

### External Secrets Operator
```yaml
# external-secrets/vault-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: itdo-erp-prod
spec:
  provider:
    vault:
      server: "https://vault.company.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "itdo-erp-role"
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
  namespace: itdo-erp-prod
spec:
  refreshInterval: 15s
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: app-secrets
    creationPolicy: Owner
  data:
  - secretKey: database-password
    remoteRef:
      key: itdo-erp/database
      property: password
  - secretKey: jwt-secret
    remoteRef:
      key: itdo-erp/auth
      property: jwt-secret
```

## 📊 Monitoring and Observability

### ArgoCD Metrics
```yaml
# monitoring/argocd-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argocd-metrics
  namespace: argocd
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-metrics
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argocd-server-metrics
  namespace: argocd
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-server-metrics
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### GitOps Dashboard
```yaml
# monitoring/gitops-dashboard.json
{
  "dashboard": {
    "title": "GitOps Operations Dashboard",
    "panels": [
      {
        "title": "Application Sync Status",
        "type": "stat",
        "targets": [
          {
            "expr": "sum by (name) (argocd_app_info{sync_status=\"Synced\"})",
            "legendFormat": "Synced Applications"
          }
        ]
      },
      {
        "title": "Application Health",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (health_status) (argocd_app_info)",
            "legendFormat": "{{health_status}}"
          }
        ]
      },
      {
        "title": "Deployment Frequency",
        "type": "graph",
        "targets": [
          {
            "expr": "increase(argocd_app_sync_total[1h])",
            "legendFormat": "Deployments per hour"
          }
        ]
      }
    ]
  }
}
```

## 🚨 Notification and Alerting

### ArgoCD Notifications
```yaml
# notifications/notifications-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
  template.app-deployed: |
    message: |
      Application {{.app.metadata.name}} deployed to {{.app.spec.destination.namespace}}
      Sync Status: {{.app.status.sync.status}}
      Health Status: {{.app.status.health.status}}
      Repository: {{.app.spec.source.repoURL}}
      Revision: {{.app.status.sync.revision}}
  template.app-health-degraded: |
    message: |
      🚨 Application {{.app.metadata.name}} health is degraded
      Current Status: {{.app.status.health.status}}
      Message: {{.app.status.health.message}}
  trigger.on-deployed: |
    - when: app.status.sync.status == 'Synced'
      send: [app-deployed]
  trigger.on-health-degraded: |
    - when: app.status.health.status == 'Degraded'
      send: [app-health-degraded]
  subscriptions: |
    - recipients:
      - slack:engineering
      triggers:
      - on-deployed
      - on-health-degraded
```

## 🔄 Rollback Strategies

### Automated Rollback
```yaml
# rollback/rollback-policy.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: backend-api
  namespace: itdo-erp-prod
spec:
  replicas: 5
  strategy:
    canary:
      canaryService: backend-api-canary
      stableService: backend-api-stable
      steps:
      - setWeight: 20
      - pause:
          duration: 5m
      - setWeight: 40
      - pause:
          duration: 10m
      - setWeight: 60
      - pause:
          duration: 10m
      - setWeight: 80
      - pause:
          duration: 10m
      analysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: backend-api-canary
        startingStep: 2
        interval: 10s
        count: 5
        failureLimit: 3
        successCondition: result[0] >= 0.95
  selector:
    matchLabels:
      app: backend-api
  template:
    metadata:
      labels:
        app: backend-api
    spec:
      containers:
      - name: api
        image: itdo-erp/backend:latest
```

### Manual Rollback Procedure
```bash
#!/bin/bash
# scripts/rollback.sh

set -e

APP_NAME="itdo-erp-prod"
ENVIRONMENT="production"
PREVIOUS_REVISION=""

# Get current application status
echo "Getting current application status..."
argocd app get $APP_NAME

# List previous revisions
echo "Available revisions:"
argocd app history $APP_NAME

# Prompt for rollback revision
read -p "Enter revision to rollback to: " PREVIOUS_REVISION

# Confirm rollback
read -p "Rollback $APP_NAME to revision $PREVIOUS_REVISION? (y/N): " confirm
if [[ $confirm != "y" ]]; then
    echo "Rollback cancelled"
    exit 1
fi

# Perform rollback
echo "Rolling back $APP_NAME to revision $PREVIOUS_REVISION..."
argocd app rollback $APP_NAME $PREVIOUS_REVISION

# Monitor rollback status
echo "Monitoring rollback status..."
argocd app wait $APP_NAME --health

echo "Rollback completed successfully!"
```

## 🎯 Implementation Roadmap

### Phase 1: Foundation Setup (Week 1)
1. **ArgoCD Installation**
   - Deploy ArgoCD in cluster
   - Configure RBAC and security
   - Setup SSL/TLS certificates
   - Configure authentication

2. **Repository Structure**
   - Create GitOps repositories
   - Setup branch protection rules
   - Configure webhooks
   - Initial Kustomize structure

### Phase 2: Basic GitOps (Week 2)
1. **Application Deployment**
   - Convert current deployments to GitOps
   - Setup App of Apps pattern
   - Configure sync policies
   - Test basic functionality

2. **CI/CD Integration**
   - GitHub Actions integration
   - Image building pipeline
   - GitOps repository updates
   - Automated testing

### Phase 3: Advanced Features (Week 3)
1. **Progressive Delivery**
   - Canary deployments
   - Blue-green deployments
   - Automated rollbacks
   - Health checks

2. **Security Integration**
   - Policy as code
   - Secret management
   - Image scanning
   - Compliance monitoring

### Phase 4: Monitoring & Operations (Week 4)
1. **Observability**
   - GitOps metrics
   - Deployment dashboards
   - Alert configuration
   - Performance monitoring

2. **Operational Procedures**
   - Runbooks creation
   - Incident response
   - Change management
   - Training materials

## ✅ Success Metrics

### Deployment Metrics
- **Deployment Frequency**: Daily deployments to staging
- **Lead Time**: < 2 hours from commit to production
- **Change Failure Rate**: < 5%
- **Mean Time to Recovery**: < 30 minutes

### Operational Metrics
- **Sync Success Rate**: > 99%
- **Configuration Drift**: 0 instances
- **Security Compliance**: 100%
- **Rollback Success Rate**: > 95%

---

**Document Status**: Design Phase Complete  
**Next Phase**: Zero-Trust Security Design  
**Implementation Risk**: LOW (Design Only)  
**Production Impact**: NONE