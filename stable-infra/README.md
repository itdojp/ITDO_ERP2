# ITDO ERP v2 - 45日間安定インフラ

**CC03 v61.0 - シンプル設計重視**

## 🎯 プロジェクト概要

45日間の安定稼働を目指すシンプルなインフラ構成です。複雑さを排除し、手動運用を重視した設計になっています。

### プロジェクト期間
- **開始**: 2025-07-25
- **終了**: 2025-09-08
- **期間**: 45日間

### 制約事項
- ✅ 自動システム完全禁止
- ✅ 手動コミットのみ（1日最大3個）
- ✅ シンプル設計重視

## 🏗️ アーキテクチャ

### サービス構成（6サービス）
```
NGINX (SSL終端) → Frontend (React) → Backend (FastAPI)
                                   ↓
                  PostgreSQL ← → Redis ← Monitor (Prometheus)
```

### ネットワーク設計
- **web-network**: NGINX ↔ Frontend
- **app-network**: Backend ↔ Monitor (内部通信)
- **db-network**: Database ↔ Cache (内部通信)

## 🚀 クイックスタート

### 1. デプロイ実行
```bash
cd stable-infra
./deploy.sh deploy
```

### 2. サービス確認
```bash
./deploy.sh status
```

### 3. 監視実行
```bash
./monitor.sh all
```

## 📁 ファイル構成

```
stable-infra/
├── docker-compose.yml      # メインサービス定義
├── .env                    # 環境設定
├── nginx.conf              # NGINX設定
├── prometheus.yml          # 監視設定
├── deploy.sh               # デプロイスクリプト
├── backup.sh               # バックアップスクリプト
├── monitor.sh              # 監視スクリプト
├── ssl/                    # SSL証明書（自動生成）
└── README.md               # このファイル
```

## 🔧 運用手順

### デプロイ操作
```bash
./deploy.sh deploy    # フルデプロイ
./deploy.sh status    # 状態確認
./deploy.sh logs      # ログ表示
./deploy.sh stop      # サービス停止
```

### バックアップ操作
```bash
./backup.sh backup    # フルバックアップ実行
./backup.sh list      # バックアップ一覧
./backup.sh restore   # リストア実行
./backup.sh cleanup   # 古いファイル削除
```

### 監視操作
```bash
./monitor.sh all           # 全監視項目
./monitor.sh services      # サービス状態のみ
./monitor.sh connectivity  # 接続テストのみ
./monitor.sh watch         # 継続監視モード
```

## 🌐 アクセスURL

- **メインアプリ**: https://itdo-erp.local
- **API**: https://itdo-erp.local/api/v1/
- **監視**: https://monitor.itdo-erp.local:9090
- **ヘルスチェック**: https://itdo-erp.local/health

## 📊 成功指標

### 安定性目標
- **稼働率**: 99.9%以上（45日で最大65分ダウンタイム）
- **レスポンス**: API < 500ms
- **エラー率**: < 0.1%

### シンプルさ目標
- **設定ファイル**: 8個
- **サービス数**: 6個
- **手動手順**: 1ページ以内

## 🛠️ トラブルシューティング

### サービス起動しない
```bash
# 状態確認
./deploy.sh status

# ログ確認
./deploy.sh logs <サービス名>

# 再デプロイ
./deploy.sh deploy
```

### 接続エラー
```bash
# 接続テスト
./monitor.sh connectivity

# NGINX設定確認
docker compose exec nginx nginx -t

# SSL証明書確認
ls -la ssl/
```

### パフォーマンス問題
```bash
# リソース使用量確認
./monitor.sh resources

# レスポンス時間測定
./monitor.sh performance

# データベース接続数確認
docker compose exec postgres psql -U itdo_user -d itdo_erp_stable -c "SELECT count(*) FROM pg_stat_activity;"
```

## 📈 日次運用チェックリスト

### 毎日実行すること
- [ ] `./monitor.sh all` でシステム状態確認
- [ ] `./deploy.sh status` でサービス状態確認
- [ ] エラーログ確認（必要に応じて）

### 週次実行すること
- [ ] `./backup.sh backup` でバックアップ実行
- [ ] `./backup.sh cleanup` で古いファイル削除
- [ ] システム更新の検討

### 改善コミット（1日最大3個）
毎日最大3つの改善を段階的に実装し、45日間で安定性を向上させます。

## 🔒 セキュリティ

### 基本セキュリティ
- SSL/TLS暗号化（開発用自己署名証明書）
- 内部ネットワーク分離
- 基本的なセキュリティヘッダー

### パスワード管理
- 初期パスワードは`.env`で管理
- 本番環境では強力なパスワードに変更必須

## 📞 サポート

### 制限事項
- 自動システム使用禁止
- 1日最大3コミット
- 手動運用のみ

### 緊急時対応
1. `./monitor.sh all` で状況確認
2. `./deploy.sh logs` でエラー特定
3. 必要に応じて `./deploy.sh deploy` で再デプロイ

---

**シンプル・イズ・ベスト**  
*45日間の安定稼働を目指して*