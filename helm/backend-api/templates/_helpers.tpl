{{/*
Expand the name of the chart.
*/}}
{{- define "backend-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "backend-api.fullname" -}}
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
{{- define "backend-api.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "backend-api.labels" -}}
helm.sh/chart: {{ include "backend-api.chart" . }}
{{ include "backend-api.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: backend
app.kubernetes.io/part-of: itdo-erp
{{- end }}

{{/*
Selector labels
*/}}
{{- define "backend-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "backend-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "backend-api.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "backend-api.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate database URL
*/}}
{{- define "backend-api.databaseUrl" -}}
postgresql://{{ .Values.database.user }}:$(DATABASE_PASSWORD)@{{ .Values.database.host }}:{{ .Values.database.port }}/{{ .Values.database.name }}?sslmode={{ .Values.database.sslMode }}
{{- end }}

{{/*
Generate Redis URL
*/}}
{{- define "backend-api.redisUrl" -}}
redis://{{ .Values.redis.host }}:{{ .Values.redis.port }}/{{ .Values.redis.database }}
{{- end }}

{{/*
Environment-specific resource overrides
*/}}
{{- define "backend-api.resources" -}}
{{- if eq .Values.config.environment "dev" }}
{{- toYaml .Values.dev.resources }}
{{- else if eq .Values.config.environment "staging" }}
{{- toYaml .Values.staging.resources }}
{{- else }}
{{- toYaml .Values.resources }}
{{- end }}
{{- end }}

{{/*
Environment-specific replica count
*/}}
{{- define "backend-api.replicaCount" -}}
{{- if eq .Values.config.environment "dev" }}
{{- .Values.dev.replicaCount }}
{{- else if eq .Values.config.environment "staging" }}
{{- .Values.staging.replicaCount }}
{{- else }}
{{- .Values.replicaCount }}
{{- end }}
{{- end }}