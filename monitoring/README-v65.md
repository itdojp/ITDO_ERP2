# 📊 CC03 v65.0 - 統合監視ダッシュボードシステム

## 🎯 概要

CC03 v65.0で実装された包括的なPrometheus + Grafana統合監視システムです。リアルタイム監視、インテリジェントアラート、業務メトリクス可視化を提供します。

## 🚀 クイックスタート

### 1. 監視システム起動
```bash
cd /home/work/ITDO_ERP2/monitoring
./deploy-monitoring-v65.sh deploy
```

### 2. 監視ダッシュボードアクセス
- **Grafana**: http://localhost:3001
  - ユーザー: `admin`
  - パスワード: `GrafanaAdmin2025!Monitor#v65`
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

## 🏗️ システム構成

### 監視対象サービス
- ✅ **システムメトリクス** (CPU, Memory, Disk, Network)
- ✅ **コンテナメトリクス** (Docker/Podman監視)
- ✅ **PostgreSQL** (データベース監視)
- ✅ **Redis** (キャッシュ監視)
- ✅ **NGINX** (Webサーバー監視)
- ✅ **Backend API** (アプリケーション監視)
- ✅ **Keycloak** (認証サービス監視)
- ✅ **SSL証明書監視**
- ✅ **外部サービス監視**
- ✅ **Blue-Green環境監視**

### 監視コンポーネント
| サービス | ポート | 説明 |
|----------|--------|------|
| **Prometheus** | 9090 | メトリクス収集・保存 |
| **Grafana** | 3001 | ダッシュボード・可視化 |
| **Alertmanager** | 9093 | アラート管理 |
| **Node Exporter** | 9100 | システムメトリクス |
| **cAdvisor** | 8080 | コンテナメトリクス |
| **Postgres Exporter** | 9187 | PostgreSQLメトリクス |
| **Redis Exporter** | 9121 | Redisメトリクス |
| **NGINX Exporter** | 9113 | NGINXメトリクス |
| **Blackbox Exporter** | 9115 | 外部監視 |
| **SSL Exporter** | 9219 | SSL証明書監視 |

## 📊 リアルタイムダッシュボード

### 1. システム全体概要
- **URL**: http://localhost:3001/d/overview
- **更新間隔**: 5秒
- **機能**: システム全体の健全性、リソース使用率、アクティブアラート

### 2. アプリケーションパフォーマンス
- **URL**: http://localhost:3001/d/application
- **更新間隔**: 5秒  
- **機能**: API応答時間、エラー率、レスポンス時間分布

### 3. データベース監視
- **URL**: http://localhost:3001/d/database
- **更新間隔**: 10秒
- **機能**: PostgreSQL/Redis監視、接続数、クエリ統計

## 🚨 アラート設定

### アラート重要度レベル
- **Critical**: 即座対応が必要 (5分間隔通知)
- **Warning**: 監視が必要 (30分間隔通知)
- **Info**: 情報通知 (1時間間隔通知)

### 通知先設定
```yaml
# alertmanager-v65.yml
receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'admin@itdo-erp.com'
    slack_configs:
      - channel: '#alerts-critical'
```

### 主要アラートルール
| アラート名 | 条件 | 重要度 |
|-----------|------|--------|
| **HighCPUUsage** | CPU > 80% (2分間) | Warning |
| **CriticalCPUUsage** | CPU > 95% (1分間) | Critical |
| **HighMemoryUsage** | Memory > 85% (3分間) | Warning |
| **ServiceDown** | サービス停止 (30秒) | Critical |
| **HighAPIErrorRate** | APIエラー率 > 5% (2分間) | Critical |
| **DiskSpaceCritical** | ディスク > 90% (2分間) | Critical |

## 🔧 管理コマンド

### 基本操作
```bash
# ステータス確認
./deploy-monitoring-v65.sh status

# ログ確認
./deploy-monitoring-v65.sh logs [service]

# サービス再起動
./deploy-monitoring-v65.sh restart [service]

# 監視システム停止
./deploy-monitoring-v65.sh stop

# 完全削除 (データ含む)
./deploy-monitoring-v65.sh cleanup
```

### 個別サービス管理
```bash
# 個別ログ確認
./deploy-monitoring-v65.sh logs prometheus
./deploy-monitoring-v65.sh logs grafana
./deploy-monitoring-v65.sh logs alertmanager

# 個別サービス再起動
./deploy-monitoring-v65.sh restart prometheus
./deploy-monitoring-v65.sh restart grafana
```

## 📈 カスタムメトリクス

### アプリケーションメトリクス追加
```python
# Backend APIにメトリクス追加例
from prometheus_client import Counter, Histogram, generate_latest

# カスタムメトリクス定義
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### ビジネスメトリクス例
```python
# ビジネスKPI監視
TRANSACTION_COUNT = Counter('business_transactions_total', 'Total business transactions')
TRANSACTION_AMOUNT = Histogram('business_transaction_amount', 'Transaction amounts')
USER_LOGINS = Counter('user_logins_total', 'Total user logins')
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. Prometheusがメトリクスを収集できない
```bash
# ターゲット確認
curl http://localhost:9090/api/v1/targets

# ネットワーク確認
docker network ls
docker network inspect itdo-erp-monitoring-v65_monitoring
```

#### 2. Grafanaダッシュボードが表示されない
```bash
# Grafanaログ確認
./deploy-monitoring-v65.sh logs grafana

# データソース確認
curl -u admin:GrafanaAdmin2025!Monitor#v65 \
  http://localhost:3001/api/datasources
```

#### 3. アラートが送信されない
```bash
# Alertmanager設定確認
curl http://localhost:9093/api/v1/status

# アラートルール確認
curl http://localhost:9090/api/v1/rules
```

### パフォーマンス最適化

#### メトリクス保持期間調整
```yaml
# prometheus-v65.yml
storage:
  tsdb:
    retention.time: 30d    # 30日間保持
    retention.size: 15GB   # 15GB上限
```

#### スクレイプ間隔調整
```yaml
# より頻繁な監視が必要な場合
scrape_configs:
  - job_name: 'critical-service'
    scrape_interval: 5s    # 5秒間隔
```

## 🔐 セキュリティ設定

### 認証・認可設定
```yaml
# Grafana認証設定
environment:
  - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
  - GF_USERS_ALLOW_SIGN_UP=false
  - GF_AUTH_BASIC_ENABLED=true
```

### SSL/TLS設定
```yaml
# Prometheus SSL設定
tls_config:
  cert_file: /etc/ssl/certs/prometheus.crt
  key_file: /etc/ssl/private/prometheus.key
```

## 📚 追加リソース

### 参考ドキュメント
- [Prometheus公式ドキュメント](https://prometheus.io/docs/)
- [Grafana公式ドキュメント](https://grafana.com/docs/)
- [PromQL クエリガイド](https://prometheus.io/docs/prometheus/latest/querying/basics/)

### 学習リソース
- [Prometheus監視設計パターン](https://prometheus.io/docs/practices/)
- [Grafanaダッシュボード設計ベストプラクティス](https://grafana.com/docs/grafana/latest/best-practices/)

---

## 🎉 CC03 v65.0 成果

✅ **即効性実現**: リアルタイム5秒更新監視システム  
✅ **包括的監視**: システム・アプリ・DB・セキュリティ全方位監視  
✅ **インテリジェントアラート**: 重要度別自動通知システム  
✅ **運用効率化**: ワンコマンド監視システム管理  
✅ **スケーラビリティ**: マイクロサービス対応監視基盤  

**🚀 継続的インフラ改善Day 2 - 監視ダッシュボード実装完了!**