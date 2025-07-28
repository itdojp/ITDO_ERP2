# 認証・認可システム デプロイメント構成書

## 1. 概要

本文書は、認証・認可システムのデプロイメント構成と環境設定を定義します。

## 2. システム構成図

```mermaid
graph TB
    subgraph "クライアント層"
        Browser[Webブラウザ]
        Mobile[モバイルアプリ]
    end
    
    subgraph "アプリケーション層"
        Nginx[Nginx<br>リバースプロキシ]
        Backend[FastAPI<br>認証API]
        Frontend[React<br>フロントエンド]
    end
    
    subgraph "認証基盤"
        Keycloak[Keycloak<br>認証サーバー]
    end
    
    subgraph "データ層"
        PostgreSQL[(PostgreSQL<br>ユーザーDB)]
        Redis[(Redis<br>セッション)]
    end
    
    Browser --> Nginx
    Mobile --> Nginx
    Nginx --> Frontend
    Nginx --> Backend
    Backend --> Keycloak
    Backend --> PostgreSQL
    Backend --> Redis
    Keycloak --> PostgreSQL
```

## 3. コンテナ構成

### 3.1 Docker Compose設定

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: itdo_erp
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - itdo_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - itdo_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Keycloak
  keycloak:
    image: quay.io/keycloak/keycloak:23.0
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: ${KC_DB_USER}
      KC_DB_PASSWORD: ${KC_DB_PASSWORD}
      KEYCLOAK_ADMIN: ${KC_ADMIN_USER}
      KEYCLOAK_ADMIN_PASSWORD: ${KC_ADMIN_PASSWORD}
      KC_PROXY: edge
      KC_HOSTNAME_STRICT: false
    command: start --optimized
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - itdo_network

  # Backend API (開発環境)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/itdo_erp
      REDIS_URL: redis://:{REDIS_PASSWORD}@redis:6379/0
      KEYCLOAK_URL: http://keycloak:8080
      KEYCLOAK_REALM: ${KC_REALM}
      SECRET_KEY: ${SECRET_KEY}
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - itdo_network

  # Frontend (開発環境)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    environment:
      VITE_API_URL: http://localhost:8000/api/v1
      VITE_KEYCLOAK_URL: http://localhost:8080
      VITE_KEYCLOAK_REALM: ${KC_REALM}
      VITE_KEYCLOAK_CLIENT_ID: ${KC_CLIENT_ID}
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    networks:
      - itdo_network

volumes:
  postgres_data:
  redis_data:

networks:
  itdo_network:
    driver: bridge
```

## 4. 環境変数設定

### 4.1 環境変数一覧

```bash
# .env.example

# Database
DB_USER=itdo_user
DB_PASSWORD=secure_password_here
DB_HOST=postgres
DB_PORT=5432
DB_NAME=itdo_erp

# Redis
REDIS_PASSWORD=redis_secure_password
REDIS_HOST=redis
REDIS_PORT=6379

# Keycloak
KC_ADMIN_USER=admin
KC_ADMIN_PASSWORD=admin_secure_password
KC_DB_USER=keycloak
KC_DB_PASSWORD=keycloak_secure_password
KC_REALM=itdo-erp
KC_CLIENT_ID=itdo-erp-client
KC_CLIENT_SECRET=client_secret_here

# Application
SECRET_KEY=your-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480  # 8時間
REFRESH_TOKEN_EXPIRE_DAYS=7
IDLE_TIMEOUT_MINUTES=30

# Security
BCRYPT_ROUNDS=12
PASSWORD_MIN_LENGTH=8
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCK_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://app.itdo-erp.jp"]

# Email (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@itdo.jp
SMTP_PASSWORD=smtp_password_here
SMTP_FROM=ITDO ERP System <noreply@itdo.jp>

# MFA
TOTP_VALIDITY_WINDOW=1  # 前後1つのウィンドウを許容（計90秒）
BACKUP_CODE_COUNT=10

# Session
MAX_SESSIONS_PER_USER=3
SESSION_CLEANUP_INTERVAL_HOURS=1

# Audit
LOGIN_HISTORY_RETENTION_DAYS=365  # 1年間保持

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/yyy
LOG_LEVEL=INFO
```

### 4.2 環境別設定

| 設定項目 | 開発環境 | ステージング環境 | 本番環境 |
|---------|---------|----------------|---------|
| DEBUG | true | true | false |
| LOG_LEVEL | DEBUG | INFO | WARNING |
| CORS_ORIGINS | ["*"] | 特定ドメイン | 特定ドメイン |
| HTTPS | 不要 | 必須 | 必須 |
| セッション有効期限 | 24時間 | 8時間 | 8時間 |

## 5. Keycloak設定

### 5.1 レルム設定

```json
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
  "waitIncrementSeconds": 300,
  "quickLoginCheckMilliSeconds": 1000,
  "maxDeltaTimeSeconds": 43200,
  "failureFactor": 5
}
```

### 5.2 クライアント設定

```json
{
  "clientId": "itdo-erp-client",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "redirectUris": [
    "http://localhost:3000/*",
    "https://app.itdo-erp.jp/*"
  ],
  "webOrigins": ["+"],
  "protocol": "openid-connect",
  "standardFlowEnabled": true,
  "implicitFlowEnabled": false,
  "directAccessGrantsEnabled": true,
  "serviceAccountsEnabled": false,
  "publicClient": false,
  "frontchannelLogout": true,
  "attributes": {
    "saml.assertion.signature": "false",
    "saml.multivalued.roles": "false",
    "saml.force.post.binding": "false",
    "saml.encrypt": "false",
    "post.logout.redirect.uris": "+",
    "oauth2.device.authorization.grant.enabled": "false",
    "oidc.ciba.grant.enabled": "false",
    "backchannel.logout.session.required": "true",
    "backchannel.logout.revoke.offline.tokens": "false"
  }
}
```

### 5.3 Google Identity Provider設定

```json
{
  "alias": "google",
  "providerId": "google",
  "enabled": true,
  "updateProfileFirstLoginMode": "on",
  "trustEmail": true,
  "storeToken": false,
  "addReadTokenRoleOnCreate": false,
  "config": {
    "clientId": "${GOOGLE_CLIENT_ID}",
    "clientSecret": "${GOOGLE_CLIENT_SECRET}",
    "defaultScope": "openid email profile",
    "hostedDomain": "itdo.jp"
  }
}
```

## 6. ネットワーク設定

### 6.1 ポート一覧

| サービス | 内部ポート | 外部ポート | 説明 |
|---------|-----------|-----------|------|
| Nginx | 80, 443 | 80, 443 | HTTPSリダイレクト含む |
| Backend | 8000 | - | 内部通信のみ |
| Frontend | 3000 | - | 開発時のみ外部公開 |
| PostgreSQL | 5432 | - | 内部通信のみ |
| Redis | 6379 | - | 内部通信のみ |
| Keycloak | 8080 | 8080 | 管理画面アクセス用 |

### 6.2 ファイアウォール設定

```bash
# 本番環境のファイアウォール設定例
# HTTPとHTTPSのみ許可
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH

# 内部通信用（Dockerネットワーク）
sudo ufw allow from 172.16.0.0/12 to any port 5432  # PostgreSQL
sudo ufw allow from 172.16.0.0/12 to any port 6379  # Redis
sudo ufw allow from 172.16.0.0/12 to any port 8080  # Keycloak
```

## 7. バックアップ設定

### 7.1 データベースバックアップ

```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/backup/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="itdo_erp"

# PostgreSQLバックアップ
docker exec postgres pg_dump -U ${DB_USER} ${DB_NAME} | gzip > ${BACKUP_DIR}/itdo_erp_${TIMESTAMP}.sql.gz

# 7日以上前のバックアップを削除
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +7 -delete
```

### 7.2 バックアップスケジュール

```cron
# crontab -e
# 毎日午前2時にバックアップ実行
0 2 * * * /opt/itdo-erp/scripts/backup-db.sh >> /var/log/itdo-backup.log 2>&1

# 毎週日曜日にフルバックアップ
0 3 * * 0 /opt/itdo-erp/scripts/backup-full.sh >> /var/log/itdo-backup.log 2>&1
```

## 8. 監視設定

### 8.1 ヘルスチェックエンドポイント

- Backend: `GET /health`
- Keycloak: `GET /health/ready`
- Frontend: `GET /`

### 8.2 監視項目

| 項目 | 閾値 | アラート条件 |
|------|------|-------------|
| CPU使用率 | 80% | 5分間継続 |
| メモリ使用率 | 90% | 即時 |
| ディスク使用率 | 85% | 即時 |
| レスポンスタイム | 3秒 | 10回連続 |
| エラー率 | 5% | 5分間 |
| ログイン失敗率 | 20% | 10分間 |

## 9. デプロイメント手順

### 9.1 初回デプロイ

```bash
# 1. リポジトリクローン
git clone https://github.com/itdojp/ITDO_ERP2.git
cd ITDO_ERP2

# 2. 環境変数設定
cp .env.example .env
# .envファイルを編集

# 3. Dockerイメージビルド
docker compose build

# 4. データベース初期化
docker compose up -d postgres
docker compose run backend alembic upgrade head

# 5. Keycloak初期設定
docker compose up -d keycloak
# 管理画面でレルム・クライアント設定

# 6. 全サービス起動
docker compose up -d
```

### 9.2 更新デプロイ

```bash
# 1. 最新コード取得
git pull origin main

# 2. Dockerイメージ更新
docker compose build

# 3. データベースマイグレーション
docker compose run backend alembic upgrade head

# 4. サービス再起動（ダウンタイムなし）
docker compose up -d --no-deps --scale backend=2 backend
# ヘルスチェック確認後
docker compose up -d --no-deps backend

# 5. フロントエンド更新
docker compose up -d --no-deps frontend
```

## 10. トラブルシューティング

### 10.1 よくある問題と対処法

| 問題 | 症状 | 対処法 |
|------|------|--------|
| DB接続エラー | "could not connect to server" | PostgreSQLの起動確認、接続情報確認 |
| Redis接続エラー | "Connection refused" | Redisの起動確認、パスワード確認 |
| Keycloak連携エラー | "Invalid token" | レルム設定確認、クライアントシークレット確認 |
| CORS エラー | "blocked by CORS policy" | CORS_ORIGINS環境変数確認 |

### 10.2 ログ確認

```bash
# 各サービスのログ確認
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f keycloak

# 特定時間のログ抽出
docker compose logs --since "2025-07-28T10:00:00" backend
```

## 11. セキュリティチェックリスト

- [ ] すべての環境変数が適切に設定されている
- [ ] デフォルトパスワードが変更されている
- [ ] HTTPSが有効化されている（本番環境）
- [ ] ファイアウォールが適切に設定されている
- [ ] バックアップが定期的に実行されている
- [ ] ログローテーションが設定されている
- [ ] 監視アラートが設定されている
- [ ] セキュリティアップデートが適用されている