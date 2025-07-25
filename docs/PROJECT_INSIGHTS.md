# ITDO ERP2 プロジェクト知見レポート

## 📋 概要

このドキュメントは、ITDO ERP2プロジェクトの開発過程で得られた技術的知見とプロジェクト管理の学習内容をまとめたものです。

**期間:** 2025年7月10日のセッション  
**対象:** 3つのClaude Code エージェントによる並行開発作業  
**PR対象:** #98 (Task-Department Integration), #97 (Role Service), #95 (E2E Tests)

---

## 🔧 プロジェクト技術的知見

### 1. SQLAlchemy 2.0 関連の問題パターン

#### 問題: Foreign Key Reference Error
**エラー例:**
```
Foreign key associated with column 'audit_logs.organization_id' could not find table 'organizations'
```

**原因:**
- テスト環境で`tests/conftest.py`にモデルのインポートが不足
- SQLAlchemyがモデル定義を見つけられない状態

**解決策:**
```python
# tests/conftest.py に追加が必要
from app.models import AuditLog, Department, Organization, Permission, Role, User
```

**学習ポイント:** SQLAlchemy 2.0では、テスト環境でのモデル登録が従来より厳密になっている

### 2. テストデータの一意性問題

#### 問題: Organization Code Duplicate Error
**エラー例:**
```
test_create_endpoint_success expected 201 but got 409 (conflict)
```

**原因:**
- FactoryBoyでの組織コード生成が重複
- `fake.bothify(text="ORG-####-???")`が同じ値を生成

**解決策:**
```python
# tests/factories/organization.py
"code": fake.unique.bothify(text="ORG-####-???")  # unique を追加
```

**学習ポイント:** テストファクトリーでは一意性を明示的に指定する必要がある

### 3. CORS設定の環境依存問題

#### 問題: CORS Configuration Parse Error
**エラー例:**
```
pydantic_settings.exceptions.SettingsError: error parsing value for field "BACKEND_CORS_ORIGINS"
```

**原因:**
- E2E環境とローカル環境でCORS設定形式が異なる
- 文字列形式（カンマ区切り）とJSON形式の混在

**解決策:**
```python
@field_validator("BACKEND_CORS_ORIGINS", mode="before")
@classmethod
def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
    # カンマ区切り文字列を先に処理（JSON処理前）
    if "," in v_stripped and not v_stripped.startswith("["):
        origins = [origin.strip() for origin in v_stripped.split(",") if origin.strip()]
        return origins if origins else default_origins
```

**学習ポイント:** 設定値の検証は、複数の入力形式を想定して順序を考慮する

### 4. Ruff Linting の繰り返し問題

#### 問題: Ruff Violations が繰り返し発生
**主な違反:** E501 (line too long), N805 (first argument of a method should be named 'self'), N818 (exception name should be suffixed with 'Error')

**解決策:**
```bash
# 修正コマンドの標準化
uv run ruff check . --fix
uv run ruff format .
```

**学習ポイント:** Ruffの自動修正は段階的に実行し、毎回確認が必要

### 5. Multi-tenant アーキテクチャパターン

#### 設計原則
- Organization-level データ分離
- Department階層による権限管理
- Task-Department関連付けによる可視性制御

#### 実装パターン
```python
# 階層化されたデータアクセス
class Task(SoftDeletableModel):
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    department_id: Mapped[DepartmentId | None] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
```

**学習ポイント:** マルチテナント設計では、すべてのエンティティにorganization_idが必要

---

## 📋 プロジェクト管理・指示出し方法の知見

### 1. Claude Code エージェント管理パターン

#### 効果的なワークフロー
1. **状況確認** → **問題特定** → **具体的指示** → **完了確認**のサイクル
2. 並行作業での衝突を避けるため、各エージェントに異なるPRを割り当て
3. 定期的な進捗確認と優先度調整

#### 指示の構造化
```markdown
### 🎯 優先度: [高/中/低] - [問題の要約]
**問題:** [具体的な問題の説明]
**修正手順:**
1. [具体的なコマンド]
2. [期待される結果]
3. [次のステップ]
**期待される結果:** [明確な完了条件]
```

### 2. 視覚的セパレーターの重要性

#### 効果的だったパターン
```markdown
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
## 📋 Claude Code 1への指示 (PR #98)
### 🎯 目標: [明確な目標]
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
```

**学習ポイント:** 視覚的な区切りは、複数のエージェントが同時に作業する際の混乱を防ぐ

### 3. 段階的優先度設定

#### 効果的だった優先度付け
1. **最優先:** Code Quality (Ruff linting) - 5分で完了可能
2. **次:** Backend Test - 10-15分で完了可能  
3. **最後:** 複雑な機能実装 - 時間がかかる

#### 理由
- 短時間で完了できるタスクから処理することで、成功体験を積み重ねる
- CI/CDパイプラインの基本チェックを先に通すことで、後の作業が安定する

### 4. コミュニケーションパターンの最適化

#### 効果的だったパターン
- **ユーザー:** 「X に指示済です。Y が完了したので内容を確認して、次の指示を作成してください。」
- **アシスタント:** 状況確認 → 問題特定 → 具体的指示作成

#### 無駄だったパターン
- 過度に詳細な説明
- 完了していないタスクの詳細分析
- 同時に複数の複雑な指示

### 5. 切りの良い完了基準の設定

#### 効果的だった基準設定
```markdown
### 🎯 切りの良い完了基準
1. Code 1: 完全成功（全CI緑色）→ Phase 3基盤完成
2. Code 2: Core Foundation + Backend Test 成功 → Role Service基盤安定  
3. Code 3: Code Quality + Backend Test 成功 → E2E基盤最低限確保
```

**学習ポイント:** 各エージェントに異なる完了レベルを設定することで、全体の作業効率が向上

### 6. 問題発見・解決のパターン

#### 効果的だった診断手順
1. **PR Status Check:** `gh pr view [PR番号] --json statusCheckRollup`
2. **失敗の特定:** 最も重要なチェックから順に確認
3. **根本原因の調査:** ログの詳細確認
4. **段階的修正:** 簡単な問題から順番に解決

#### 学習した問題解決順序
1. **Ruff Linting** (5分) → **SQLAlchemy Models** (15分) → **Complex Logic** (30分+)

---

## 🎯 今後の改善提案

### 技術面
1. **テンプレート化:** 共通のSQLAlchemyエラーパターンをテンプレート化
2. **CI/CD最適化:** Ruff checkを最初のステップにして、早期にフィードバック
3. **テスト安定化:** FactoryBoyの一意性制約をデフォルト設定に

### プロジェクト管理面
1. **指示テンプレート:** 効果的だった指示形式をテンプレート化
2. **進捗可視化:** 各PRの状況を一目で把握できるダッシュボード
3. **優先度マトリックス:** 時間対効果を考慮した優先度設定ルール

---

## 📊 セッション統計

- **管理したPR数:** 3個
- **解決した主要問題:** 5カテゴリ（SQLAlchemy、CORS、Ruff、テストデータ、マルチテナント）
- **指示回数:** 約20回の指示サイクル
- **効果的だった指示パターン:** 段階的優先度設定 + 視覚的セパレーター

---

*このドキュメントは今後の類似プロジェクトで参照し、継続的に改善していく予定です。*