# 🔄 Blue-Green Deployment Quick Start Guide

## CC03 v64.0 - 即効性重視のインフラ改善

### 🎯 概要
Blue-Greenデプロイメントシステムにより、ゼロダウンタイムでの本番環境更新を実現します。

### 🚀 使用方法

#### 1. 初期化
```bash
cd /home/work/ITDO_ERP2/infra
./deploy-prod.sh blue-green init
```

#### 2. Blue-Green デプロイ実行
```bash
# 既存のdeploy-prod.shから直接実行
./deploy-prod.sh blue-green deploy

# または直接実行
./deploy-blue-green-v64.sh deploy
```

#### 3. ステータス確認
```bash
./deploy-prod.sh blue-green status
```

#### 4. ロールバック（必要時）
```bash
./deploy-prod.sh blue-green rollback
```

### 🏗️ システム構成

#### 環境分離
- **Blue環境**: ポート 3001(Frontend), 8001(Backend), 8080(NGINX)
- **Green環境**: ポート 3002(Frontend), 8002(Backend), 9080(NGINX)
- **本番トラフィック**: ポート 80/443 (動的ルーティング)

#### 自動機能
- ✅ ヘルスチェック自動実行
- ✅ トラフィック自動切り替え
- ✅ 失敗時自動ロールバック
- ✅ 設定バックアップ自動作成

### 📊 利用可能コマンド

| コマンド | 説明 | 例 |
|----------|------|-----|
| `deploy` | 新バージョンをゼロダウンタイムデプロイ | `./deploy-prod.sh blue-green deploy` |
| `status` | 現在のデプロイ状況確認 | `./deploy-prod.sh blue-green status` |
| `rollback` | 前バージョンに即座ロールバック | `./deploy-prod.sh blue-green rollback` |
| `switch` | 手動環境切り替え | `./deploy-prod.sh blue-green switch green` |
| `health` | 環境ヘルスチェック | `./deploy-prod.sh blue-green health blue` |
| `cleanup` | 非アクティブ環境削除 | `./deploy-prod.sh blue-green cleanup` |

### 🔍 ヘルスチェックURL

#### Blue環境
- Frontend: http://localhost:3001
- Backend: http://localhost:8001/api/v1/health
- NGINX: http://localhost:8080/health

#### Green環境  
- Frontend: http://localhost:3002
- Backend: http://localhost:8002/api/v1/health
- NGINX: http://localhost:9080/health

#### 本番環境
- メインサイト: http://localhost
- デプロイ状況: http://localhost/deployment-status

### 🛡️ セーフガード機能

1. **ヘルスチェック**: 新環境の完全稼働確認後にトラフィック切り替え
2. **自動バックアップ**: デプロイ前に現在の設定を自動保存
3. **即座ロールバック**: 問題検出時に1コマンドで前バージョンに復帰
4. **段階的デプロイ**: データベースは共有、アプリケーション層のみ更新

### 🎉 メリット

- **ゼロダウンタイム**: ユーザーに影響を与えずに更新
- **即座復旧**: 問題発生時に1分以内でロールバック
- **安全性**: 新バージョンの動作確認後にトラフィック切り替え
- **運用継続**: 旧バージョンを維持したままテスト可能

### 🔧 トラブルシューティング

#### デプロイ失敗時
```bash
# ロールバック実行
./deploy-prod.sh blue-green rollback

# 個別環境ヘルスチェック
./deploy-prod.sh blue-green health blue
./deploy-prod.sh blue-green health green
```

#### 手動切り替え
```bash
# Blue環境に切り替え
./deploy-prod.sh blue-green switch blue

# Green環境に切り替え  
./deploy-prod.sh blue-green switch green
```

---

**🚀 CC03 v64.0 Blue-Green Deployment System Ready!**

*即効性重視のインフラ改善により、本番環境での安全なゼロダウンタイムデプロイを実現*