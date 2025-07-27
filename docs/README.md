# Documentation Structure

このディレクトリにはITDO ERP v2システムの各種ドキュメントが格納されています。

## 📁 ディレクトリ構造

### 主要ドキュメント

- **design/** - システム設計書
  - システム概要、要件定義、アーキテクチャ設計
  - データベース設計、API設計、セキュリティ設計
  - UI/UXデザインシステム

- **technical/** - 技術ドキュメント
  - 実装ガイド、フェーズ別実装計画
  - データベース詳細設計

- **api/** - API仕様書
  - OpenAPI/Swagger仕様
  - 認証API仕様

- **infrastructure/** - インフラストラクチャ設計
  - CI/CDパイプライン設計
  - Kubernetes、Docker設計
  - 監視・ロギング設計

- **testing/** - テスト関連ドキュメント
  - E2Eテストガイド
  - テスト戦略、トラブルシューティング

- **workflow/** - 開発ワークフロー
  - マージワークフロー、ベストプラクティス

- **maintenance/** - メンテナンス関連
  - ブランチ管理計画

### アーカイブ

- **archive/** - 過去のドキュメントと作業ログ
  - agent-work-logs/ - エージェント作業ログ
  - coordination-history/ - 調整・連携履歴
  - temporary-work/ - 一時作業文書
  - その他の過去バージョン文書

## 📋 主要ドキュメント一覧

### 開発ガイド
- [PROJECT_STANDARDS.md](PROJECT_STANDARDS.md) - プロジェクト標準
- [CLAUDE_CODE_OPTIMIZATION_GUIDE.md](CLAUDE_CODE_OPTIMIZATION_GUIDE.md) - Claude Code最適化ガイド
- [CODE_QUALITY_ENFORCEMENT_GUIDE.md](CODE_QUALITY_ENFORCEMENT_GUIDE.md) - コード品質管理ガイド

### システム設計
- [ARCHITECTURE.md](ARCHITECTURE.md) - システムアーキテクチャ
- [design/README.md](design/README.md) - 設計書一覧

### 運用・保守
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - トラブルシューティングガイド
- [maintenance/BRANCH_CLEANUP_PLAN.md](maintenance/BRANCH_CLEANUP_PLAN.md) - ブランチ管理計画

## 🔍 ドキュメント検索のヒント

特定のトピックを探している場合：

1. **開発を始める** → development-environment-setup.md
2. **API仕様を確認** → api/ディレクトリ
3. **テスト方法** → testing/ディレクトリ
4. **インフラ設定** → infrastructure/ディレクトリ
5. **過去の作業履歴** → archive/ディレクトリ