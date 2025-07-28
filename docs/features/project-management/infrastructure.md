# プロジェクト管理システム - インフラストラクチャ構成書

## 概要
プロジェクト管理システムのインフラストラクチャ設計と構成を定義します。高可用性、スケーラビリティ、セキュリティを考慮した設計となっています。

## システムアーキテクチャ

### 全体構成図
```
┌─────────────────────────────────────────────────────────────────┐
│                         ロードバランサー (Nginx)                    │
│                    SSL終端・リバースプロキシ・静的ファイル配信        │
└────────────────┬───────────────────────────────┬────────────────┘
                 │                               │
         ┌───────▼─────────┐             ┌─────▼──────────┐
         │   Frontend      │             │   Frontend     │
         │   (React App)   │             │   (React App)  │
         │   Port: 3000    │             │   Port: 3001   │
         └───────┬─────────┘             └─────┬──────────┘
                 │                               │
         ┌───────▼─────────────────────────────▼──────────┐
         │              API Gateway (Kong/Nginx)           │
         │        認証・レート制限・ルーティング・ログ        │
         └───────┬───────────────────┬────────────────────┘
                 │                   │
         ┌───────▼─────────┐ ┌──────▼──────────┐
         │   Backend API   │ │  Backend API    │
         │   (FastAPI)     │ │  (FastAPI)      │
         │   Port: 8000    │ │  Port: 8001     │
         └───────┬─────────┘ └──────┬──────────┘
                 │                   │
         ┌───────▼───────────────────▼──────────┐
         │         データベース層                 │
         ├────────────────┬─────────────────────┤
         │  PostgreSQL    │    Redis           │
         │  (Primary)     │  (Cache/Queue)     │
         │  Port: 5432    │  Port: 6379        │
         └────────┬───────┴─────────────────────┘
                  │
         ┌────────▼───────┐
         │  PostgreSQL    │
         │  (Replica)     │
         │  Port: 5433    │
         └────────────────┘
```

### コンテナ構成
```yaml
services:
  # フロントエンド（開発環境ではローカル実行）
  frontend:
    build: ./frontend
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=${API_URL}
    networks:
      - frontend-network
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  # バックエンドAPI
  backend:
    build: ./backend
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    networks:
      - backend-network
      - database-network
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G

  # Nginx（リバースプロキシ）
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    networks:
      - frontend-network
      - backend-network
    deploy:
      replicas: 2

  # データベース（本番環境ではマネージドサービス推奨）
  postgres-primary:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=itdo_erp
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - database-network
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G

  # Redis（キャッシュ・キュー）
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - database-network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

volumes:
  postgres-data:
  redis-data:

networks:
  frontend-network:
  backend-network:
  database-network:
```

## インフラストラクチャコンポーネント

### 1. ロードバランサー層
- **Nginx**: SSL終端、静的ファイル配信、リバースプロキシ
- **設定**:
  - SSL/TLS 1.3対応
  - HTTP/2有効化
  - Gzip圧縮
  - キャッシュヘッダー設定

### 2. アプリケーション層
- **Frontend**: React 18アプリケーション
  - 静的ファイルとしてビルド・配信
  - CDN経由での配信推奨
- **Backend**: FastAPI アプリケーション
  - Gunicorn/Uvicorn によるASGI実行
  - 水平スケーリング対応

### 3. データベース層
- **PostgreSQL 15**: メインデータストア
  - レプリケーション構成（プライマリ・レプリカ）
  - 自動バックアップ（日次）
  - ポイントインタイムリカバリ対応
- **Redis 7**: キャッシュ・セッション管理
  - LRUエビクション設定
  - 永続化オプション（AOF）

### 4. 認証・認可
- **Keycloak**: 外部認証プロバイダー
  - OAuth2/OpenID Connect
  - SAML対応
  - 多要素認証サポート

## パフォーマンス最適化

### 1. キャッシング戦略
```python
# Redisキャッシュ設定
CACHE_CONFIG = {
    "project_list": {
        "ttl": 300,  # 5分
        "key_pattern": "project:list:{organization_id}:{filters}"
    },
    "project_detail": {
        "ttl": 600,  # 10分
        "key_pattern": "project:detail:{project_id}"
    },
    "gantt_chart": {
        "ttl": 180,  # 3分
        "key_pattern": "gantt:{project_id}:{date_range}"
    },
    "resource_utilization": {
        "ttl": 900,  # 15分
        "key_pattern": "resource:utilization:{resource_id}:{date_range}"
    }
}
```

### 2. データベース最適化
```sql
-- パーティショニング設定（大規模データ対応）
CREATE TABLE task_progress_2025 PARTITION OF task_progress
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- 主要インデックス
CREATE INDEX CONCURRENTLY idx_projects_org_status 
    ON projects(organization_id, status) 
    WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY idx_tasks_project_dates 
    ON tasks(project_id, start_date, end_date) 
    WHERE deleted_at IS NULL;

-- マテリアライズドビュー（レポート高速化）
CREATE MATERIALIZED VIEW mv_project_summary AS
SELECT 
    p.id,
    p.name,
    COUNT(DISTINCT t.id) as task_count,
    AVG(t.progress_percentage) as avg_progress,
    COUNT(DISTINCT pm.user_id) as member_count
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id
LEFT JOIN project_members pm ON p.id = pm.project_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.name;

CREATE INDEX idx_mv_project_summary_id ON mv_project_summary(id);
```

### 3. 非同期処理
```python
# Celeryタスク定義
from celery import Celery

celery = Celery('project_management')

@celery.task
def calculate_critical_path(project_id: int):
    """クリティカルパスの非同期計算"""
    pass

@celery.task
def generate_project_report(project_id: int, format: str):
    """レポート生成の非同期処理"""
    pass

@celery.task
def update_resource_utilization():
    """リソース稼働率の定期更新"""
    pass
```

## セキュリティ設定

### 1. ネットワークセキュリティ
```yaml
# ファイアウォール設定
firewall_rules:
  - name: allow-https
    protocol: tcp
    ports: [443]
    source_ranges: ["0.0.0.0/0"]
  
  - name: allow-http
    protocol: tcp
    ports: [80]
    source_ranges: ["0.0.0.0/0"]
  
  - name: allow-internal
    protocol: tcp
    ports: [5432, 6379, 8000]
    source_ranges: ["10.0.0.0/8"]
```

### 2. アプリケーションセキュリティ
```python
# セキュリティヘッダー設定
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'"
}

# レート制限設定
RATE_LIMITS = {
    "api_global": "1000/hour",
    "api_user": "100/minute",
    "auth_login": "5/minute",
    "report_generation": "10/hour"
}
```

### 3. データ暗号化
- **通信**: TLS 1.3による暗号化
- **保存時**: PostgreSQLの透過的データ暗号化（TDE）
- **バックアップ**: AES-256による暗号化

## モニタリング・監視

### 1. メトリクス収集
```yaml
# Prometheus設定
prometheus:
  scrape_configs:
    - job_name: 'backend'
      static_configs:
        - targets: ['backend:8000']
      metrics_path: '/metrics'
    
    - job_name: 'postgres'
      static_configs:
        - targets: ['postgres-exporter:9187']
    
    - job_name: 'redis'
      static_configs:
        - targets: ['redis-exporter:9121']
```

### 2. ログ管理
```yaml
# Fluentd設定
logging:
  drivers:
    - name: fluentd
      options:
        fluentd-address: "localhost:24224"
        tag: "project-management.{{.Name}}"
  
  parsers:
    - name: backend
      format: json
      time_key: timestamp
    
    - name: nginx
      format: nginx
```

### 3. アラート設定
```yaml
alerts:
  - name: high_cpu_usage
    condition: cpu_usage > 80%
    duration: 5m
    action: scale_up
  
  - name: database_connection_pool
    condition: connection_pool_usage > 90%
    duration: 3m
    action: notify_ops
  
  - name: response_time_degradation
    condition: p95_response_time > 1000ms
    duration: 5m
    action: notify_dev
```

## バックアップ・災害復旧

### 1. バックアップ戦略
- **データベース**: 
  - 日次フルバックアップ（深夜2時）
  - 継続的アーカイブログ（WAL）
  - 30日間保持
- **アプリケーションデータ**:
  - アップロードファイルの日次バックアップ
  - オブジェクトストレージへの同期

### 2. 災害復旧計画
- **RTO（目標復旧時間）**: 4時間
- **RPO（目標復旧時点）**: 1時間
- **復旧手順**:
  1. 代替リージョンでインフラ起動
  2. 最新バックアップからデータ復元
  3. DNSフェイルオーバー
  4. サービス正常性確認

## スケーリング戦略

### 1. 水平スケーリング
```yaml
# Kubernetes HPA設定
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. データベーススケーリング
- **読み取り負荷分散**: レプリカへの自動振り分け
- **コネクションプーリング**: PgBouncerによる接続管理
- **パーティショニング**: 時系列データの自動パーティション

## 開発環境との差異

### 開発環境
- データ層のみコンテナ化（Podman）
- アプリケーション層はローカル実行
- 簡易認証（開発用トークン）
- ログはコンソール出力

### 本番環境
- 全層コンテナ化（Kubernetes）
- 冗長構成・自動フェイルオーバー
- 本格的な認証（Keycloak）
- 集中ログ管理（ELK Stack）

## デプロイメントパイプライン

### CI/CD設定
```yaml
# GitHub Actions設定
deploy:
  steps:
    - name: Build Frontend
      run: |
        cd frontend
        npm ci
        npm run build
    
    - name: Build Backend
      run: |
        cd backend
        docker build -t backend:${{ github.sha }} .
    
    - name: Run Tests
      run: |
        make test-full
    
    - name: Deploy to Staging
      if: github.ref == 'refs/heads/develop'
      run: |
        kubectl apply -f k8s/staging/
    
    - name: Deploy to Production
      if: github.ref == 'refs/heads/main'
      run: |
        kubectl apply -f k8s/production/
```

## コスト最適化

### 1. リソース最適化
- **オートスケーリング**: 負荷に応じた自動調整
- **スポットインスタンス**: 開発・テスト環境での活用
- **予約インスタンス**: 本番環境の基本容量

### 2. ストレージ最適化
- **ライフサイクルポリシー**: 古いバックアップの自動削除
- **データ圧縮**: ログファイルの圧縮保存
- **階層化ストレージ**: アクセス頻度に応じた配置

## 運用手順

### 1. デプロイメント
```bash
# 本番環境へのデプロイ
./deploy.sh production

# ローリングアップデート
kubectl set image deployment/backend backend=backend:v2.0.0

# ロールバック
kubectl rollout undo deployment/backend
```

### 2. メンテナンス
```bash
# データベースメンテナンス
pg_dump -h localhost -U postgres itdo_erp > backup.sql
VACUUM ANALYZE;

# キャッシュクリア
redis-cli FLUSHALL

# ログローテーション
logrotate /etc/logrotate.d/project-management
```

### 3. トラブルシューティング
```bash
# ヘルスチェック
curl http://localhost:8000/health

# ログ確認
kubectl logs -f deployment/backend

# メトリクス確認
curl http://localhost:9090/metrics
```

## 環境変数設定

### 必須環境変数
```bash
# データベース接続
DATABASE_URL=postgresql://user:password@postgres:5432/itdo_erp
REDIS_URL=redis://redis:6379/0

# 認証設定
KEYCLOAK_URL=https://auth.itdo-erp.jp
KEYCLOAK_REALM=itdo
KEYCLOAK_CLIENT_ID=project-management

# セキュリティ
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# 監視
SENTRY_DSN=https://xxx@sentry.io/yyy
PROMETHEUS_ENABLED=true

# 機能フラグ
FEATURE_GANTT_CHART=true
FEATURE_RESOURCE_MANAGEMENT=true
FEATURE_RECURRING_PROJECTS=true
```

## まとめ
このインフラストラクチャ構成により、高可用性、スケーラビリティ、セキュリティを確保したプロジェクト管理システムの運用が可能となります。開発環境との適切な分離を保ちながら、本番環境では冗長性とパフォーマンスを重視した設計となっています。