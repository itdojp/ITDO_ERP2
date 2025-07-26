{{/*
Expand the name of the chart.
*/}}
{{- define "itdo-erp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "itdo-erp.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "itdo-erp.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "itdo-erp.labels" -}}
helm.sh/chart: {{ include "itdo-erp.chart" . }}
{{ include "itdo-erp.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: {{ include "itdo-erp.name" . }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "itdo-erp.selectorLabels" -}}
app.kubernetes.io/name: {{ include "itdo-erp.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Backend labels
*/}}
{{- define "itdo-erp.backend.labels" -}}
{{ include "itdo-erp.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "itdo-erp.backend.selectorLabels" -}}
{{ include "itdo-erp.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "itdo-erp.frontend.labels" -}}
{{ include "itdo-erp.labels" . }}
app.kubernetes.io/component: web
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "itdo-erp.frontend.selectorLabels" -}}
{{ include "itdo-erp.selectorLabels" . }}
app.kubernetes.io/component: web
{{- end }}

{{/*
Create the name of the service account to use for backend
*/}}
{{- define "itdo-erp.backend.serviceAccountName" -}}
{{- if .Values.backend.serviceAccount.create }}
{{- default (printf "%s-backend" (include "itdo-erp.fullname" .)) .Values.backend.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.backend.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the service account to use for frontend
*/}}
{{- define "itdo-erp.frontend.serviceAccountName" -}}
{{- if .Values.frontend.serviceAccount.create }}
{{- default (printf "%s-frontend" (include "itdo-erp.fullname" .)) .Values.frontend.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.frontend.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate backend image name
*/}}
{{- define "itdo-erp.backend.image" -}}
{{- if .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.backend.image.repository .Values.backend.image.tag }}
{{- else }}
{{- printf "%s:%s" .Values.backend.image.repository .Values.backend.image.tag }}
{{- end }}
{{- end }}

{{/*
Generate frontend image name
*/}}
{{- define "itdo-erp.frontend.image" -}}
{{- if .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.frontend.image.repository .Values.frontend.image.tag }}
{{- else }}
{{- printf "%s:%s" .Values.frontend.image.repository .Values.frontend.image.tag }}
{{- end }}
{{- end }}

{{/*
Database host name
*/}}
{{- define "itdo-erp.database.host" -}}
{{- if .Values.postgresql.external.enabled }}
{{- .Values.postgresql.external.host }}
{{- else }}
{{- printf "%s-postgresql" .Release.Name }}
{{- end }}
{{- end }}

{{/*
Database port
*/}}
{{- define "itdo-erp.database.port" -}}
{{- if .Values.postgresql.external.enabled }}
{{- .Values.postgresql.external.port }}
{{- else }}
{{- 5432 }}
{{- end }}
{{- end }}

{{/*
Database name
*/}}
{{- define "itdo-erp.database.name" -}}
{{- if .Values.postgresql.external.enabled }}
{{- .Values.postgresql.external.database }}
{{- else }}
{{- .Values.postgresql.auth.database }}
{{- end }}
{{- end }}

{{/*
Redis host name
*/}}
{{- define "itdo-erp.redis.host" -}}
{{- if .Values.redis.external.enabled }}
{{- .Values.redis.external.host }}
{{- else }}
{{- printf "%s-redis-master" .Release.Name }}
{{- end }}
{{- end }}

{{/*
Redis port
*/}}
{{- define "itdo-erp.redis.port" -}}
{{- if .Values.redis.external.enabled }}
{{- .Values.redis.external.port }}
{{- else }}
{{- 6379 }}
{{- end }}
{{- end }}

{{/*
Create security context
*/}}
{{- define "itdo-erp.securityContext" -}}
{{- if .Values.global.securityContext }}
securityContext:
  runAsNonRoot: {{ .Values.global.securityContext.runAsNonRoot }}
  runAsUser: {{ .Values.global.securityContext.runAsUser }}
  runAsGroup: {{ .Values.global.securityContext.runAsGroup }}
  fsGroup: {{ .Values.global.securityContext.fsGroup }}
{{- end }}
{{- end }}

{{/*
Create pod security context
*/}}
{{- define "itdo-erp.podSecurityContext" -}}
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false
  runAsNonRoot: true
  runAsUser: {{ .Values.global.securityContext.runAsUser | default 1001 }}
  runAsGroup: {{ .Values.global.securityContext.runAsGroup | default 1001 }}
  capabilities:
    drop:
    - ALL
{{- end }}

{{/*
Create image pull secrets
*/}}
{{- define "itdo-erp.imagePullSecrets" -}}
{{- if .Values.global.imagePullSecrets }}
imagePullSecrets:
{{- range .Values.global.imagePullSecrets }}
  - name: {{ . }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create affinity rules for backend
*/}}
{{- define "itdo-erp.backend.affinity" -}}
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            {{- include "itdo-erp.backend.selectorLabels" . | nindent 12 }}
        topologyKey: kubernetes.io/hostname
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      preference:
        matchExpressions:
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["m5.large", "m5.xlarge", "c5.large", "c5.xlarge"]
{{- end }}

{{/*
Create affinity rules for frontend
*/}}
{{- define "itdo-erp.frontend.affinity" -}}
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            {{- include "itdo-erp.frontend.selectorLabels" . | nindent 12 }}
        topologyKey: kubernetes.io/hostname
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      preference:
        matchExpressions:
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["t3.medium", "t3.large", "m5.large"]
{{- end }}

{{/*
Create tolerations
*/}}
{{- define "itdo-erp.tolerations" -}}
tolerations:
- key: "app.kubernetes.io/name"
  operator: "Equal"
  value: "itdo-erp"
  effect: "NoSchedule"
{{- end }}

{{/*
Create resource limits and requests
*/}}
{{- define "itdo-erp.resources" -}}
{{- if .resources }}
resources:
  {{- if .resources.limits }}
  limits:
    {{- if .resources.limits.cpu }}
    cpu: {{ .resources.limits.cpu }}
    {{- end }}
    {{- if .resources.limits.memory }}
    memory: {{ .resources.limits.memory }}
    {{- end }}
    {{- if .resources.limits.ephemeral-storage }}
    ephemeral-storage: {{ .resources.limits.ephemeral-storage }}
    {{- end }}
  {{- end }}
  {{- if .resources.requests }}
  requests:
    {{- if .resources.requests.cpu }}
    cpu: {{ .resources.requests.cpu }}
    {{- end }}
    {{- if .resources.requests.memory }}
    memory: {{ .resources.requests.memory }}
    {{- end }}
    {{- if .resources.requests.ephemeral-storage }}
    ephemeral-storage: {{ .resources.requests.ephemeral-storage }}
    {{- end }}
  {{- end }}
{{- end }}
{{- end }}

{{/*
Create environment variables for backend
*/}}
{{- define "itdo-erp.backend.env" -}}
env:
# Database Configuration
- name: DATABASE_HOST
  value: {{ include "itdo-erp.database.host" . | quote }}
- name: DATABASE_PORT
  value: {{ include "itdo-erp.database.port" . | quote }}
- name: DATABASE_NAME
  value: {{ include "itdo-erp.database.name" . | quote }}
- name: DATABASE_USER
  valueFrom:
    secretKeyRef:
      name: {{ .Values.postgresql.auth.existingSecret | default "itdo-erp-secrets" }}
      key: {{ .Values.postgresql.auth.secretKeys.userPasswordKey | default "DATABASE_USER" }}
- name: DATABASE_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Values.postgresql.auth.existingSecret | default "itdo-erp-secrets" }}
      key: {{ .Values.postgresql.auth.secretKeys.adminPasswordKey | default "DATABASE_PASSWORD" }}

# Redis Configuration
- name: REDIS_HOST
  value: {{ include "itdo-erp.redis.host" . | quote }}
- name: REDIS_PORT
  value: {{ include "itdo-erp.redis.port" . | quote }}
- name: REDIS_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Values.redis.auth.existingSecret | default "itdo-erp-secrets" }}
      key: {{ .Values.redis.auth.existingSecretPasswordKey | default "REDIS_PASSWORD" }}

# Application Configuration
{{- range $key, $value := .Values.backend.env }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}

# Security Configuration
- name: JWT_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: itdo-erp-secrets
      key: JWT_SECRET_KEY
- name: ENCRYPTION_KEY
  valueFrom:
    secretKeyRef:
      name: itdo-erp-secrets
      key: ENCRYPTION_KEY
{{- end }}

{{/*
Create environment variables for frontend
*/}}
{{- define "itdo-erp.frontend.env" -}}
env:
{{- range $key, $value := .Values.frontend.env }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}
{{- end }}