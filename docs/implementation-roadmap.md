# 型安全性を重視した実装ロードマップ

## 実装し直しが必要な箇所

### 1. 即座に再実装が必要（既存スタブの置き換え）
- `backend/app/models/organization.py` - 16行 → 完全実装
- `backend/app/models/department.py` - 17行 → 完全実装  
- `backend/app/models/role.py` - 52行 → 完全実装

### 2. 既存実装の改修が必要
- `backend/app/models/user.py` - 新ベースクラスへの移行
- `backend/app/services/user.py` - リポジトリパターンへの移行
- `backend/app/api/v1/users.py` - 新APIベースクラスの活用

### 3. 完全新規実装が必要
- リポジトリレイヤー全体
- ビジネスエンティティ（Customer, Supplier, Product等）
- ERP業務機能すべて

## 各フェーズでの実装準備完了ポイント

### フェーズ1: 基盤整備（1-2週間）

**週1完了時点で実装可能**:
- ✅ 型定義フレームワーク (`app/types/__init__.py`)
- ✅ ベースリポジトリ (`app/repositories/base.py`)
- ✅ CI/CD型チェック強化

**週2完了時点で実装可能**:
- Organization, Department, Roleの再実装開始
- 既存Userサービスのリファクタリング開始

### フェーズ2: データレイヤー再構築（2-3週間）

**週1完了時点で実装可能**:
- ✅ 新ベースモデル (`app/models/base.py`)
- Organization, Department, Role モデルの完全実装
- Userモデルの新ベースクラスへの移行

**週2完了時点で実装可能**:
- Customer, Supplier, Product モデルの実装
- 各モデルに対応するリポジトリの実装

**週3完了時点で実装可能**:
- Inventory, Sales, Purchase モデルの実装
- トランザクション管理の実装

### フェーズ3: APIレイヤー再構築（2-3週間）

**週1完了時点で実装可能**:
- ✅ ベースAPIルーター (`app/api/base.py`)
- ✅ 共通スキーマ (`app/schemas/common.py`)
- Organization, Department, Role APIの実装

**週2完了時点で実装可能**:
- Customer, Supplier, Product APIの実装
- 既存User APIの新ベースクラスへの移行

**週3完了時点で実装可能**:
- Sales, Purchase, Inventory APIの実装
- API統合テストの実装

### フェーズ4: テストフレームワーク再構築（1-2週間）

**3日完了時点で実装可能**:
- 型安全なテストフィクスチャ
- テストファクトリーの実装

**週1完了時点で実装可能**:
- 全モデルの単体テスト
- 全APIの統合テスト

**週2完了時点で実装可能**:
- E2Eテストの実装
- パフォーマンステストの実装

### フェーズ5: 統合・最適化（1-2週間）

**週1完了時点で実装可能**:
- キャッシュレイヤーの実装
- バックグラウンドタスクの実装

**週2完了時点で実装可能**:
- 監視・ロギングの強化
- 本番環境へのデプロイ準備

## 実装の優先順位

1. **最優先**: Organization, Department, Role（基本的な組織構造）
2. **高優先**: Customer, Supplier, Product（マスターデータ）
3. **中優先**: Sales, Purchase, Inventory（トランザクション）
4. **低優先**: Production, HR, Analytics（高度な機能）

## 成功の指標

- mypyエラー: 0件（厳格モード）
- テストカバレッジ: >95%
- API応答時間: <100ms（95パーセンタイル）
- 型安全性: 100%（anyの使用禁止）