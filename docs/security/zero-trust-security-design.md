# Zero-Trust Security Design for ITDO ERP v2

## 🎯 Overview

This document outlines the Zero-Trust security architecture for ITDO ERP, implementing "never trust, always verify" principles across all infrastructure, applications, and data access patterns.

## 🛡️ Zero-Trust Principles

### Core Tenets
1. **Never Trust, Always Verify**: No implicit trust based on location
2. **Least Privilege Access**: Minimal necessary permissions
3. **Assume Breach**: Design for containment and detection
4. **Verify Explicitly**: Authenticate and authorize every transaction
5. **Continuous Monitoring**: Real-time security posture assessment

### Implementation Layers
- **Identity Layer**: Strong authentication and authorization
- **Device Layer**: Device compliance and health verification
- **Network Layer**: Micro-segmentation and encryption
- **Application Layer**: API security and runtime protection
- **Data Layer**: Classification, encryption, and access controls

## 🏗️ Architecture Overview

### Zero-Trust Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet Gateway                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Web Application Firewall                     │
│                    (CloudFlare/AWS WAF)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Load Balancer + DDoS                        │
│                    (NGINX/HAProxy)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Service Mesh (Istio)                         │
│           ┌─────────────────┬─────────────────┐              │
│           │   mTLS Layer    │  Policy Engine  │              │
│           └─────────────────┴─────────────────┘              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Kubernetes Cluster                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  Frontend   │ │   Backend   │ │  Database   │           │
│  │  Namespace  │ │  Namespace  │ │  Namespace  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│          Network Policies + RBAC + Pod Security            │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Identity and Access Management

### Identity Provider Integration
```yaml
# identity/keycloak-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: keycloak-config
  namespace: identity
data:
  realm.json: |
    {
      "realm": "itdo-erp",
      "enabled": true,
      "sslRequired": "external",
      "registrationAllowed": false,
      "loginWithEmailAllowed": true,
      "duplicateEmailsAllowed": false,
      "resetPasswordAllowed": true,
      "editUsernameAllowed": false,
      "bruteForceProtected": true,
      "permanentLockout": false,
      "maxFailureWaitSeconds": 900,
      "minimumQuickLoginWaitSeconds": 60,
      "waitIncrementSeconds": 60,
      "quickLoginCheckMilliSeconds": 1000,
      "maxDeltaTimeSeconds": 43200,
      "failureFactor": 30,
      "roles": {
        "realm": [
          {"name": "admin", "description": "Administrator role"},
          {"name": "manager", "description": "Manager role"},
          {"name": "user", "description": "Standard user role"},
          {"name": "readonly", "description": "Read-only access"}
        ]
      },
      "defaultRoles": ["user"],
      "requiredActions": [
        "VERIFY_EMAIL",
        "UPDATE_PASSWORD",
        "CONFIGURE_TOTP"
      ],
      "otpPolicyType": "totp",
      "otpPolicyAlgorithm": "HmacSHA256",
      "otpPolicyDigits": 6,
      "otpPolicyLookAheadWindow": 1,
      "otpPolicyPeriod": 30,
      "passwordPolicy": "length(12) and digits(2) and lowerCase(2) and upperCase(2) and specialChars(2) and notUsername and notEmail"
    }
```

### Multi-Factor Authentication
```yaml
# identity/mfa-policy.yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: enforce-mfa
spec:
  validationFailureAction: enforce
  rules:
  - name: require-mfa-annotation
    match:
      any:
      - resources:
          kinds:
          - ServiceAccount
    validate:
      message: "ServiceAccounts must have MFA enabled"
      pattern:
        metadata:
          annotations:
            security.itdo-erp.com/mfa-required: "true"
```

### RBAC Configuration
```yaml
# rbac/role-definitions.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: itdo-erp-admin
rules:
- apiGroups: [""]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["apps"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: itdo-erp-developer
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: itdo-erp-readonly
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
```

### Service Account Security
```yaml
# rbac/service-accounts.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-api
  namespace: itdo-erp-prod
  annotations:
    security.itdo-erp.com/mfa-required: "true"
    security.itdo-erp.com/access-review: "quarterly"
automountServiceAccountToken: false
---
apiVersion: v1
kind: Secret
metadata:
  name: backend-api-token
  namespace: itdo-erp-prod
  annotations:
    kubernetes.io/service-account.name: backend-api
type: kubernetes.io/service-account-token
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: backend-api-binding
  namespace: itdo-erp-prod
subjects:
- kind: ServiceAccount
  name: backend-api
  namespace: itdo-erp-prod
roleRef:
  kind: Role
  name: itdo-erp-developer
  apiGroup: rbac.authorization.k8s.io
```

## 🌐 Network Security

### Service Mesh Configuration (Istio)
```yaml
# network/istio-security.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: itdo-erp-prod
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: frontend-authz
  namespace: itdo-erp-prod
spec:
  selector:
    matchLabels:
      app: frontend
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account"]
  - to:
    - operation:
        methods: ["GET", "POST"]
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: backend-authz
  namespace: itdo-erp-prod
spec:
  selector:
    matchLabels:
      app: backend-api
  rules:
  - from:
    - source:
        principals: 
        - "cluster.local/ns/itdo-erp-prod/sa/frontend"
        - "cluster.local/ns/itdo-erp-prod/sa/api-gateway"
  - to:
    - operation:
        methods: ["GET", "POST", "PUT", "DELETE"]
        paths: ["/api/v1/*"]
  - when:
    - key: request.headers[authorization]
      values: ["Bearer *"]
```

### Network Policies
```yaml
# network/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-default
  namespace: itdo-erp-prod
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-network-policy
  namespace: itdo-erp-prod
spec:
  podSelector:
    matchLabels:
      tier: frontend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: istio-system
    ports:
    - protocol: TCP
      port: 3000
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - protocol: TCP
      port: 8000
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: itdo-erp-prod
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    - podSelector:
        matchLabels:
          tier: gateway
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          tier: cache
    ports:
    - protocol: TCP
      port: 6379
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 443
```

### Encryption in Transit
```yaml
# network/tls-config.yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: itdo-erp-gateway
  namespace: itdo-erp-prod
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: itdo-erp-tls
    hosts:
    - "*.itdo-erp.com"
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*.itdo-erp.com"
    tls:
      httpsRedirect: true
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: backend-tls
  namespace: itdo-erp-prod
spec:
  host: backend-api.itdo-erp-prod.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
  portLevelSettings:
  - port:
      number: 8000
    tls:
      mode: ISTIO_MUTUAL
```

## 🔒 Application Security

### Container Security
```yaml
# security/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: itdo-erp-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
  hostNetwork: false
  hostIPC: false
  hostPID: false
---
apiVersion: v1
kind: SecurityContext
metadata:
  name: itdo-erp-security-context
spec:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 3000
  fsGroup: 2000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  seccompProfile:
    type: RuntimeDefault
```

### Runtime Security
```yaml
# security/falco-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-rules
  namespace: security
data:
  itdo_erp_rules.yaml: |
    - rule: Unauthorized API Access
      desc: Detect unauthorized access to ITDO ERP APIs
      condition: >
        k8s_audit and
        ka.target.resource contains "itdo-erp" and
        ka.verb in (create, update, delete) and
        not ka.user.name in (system:serviceaccount:itdo-erp-prod:backend-api,
                             system:serviceaccount:itdo-erp-prod:frontend)
      output: >
        Unauthorized API access detected
        (user=%ka.user.name verb=%ka.verb resource=%ka.target.resource
         reason=%ka.reason.reason)
      priority: WARNING
    
    - rule: Suspicious Network Activity
      desc: Detect suspicious network connections from ITDO ERP pods
      condition: >
        fd.sport != 0 and
        container.image.repository contains "itdo-erp" and
        not fd.rip in (postgres_ips, redis_ips, internal_services)
      output: >
        Suspicious network connection from ITDO ERP container
        (container=%container.name dest_ip=%fd.rip dest_port=%fd.rport)
      priority: WARNING
    
    - rule: File System Modification
      desc: Detect unauthorized file system modifications
      condition: >
        open_write and
        container.image.repository contains "itdo-erp" and
        fd.filename startswith "/app" and
        not fd.filename startswith "/app/logs"
      output: >
        Unauthorized file modification in ITDO ERP container
        (container=%container.name file=%fd.name)
      priority: ERROR
```

### API Security
```yaml
# security/api-security.yaml
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: api-jwt
  namespace: itdo-erp-prod
spec:
  selector:
    matchLabels:
      app: backend-api
  jwtRules:
  - issuer: "https://auth.itdo-erp.com/auth/realms/itdo-erp"
    jwksUri: "https://auth.itdo-erp.com/auth/realms/itdo-erp/protocol/openid_connect/certs"
    audiences:
    - "itdo-erp-api"
    forwardOriginalToken: true
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: api-authz
  namespace: itdo-erp-prod
spec:
  selector:
    matchLabels:
      app: backend-api
  rules:
  - from:
    - source:
        requestPrincipals: ["*"]
  - to:
    - operation:
        methods: ["GET", "POST", "PUT", "DELETE"]
        paths: ["/api/v1/*"]
  - when:
    - key: request.auth.claims[aud]
      values: ["itdo-erp-api"]
    - key: request.auth.claims[scope]
      values: ["read", "write", "admin"]
```

## 🛡️ Data Protection

### Data Classification
```yaml
# data/classification-labels.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: data-classification
  namespace: itdo-erp-prod
  labels:
    data.classification: "confidential"
data:
  classification-policy: |
    # Data Classification Policy
    
    ## PUBLIC (Label: public)
    - API documentation
    - Public facing content
    - Marketing materials
    
    ## INTERNAL (Label: internal)
    - Internal documentation
    - System logs (non-sensitive)
    - Configuration templates
    
    ## CONFIDENTIAL (Label: confidential)
    - User authentication data
    - Business logic code
    - Internal metrics
    
    ## RESTRICTED (Label: restricted)
    - Personal Identifiable Information (PII)
    - Financial data
    - Authentication secrets
    - Database credentials
    
    ## Handling Requirements by Classification:
    - PUBLIC: No special handling required
    - INTERNAL: Access control required
    - CONFIDENTIAL: Encryption at rest and in transit
    - RESTRICTED: Encryption + audit logging + need-to-know access
```

### Encryption at Rest
```yaml
# data/encryption-config.yaml
apiVersion: v1
kind: Secret
metadata:
  name: encryption-key
  namespace: itdo-erp-prod
  labels:
    data.classification: "restricted"
type: Opaque
data:
  key: <base64-encoded-encryption-key>
---
apiVersion: v1
kind: StorageClass
metadata:
  name: encrypted-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:region:account:key/key-id"
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
  namespace: itdo-erp-prod
  labels:
    data.classification: "restricted"
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: encrypted-ssd
  resources:
    requests:
      storage: 100Gi
```

### Database Security
```yaml
# data/database-security.yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
  namespace: itdo-erp-prod
spec:
  instances: 3
  postgresql:
    parameters:
      # Enable SSL/TLS
      ssl: "on"
      ssl_cert_file: "/opt/certs/tls.crt"
      ssl_key_file: "/opt/certs/tls.key"
      ssl_ca_file: "/opt/certs/ca.crt"
      ssl_crl_file: ""
      
      # Security settings
      log_connections: "on"
      log_disconnections: "on"
      log_statement: "all"
      shared_preload_libraries: "pg_stat_statements,pg_audit"
      
      # Audit settings
      pgaudit.log: "all"
      pgaudit.log_catalog: "off"
      pgaudit.log_parameter: "on"
      pgaudit.log_relation: "on"
      pgaudit.log_statement_once: "on"
      
      # Performance and security
      max_connections: "100"
      password_encryption: "scram-sha-256"
      
  certificates:
    serverTLSSecret: "postgres-server-cert"
    serverCASecret: "postgres-ca-cert"
    clientCASecret: "postgres-ca-cert"
    replicationTLSSecret: "postgres-replication-cert"
    
  monitoring:
    enabled: true
    podMonitorMetricRelabelings:
    - sourceLabels: [__name__]
      regex: 'pg_.*'
      targetLabel: __name__
      replacement: 'postgres_${1}'
```

## 🔍 Monitoring and Auditing

### Security Monitoring
```yaml
# monitoring/security-monitoring.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: zero-trust-security-rules
  namespace: security
spec:
  groups:
  - name: authentication
    rules:
    - alert: HighFailedAuthentications
      expr: rate(keycloak_failed_login_attempts[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
        category: security
      annotations:
        summary: "High rate of failed authentication attempts"
        description: "Failed login rate is {{ $value }} per second"
    
    - alert: UnauthorizedAPIAccess
      expr: rate(istio_requests_total{response_code="401"}[5m]) > 0.05
      for: 1m
      labels:
        severity: critical
        category: security
      annotations:
        summary: "High rate of unauthorized API access attempts"
        description: "Unauthorized access rate is {{ $value }} per second"
  
  - name: network
    rules:
    - alert: UnexpectedNetworkConnection
      expr: rate(falco_events_total{rule_name="Suspicious Network Activity"}[5m]) > 0
      for: 0m
      labels:
        severity: critical
        category: security
      annotations:
        summary: "Unexpected network connections detected"
        description: "Falco detected {{ $value }} suspicious network connections"
    
    - alert: NetworkPolicyViolation
      expr: rate(networkpolicy_violations_total[5m]) > 0
      for: 0m
      labels:
        severity: warning
        category: security
      annotations:
        summary: "Network policy violations detected"
        description: "{{ $value }} network policy violations in the last 5 minutes"
  
  - name: runtime
    rules:
    - alert: PrivilegeEscalation
      expr: rate(falco_events_total{rule_name="Privilege Escalation"}[5m]) > 0
      for: 0m
      labels:
        severity: critical
        category: security
      annotations:
        summary: "Privilege escalation detected"
        description: "Falco detected {{ $value }} privilege escalation attempts"
```

### Audit Logging
```yaml
# monitoring/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log all security-related events at Metadata level
- level: Metadata
  namespaces: ["itdo-erp-prod", "itdo-erp-staging"]
  resources:
  - group: ""
    resources: ["secrets", "serviceaccounts"]
  - group: "rbac.authorization.k8s.io"
    resources: ["*"]
  - group: "security.istio.io"
    resources: ["*"]

# Log all requests to sensitive APIs at Request level
- level: Request
  namespaces: ["itdo-erp-prod"]
  resources:
  - group: ""
    resources: ["pods/exec", "pods/portforward", "pods/proxy"]
  verbs: ["create"]

# Log authentication events
- level: Request
  resources:
  - group: "authentication.k8s.io"
    resources: ["tokenreviews"]

# Log authorization events
- level: Request
  resources:
  - group: "authorization.k8s.io"
    resources: ["subjectaccessreviews"]

# Log changes to security policies
- level: RequestResponse
  namespaces: ["itdo-erp-prod"]
  resources:
  - group: "networking.k8s.io"
    resources: ["networkpolicies"]
  - group: "policy"
    resources: ["podsecuritypolicies"]
  verbs: ["create", "update", "patch", "delete"]
```

### Compliance Monitoring
```yaml
# compliance/cis-compliance.yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: cis-kubernetes-compliance
  annotations:
    policies.kyverno.io/title: CIS Kubernetes Compliance
    policies.kyverno.io/category: Security
    policies.kyverno.io/severity: high
spec:
  validationFailureAction: enforce
  background: true
  rules:
  - name: disallow-privileged-containers
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Privileged containers are not allowed"
      pattern:
        spec:
          =(securityContext):
            =(privileged): "false"
          containers:
          - name: "*"
            =(securityContext):
              =(privileged): "false"
  
  - name: require-non-root-user
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Containers must run as non-root user"
      pattern:
        spec:
          =(securityContext):
            =(runAsNonRoot): "true"
          containers:
          - name: "*"
            =(securityContext):
              =(runAsNonRoot): "true"
  
  - name: disallow-host-namespaces
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Host namespaces are not allowed"
      pattern:
        spec:
          =(hostPID): "false"
          =(hostIPC): "false"
          =(hostNetwork): "false"
```

## 🚨 Incident Response

### Automated Response
```yaml
# incident/automated-response.yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: security-incident-response
  namespace: security
spec:
  entrypoint: incident-response
  templates:
  - name: incident-response
    dag:
      tasks:
      - name: assess-threat
        template: threat-assessment
      - name: isolate-workload
        template: workload-isolation
        dependencies: [assess-threat]
        when: "{{tasks.assess-threat.outputs.parameters.severity}} == critical"
      - name: collect-evidence
        template: evidence-collection
        dependencies: [assess-threat]
      - name: notify-team
        template: notification
        dependencies: [assess-threat]
  
  - name: threat-assessment
    script:
      image: security-tools:latest
      command: [python]
      source: |
        import json
        import sys
        
        # Analyze security alerts
        severity = analyze_security_event()
        
        with open('/tmp/assessment.json', 'w') as f:
            json.dump({'severity': severity}, f)
    outputs:
      parameters:
      - name: severity
        valueFrom:
          path: /tmp/assessment.json
          parameter: severity
  
  - name: workload-isolation
    resource:
      action: create
      manifest: |
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        metadata:
          name: emergency-isolation
          namespace: itdo-erp-prod
        spec:
          podSelector:
            matchLabels:
              security.incident: "true"
          policyTypes:
          - Ingress
          - Egress
          # Deny all traffic
  
  - name: evidence-collection
    script:
      image: forensics-tools:latest
      command: [bash]
      source: |
        # Collect logs, network traces, and system state
        kubectl logs -l app=backend-api --since=1h > /evidence/application.log
        kubectl get events --sort-by=.metadata.creationTimestamp > /evidence/events.log
        kubectl describe pods -l app=backend-api > /evidence/pod-state.log
    volumeMounts:
    - name: evidence
      mountPath: /evidence
  
  - name: notification
    container:
      image: notification-service:latest
      command: ["notify"]
      args: ["--channel", "security", "--severity", "{{workflow.parameters.severity}}"]
```

### Manual Response Procedures
```bash
#!/bin/bash
# scripts/security-incident-response.sh

set -e

INCIDENT_ID="SEC-$(date +%Y%m%d-%H%M%S)"
EVIDENCE_DIR="/tmp/evidence/${INCIDENT_ID}"
NAMESPACE="itdo-erp-prod"

echo "🚨 Security Incident Response Started"
echo "Incident ID: ${INCIDENT_ID}"
echo "Timestamp: $(date)"

# Create evidence collection directory
mkdir -p "${EVIDENCE_DIR}"

# 1. Immediate Assessment
echo "📊 Collecting system state..."
kubectl get pods -n "${NAMESPACE}" -o wide > "${EVIDENCE_DIR}/pods.log"
kubectl get events -n "${NAMESPACE}" --sort-by=.metadata.creationTimestamp > "${EVIDENCE_DIR}/events.log"
kubectl get networkpolicies -n "${NAMESPACE}" > "${EVIDENCE_DIR}/network-policies.log"

# 2. Log Collection
echo "📝 Collecting application logs..."
for pod in $(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.name}'); do
    kubectl logs "${pod}" -n "${NAMESPACE}" --since=2h > "${EVIDENCE_DIR}/${pod}.log" 2>/dev/null || true
done

# 3. Security State
echo "🔐 Collecting security configuration..."
kubectl get rolebindings,clusterrolebindings -o yaml > "${EVIDENCE_DIR}/rbac.yaml"
kubectl get secrets -n "${NAMESPACE}" > "${EVIDENCE_DIR}/secrets.log"
kubectl get serviceaccounts -n "${NAMESPACE}" -o yaml > "${EVIDENCE_DIR}/serviceaccounts.yaml"

# 4. Network State
echo "🌐 Collecting network configuration..."
kubectl get services,ingresses -n "${NAMESPACE}" -o yaml > "${EVIDENCE_DIR}/network.yaml"
kubectl get endpoints -n "${NAMESPACE}" > "${EVIDENCE_DIR}/endpoints.log"

# 5. Check for IOCs (Indicators of Compromise)
echo "🔍 Scanning for indicators of compromise..."
echo "Checking for suspicious processes..."
kubectl exec -n "${NAMESPACE}" -l app=backend-api -- ps aux > "${EVIDENCE_DIR}/processes.log" 2>/dev/null || true

echo "Checking for unusual network connections..."
kubectl exec -n "${NAMESPACE}" -l app=backend-api -- netstat -tulpn > "${EVIDENCE_DIR}/connections.log" 2>/dev/null || true

# 6. Generate incident summary
cat > "${EVIDENCE_DIR}/incident-summary.md" << EOF
# Security Incident Report

**Incident ID:** ${INCIDENT_ID}
**Date/Time:** $(date)
**Namespace:** ${NAMESPACE}
**Investigator:** $(whoami)

## Initial Assessment

### Timeline
- **Detection Time:** $(date)
- **Response Time:** $(date)

### Affected Resources
- Namespace: ${NAMESPACE}
- Pods: $(kubectl get pods -n "${NAMESPACE}" --no-headers | wc -l)
- Services: $(kubectl get services -n "${NAMESPACE}" --no-headers | wc -l)

### Evidence Collected
$(ls -la "${EVIDENCE_DIR}")

## Recommended Actions

1. **Immediate:**
   - [ ] Review evidence files
   - [ ] Determine scope of impact
   - [ ] Implement containment measures

2. **Short-term:**
   - [ ] Patch identified vulnerabilities
   - [ ] Update security policies
   - [ ] Enhance monitoring

3. **Long-term:**
   - [ ] Conduct post-incident review
   - [ ] Update incident response procedures
   - [ ] Implement additional preventive measures

EOF

echo "✅ Evidence collection completed"
echo "📁 Evidence stored in: ${EVIDENCE_DIR}"
echo "📋 Review incident summary: ${EVIDENCE_DIR}/incident-summary.md"

# Optional: Upload to secure storage
if [ -n "${EVIDENCE_BUCKET}" ]; then
    echo "📤 Uploading evidence to secure storage..."
    tar -czf "${INCIDENT_ID}-evidence.tar.gz" -C "/tmp/evidence" "${INCIDENT_ID}"
    aws s3 cp "${INCIDENT_ID}-evidence.tar.gz" "s3://${EVIDENCE_BUCKET}/incidents/"
    echo "✅ Evidence uploaded to s3://${EVIDENCE_BUCKET}/incidents/${INCIDENT_ID}-evidence.tar.gz"
fi
```

## 🎯 Implementation Roadmap

### Phase 1: Identity Foundation (Week 1-2)
1. **Identity Provider Setup**
   - Deploy and configure Keycloak
   - Setup realm and authentication flows
   - Configure MFA policies
   - Integrate with existing systems

2. **RBAC Implementation**
   - Design role hierarchy
   - Implement Kubernetes RBAC
   - Setup service account security
   - Configure audit logging

### Phase 2: Network Security (Week 3-4)
1. **Service Mesh Deployment**
   - Install and configure Istio
   - Enable mTLS cluster-wide
   - Implement authorization policies
   - Configure ingress security

2. **Network Segmentation**
   - Deploy network policies
   - Implement micro-segmentation
   - Configure traffic encryption
   - Setup monitoring

### Phase 3: Application Security (Week 5-6)
1. **Container Security**
   - Implement pod security standards
   - Configure runtime security
   - Deploy image scanning
   - Setup vulnerability management

2. **API Security**
   - Implement JWT authentication
   - Configure authorization policies
   - Setup rate limiting
   - Enable API monitoring

### Phase 4: Data Protection (Week 7-8)
1. **Encryption Implementation**
   - Enable encryption at rest
   - Configure encryption in transit
   - Implement key management
   - Setup data classification

2. **Compliance & Monitoring**
   - Deploy compliance scanning
   - Configure security monitoring
   - Setup incident response
   - Implement automated remediation

## ✅ Success Metrics

### Security Posture
- **Authentication Success Rate**: > 99.9%
- **Authorization Violations**: < 0.1% of requests
- **Encryption Coverage**: 100% of data at rest and in transit
- **Network Policy Compliance**: 100%

### Incident Response
- **Mean Time to Detection (MTTD)**: < 5 minutes
- **Mean Time to Response (MTTR)**: < 15 minutes
- **False Positive Rate**: < 5%
- **Security Training Completion**: 100%

### Compliance
- **CIS Kubernetes Compliance**: > 95%
- **OWASP Top 10 Coverage**: 100%
- **Audit Trail Completeness**: 100%
- **Vulnerability Remediation**: < 30 days

---

**Document Status**: Design Phase Complete  
**Next Phase**: FinOps Platform Design  
**Implementation Risk**: LOW (Design Only)  
**Production Impact**: NONE