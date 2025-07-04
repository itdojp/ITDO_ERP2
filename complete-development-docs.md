# 統合開発ドキュメント - Claude Code & GitHub協調開発

## はじめに

このプロジェクトは**ハイブリッド開発環境**を採用しています。
- データ層（PostgreSQL, Redis, Keycloak）は常にコンテナで実行
- 開発層（FastAPI, React）はローカル/コンテナを選択可能
- 開発速度とセキュリティのバランスを最適化
- Pythonパッケージ管理には**uv**を使用します（pip/activateは使用しません）

## クイックスタート

### データ層の起動（コンテナ）
```bash
# 1. リポジトリクローン（ローカル）
git clone https://github.com/yourorg/yourproject.git
cd yourproject

# 2. 開発環境初期化（ローカル）
./scripts/init-project.sh

# 3. データ層コンテナ起動（ローカル）
podman-compose -f infra/compose-data.yaml up -d
```

### 開発方式の選択

#### オプションA: ローカル開発（推奨・高速）
```bash
# 4. Python環境セットアップ（ローカル）
cd backend
uv venv
uv pip sync requirements-dev.txt

# 5. Node.js環境セットアップ（ローカル）
cd ../frontend
npm install

# 6. 開発サーバー起動（ローカル）
# Terminal 1: Backend
cd backend && uv run uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

#### オプションB: フルコンテナ開発（一貫性重視）
```bash
# 4. 開発コンテナ起動（ローカル）
./scripts/dev-env.sh start

# 5. コンテナに接続（ローカル）
./scripts/dev-env.sh shell

# 6. 開発サーバー起動（コンテナ内）
make dev
```

## 重要な注意事項

### ハイブリッド開発環境の構成
- **データ層（常時コンテナ）**: PostgreSQL, Redis, Keycloak
- **開発層（選択可能）**: FastAPI, React - ローカル実行推奨（開発速度優先）
- **フルコンテナオプション**: 環境の完全な一貫性が必要な場合に使用

### 実行場所の区別
- **ローカルマシン**: Git操作、開発サーバー実行（高速開発時）、パッケージ管理
- **データコンテナ**: PostgreSQL, Redis, Keycloak（常時）
- **開発コンテナ**: 完全な環境一貫性が必要な場合のみ

### Python開発（uv使用）
```bash
# ローカル開発時（推奨）
cd backend
uv venv
uv pip install package
uv run python script.py
uv run pytest
uv run mypy --strict .

# コンテナ開発時
# コンテナ内で上記と同じコマンドを実行
```

## 目次

1. [システム開発設計書](#1-システム開発設計書)
2. [GitHub協調開発ワークフロー](#2-github協調開発ワークフロー)
3. [プロジェクトコンテキスト](#3-プロジェクトコンテキスト)
4. [コード生成テンプレート](#4-コード生成テンプレート)
5. [状態遷移定義](#5-状態遷移定義)
6. [既存システム分析](#6-既存システム分析)
7. [データモデル定義](#7-データモデル定義)
8. [API仕様定義](#8-api仕様定義)
9. [エラーカタログ](#9-エラーカタログ)
10. [非機能要件](#10-非機能要件)
11. [開発環境セットアップ](#11-開発環境セットアップ)
12. [自動化スクリプト](#12-自動化スクリプト)
13. [AI駆動開発（AIDD）](#13-ai駆動開発aidd)
14. [段階的移行戦略](#14-段階的移行戦略)
15. [AI時代のセキュリティ](#15-ai時代のセキュリティ)
16. [チーム開発ワークフロー](#16-チーム開発ワークフロー)

---

# 1. システム開発設計書

## 1.1 プロジェクト概要

### 技術スタック
- **バックエンド**: Python 3.11 + FastAPI
- **フロントエンド**: React 18 + TypeScript 5
- **データベース**: PostgreSQL 15
- **認証**: OAuth2 / OpenID Connect (Keycloak)
- **コンテナ**: Podman
- **Python管理**: uv
- **Node.js管理**: Volta
- **E2Eテスト**: Playwright
- **バージョン管理**: GitHub

### 開発環境
- Windows上のWSL2 (Ubuntu)
- Claude Code

## 1.2 ディレクトリ構造

```
project/
├── backend/                    # FastAPIバックエンド
│   ├── app/
│   │   ├── api/               # APIエンドポイント
│   │   │   └── v1/
│   │   ├── core/              # 設定、セキュリティ、依存関係
│   │   ├── models/            # SQLAlchemyモデル
│   │   ├── schemas/           # Pydanticスキーマ
│   │   ├── services/          # ビジネスロジック
│   │   └── main.py
│   ├── tests/                 # テストコード
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── alembic/               # DBマイグレーション
│   ├── docs/                  # API仕様書
│   │   ├── api-spec.md
│   │   └── test-spec.md
│   ├── .venv/                 # Python仮想環境（uvが管理）
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── requirements.txt       # 本番用（uv pip compileで生成）
│   └── requirements-dev.txt   # 開発用（uv pip compileで生成）
├── frontend/                   # Reactフロントエンド
│   ├── src/
│   │   ├── components/        # UIコンポーネント
│   │   ├── features/          # 機能別モジュール
│   │   ├── hooks/             # カスタムフック
│   │   ├── services/          # API通信
│   │   ├── types/             # TypeScript型定義
│   │   └── App.tsx
│   ├── tests/                 # テストコード
│   ├── docs/                  # フロントエンド仕様書
│   │   ├── component-spec.md
│   │   └── test-spec.md
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
├── e2e/                       # E2Eテスト
│   ├── tests/
│   ├── fixtures/
│   └── playwright.config.ts
├── infra/                     # インフラ設定
│   ├── compose.yaml           # 本番用Docker Compose
│   ├── compose-dev.yaml       # 開発用Docker Compose（Podman対応）
│   ├── Dockerfile.dev         # 開発用コンテナ定義
│   ├── docker-entrypoint-dev.sh
│   └── init-scripts/
├── scripts/                   # 自動化スクリプト（一部ローカル実行）
│   ├── init-project.sh        # ローカル実行
│   ├── setup-dev.sh           # 廃止（コンテナ内でmake install）
│   ├── test.sh               # ローカル実行（コンテナ経由）
│   ├── start-feature.sh      # ローカル実行（一部コンテナ経由）
│   ├── dev-env.sh           # ローカル実行（コンテナ管理）
│   └── claude-sync.sh       # 廃止
├── docs/                      # プロジェクトドキュメント
│   ├── architecture.md
│   ├── development-guide.md
│   └── test-strategy.md
├── .github/                   # GitHub設定（ローカルリポジトリ）
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── .claude/                   # AI開発用設定
│   ├── PROJECT_CONTEXT.md
│   ├── DATA_MODELS.yaml
│   ├── ERROR_CATALOG.md
│   └── META_PROMPT.md
├── Makefile                   # コンテナ内実行用
├── .pre-commit-config.yaml   # ローカル実行（コンテナ経由）
├── .env                      # 開発用環境変数（.gitignore対象）
└── README.md
```

---

# 2. GitHub協調開発ワークフロー

## 2.1 基本原則

- **全ての作業はIssueから始める**
- **Issueごとに必ず対応するPRを作成する**
- **PRは必ずDraftで作成し、WIP（作業中）はラベルやタイトルで明示する**
- **レビューはAI（Copilot Agent）→人間の順で実施（自動化済み）**
- **PR作成時に自動でレビュワーが割り当てられる（GitHub Actions）**
- **作業の重複を避けるため、WIP状態や担当者を明確にする**

## 2.2 開発フロー

```mermaid
graph TD
    A[Issue作成] --> B[担当者アサイン/WIPラベル]
    B --> C[Draft PR作成（WIP付与）]
    C --> D[実装・テスト]
    D --> E[Copilot Agentによる自動レビュー]
    E --> F[人間/AIによるレビュー]
    F --> G{レビュー指摘あり?}
    G -->|Yes| D
    G -->|No| H[Draft解除（Ready for review）]
    H --> I[最終レビュー・承認]
    I --> J[PRマージ & Issueクローズ]
```

### PR作成時の自動化

Draft PR作成時には、GitHub Actionsにより以下が自動実行されます：

1. **自動レビュワー追加**
   - GitHub Copilot（AI事前レビュー）が自動追加
   - チームメンバー（作成者以外）から1人を自動指名

2. **自動ラベル付与**
   - WIPラベルの自動付与
   - ファイル変更パターンに基づくラベル付与

これにより、レビュー依頼の手間を省き、確実にAIと人間両方のレビューを受けられます。

## 2.3 Claude Code開発プロンプト

```
私はこれから Issue #[番号] の [機能名] の実装を行います。以下の手順で進めてください：

前提条件の確認:
- ハイブリッド開発環境を使用します
- データ層（PostgreSQL, Redis, Keycloak）は `podman-compose -f infra/compose-data.yaml up -d` で起動済み
- 開発はローカル環境で実行（高速開発）またはコンテナ内（環境再現時）を選択

0. **Issue確認フェーズ**
   - Issue #[番号] の内容を確認し、要件を理解してください
   - 不明点があれば質問してください
   - 関連するIssueやPRがないか確認してください

1. **Draft PR作成フェーズ**
   - ローカルで feature/#[Issue番号]-[簡潔な説明] ブランチを作成
   - Draft PRを作成: `[WIP] feat: [機能名] (Closes #[Issue番号])`
   - PRに実装計画をコメントとして記載

2. **仕様書作成フェーズ**
   - 実装する機能の詳細仕様書を作成してください
   - 仕様書には以下を含めてください：
     * 機能概要
     * インターフェース定義（API仕様/コンポーネント仕様）
     * データモデル
     * エラーハンドリング仕様
     * セキュリティ考慮事項
   - 仕様書はPRにコメントとして追加

3. **テスト仕様作成フェーズ**
   - 仕様書に基づいて、テスト仕様書を作成してください
   - 以下のテストケースを含めてください：
     * 単体テストケース（正常系・異常系）
     * 統合テストケース
     * E2Eテストシナリオ
   - 各テストケースには期待値を明記してください

4. **テストコード実装フェーズ**
   - テスト仕様に基づいて、テストコードを先に実装してください
   - Pythonの場合: pytest を使用（`cd backend && uv run pytest` で実行）
   - TypeScriptの場合: vitest を使用（`cd frontend && npm test` で実行）
   - E2Eの場合: Playwright を使用
   - テストコードをコミット・プッシュ

5. **実装フェーズ**
   - テストが失敗することを確認してから、実装を開始してください
   - 実装は小さなステップで進め、各ステップでテストを実行してください
   - ローカル開発の場合:
     * Backend: `cd backend && uv run uvicorn app.main:app --reload`
     * Frontend: `cd frontend && npm run dev`
   - すべてのテストが通ることを確認してください
   - 定期的にコミット・プッシュしてPRを更新

6. **ドキュメント更新フェーズ**
   - 実装完了後、関連ドキュメントを更新してください
   - APIドキュメント、コンポーネントドキュメントなど

7. **レビュー準備フェーズ**
   - セルフレビューを実施
   - PR descriptionを最終化
   - Draft状態を解除してReady for reviewに変更

重要な制約事項：
- データ層は必ずコンテナで実行（PostgreSQL, Redis, Keycloak）
- 開発層はローカル実行を推奨（高速な反復開発）
- 必ずIssueを起点とし、Draft PRを早期に作成すること
- テストコードを書かずに実装を進めることは禁止です
- テストが通らないコードをコミットすることは禁止です
- 型定義は必須です（Python: typing, TypeScript: 明示的な型）
  - Pythonは mypy --strict でエラーなし
  - TypeScriptは tsc --noEmit でエラーなし
  - any型の使用は原則禁止
- エラーハンドリングは必須です
- WIP状態を明確にし、作業の重複を防ぐこと

開発コマンド例:
【ローカル開発（推奨）】
- データ層起動: `podman-compose -f infra/compose-data.yaml up -d`
- Backend開発: `cd backend && uv run uvicorn app.main:app --reload`
- Frontend開発: `cd frontend && npm run dev`
- テスト実行: `cd backend && uv run pytest`
- 型チェック: `cd backend && uv run mypy --strict .`

【フルコンテナ開発（環境再現時）】
- 全環境起動: `podman-compose -f infra/compose-dev.yaml up -d`
- コンテナ接続: `podman exec -it myapp-dev-workspace bash`
- 開発サーバー: `make dev` (コンテナ内)
```

## 2.4 GitHub テンプレート

### Issueテンプレート

```markdown
# .github/ISSUE_TEMPLATE/feature_request.md
---
name: 機能要望
about: 新機能の提案
title: ''
labels: 'feature'
assignees: ''
---

## 概要
<!-- 機能の簡潔な説明 -->

## 背景・目的
<!-- なぜこの機能が必要か -->

## 要件
<!-- 実装すべき要件のリスト -->
- [ ] 要件1
- [ ] 要件2

## 技術仕様案
<!-- 実装方針の提案（任意） -->

## 完了条件
<!-- この機能が完了したと判断できる条件 -->
- [ ] 条件1
- [ ] 条件2

## 参考資料
<!-- 関連資料へのリンクなど -->
```

### PRテンプレート

```markdown
# .github/pull_request_template.md

## 概要
<!-- このPRで何を実装・修正するか簡潔に説明 -->

## 関連Issue
Closes #<!-- Issue番号 -->

## 変更内容
<!-- 実装内容の詳細 -->
- [ ] 機能A
- [ ] 機能B

## テスト
<!-- 追加・更新したテストの説明 -->
- [ ] 単体テスト追加
- [ ] 統合テスト追加
- [ ] E2Eテスト追加

## スクリーンショット
<!-- UI変更がある場合は画面キャプチャを添付 -->

## チェックリスト
- [ ] テストが全て通る
- [ ] ドキュメントを更新した
- [ ] 型チェックが通る
- [ ] リントエラーがない
- [ ] セキュリティの考慮をした

## AIレビュー結果
<!-- Copilot Agentからの指摘事項と対応状況 -->
- [ ] 自動レビュー指摘事項に対応済み

## 備考
<!-- レビュアーへの補足事項など -->
```

---

# 3. プロジェクトコンテキスト

```markdown
# .claude/PROJECT_CONTEXT.md

## 開発環境

### 重要: ハイブリッド開発環境
- **データ層は常にコンテナで実行**（PostgreSQL, Redis, Keycloak）
- **開発層はローカル実行を推奨**（FastAPI, React）- 開発速度優先
- **フルコンテナオプション利用可能** - 環境再現が必要な場合

### 開発構成の選択
- ローカル開発: 日常的な開発作業（高速、推奨）
- フルコンテナ: 環境依存の問題調査、本番環境の再現

## ビジネスドメイン
- 主要エンティティ: User, Organization, Project, Task
- 主要ユースケース: [具体的な業務フロー]
- ビジネスルール: [制約事項、計算ロジック]

## 技術的制約
- レスポンスタイム: API 200ms以内
- 同時接続数: 1000ユーザー
- データ保持期間: 7年

## 命名規則
- API: /api/v1/{resource}/{id}
- DB: snake_case
- Python: snake_case
- TypeScript: camelCase

## AI用メタプロンプト

あなたはこのプロジェクトの開発を支援するAIアシスタントです。
以下の原則に従って開発を進めてください：

1. **ハイブリッド開発**: データ層はコンテナ、開発層は状況に応じて選択
2. **安全第一**: テストなしでコードを書かない
3. **文書化**: 実装前に仕様を文書化
4. **一貫性**: 既存のパターンに従う
5. **効率性**: テンプレートを活用
6. **品質**: コードレビューの観点を持つ

開発環境コマンド例:

ローカル開発（推奨）:
- データ層起動: `podman-compose -f infra/compose-data.yaml up -d`
- Backend起動: `cd backend && uv run uvicorn app.main:app --reload`
- Frontend起動: `cd frontend && npm run dev`
- テスト実行: `cd backend && uv run pytest`

フルコンテナ開発（オプション）:
- コンテナ起動: `podman-compose -f infra/compose-dev.yaml up -d`
- コンテナ接続: `podman exec -it myapp-dev-workspace bash`
- 開発サーバー: `make dev` (コンテナ内で実行)

Python開発の注意事項（uvを使用）:
- 仮想環境作成: `uv venv`
- パッケージインストール: `uv pip install package-name`
- スクリプト実行: `uv run python script.py`
- テスト実行: `uv run pytest`
- **activateは使用しません** - すべて`uv run`で実行

利用可能なリソース：
- PROJECT_CONTEXT.md: ビジネスドメイン知識
- CODE_TEMPLATES/: コード生成テンプレート
- DATA_MODELS.yaml: データモデル定義
- ERROR_CATALOG.md: エラー処理パターン
- SECURITY_CHECKLIST.md: セキュリティ要件

開発時は必ず以下の順序で進めること：
1. データ層の起動確認
2. 関連ドキュメントの参照
3. テスト仕様の作成
4. テストコードの実装
5. プロダクションコードの実装
6. ドキュメントの更新
```

---

# 4. コード生成テンプレート

## 4.1 Backend Templates

### APIエンドポイントテンプレート

```python
# File: backend/app/api/v1/{resource}.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.{resource} import {Resource}
from app.schemas.{resource} import (
    {Resource}Create,
    {Resource}Update,
    {Resource}Response,
    {Resource}ListResponse
)
from app.services.{resource} import {Resource}Service

router = APIRouter(prefix="/{resources}", tags=["{resources}"])

@router.get("", response_model={Resource}ListResponse)
async def list_{resources}(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> {Resource}ListResponse:
    """
    {Resources}の一覧を取得
    """
    service = {Resource}Service(db)
    items, total = await service.list(skip=skip, limit=limit, user=current_user)
    return {Resource}ListResponse(items=items, total=total, skip=skip, limit=limit)

@router.get("/{{{resource}_id}}", response_model={Resource}Response)
async def get_{resource}(
    {resource}_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> {Resource}Response:
    """
    {Resource}の詳細を取得
    """
    service = {Resource}Service(db)
    item = await service.get_by_id({resource}_id, user=current_user)
    if not item:
        raise HTTPException(status_code=404, detail="{Resource} not found")
    return item

@router.post("", response_model={Resource}Response, status_code=201)
async def create_{resource}(
    data: {Resource}Create,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> {Resource}Response:
    """
    新規{Resource}を作成
    """
    service = {Resource}Service(db)
    return await service.create(data, user=current_user)

@router.put("/{{{resource}_id}}", response_model={Resource}Response)
async def update_{resource}(
    {resource}_id: int,
    data: {Resource}Update,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> {Resource}Response:
    """
    {Resource}を更新
    """
    service = {Resource}Service(db)
    item = await service.update({resource}_id, data, user=current_user)
    if not item:
        raise HTTPException(status_code=404, detail="{Resource} not found")
    return item

@router.delete("/{{{resource}_id}}", status_code=204)
async def delete_{resource}(
    {resource}_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    {Resource}を削除
    """
    service = {Resource}Service(db)
    if not await service.delete({resource}_id, user=current_user):
        raise HTTPException(status_code=404, detail="{Resource} not found")
```

### サービスクラステンプレート

```python
# File: backend/app/services/{resource}.py
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.{resource} import {Resource}
from app.models.user import User
from app.schemas.{resource} import {Resource}Create, {Resource}Update

class {Resource}Service:
    def __init__(self, db: Session):
        self.db = db

    async def list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        user: Optional[User] = None
    ) -> Tuple[List[{Resource}], int]:
        """
        {Resource}一覧を取得
        """
        query = select({Resource})
        
        # フィルタリング条件を追加
        if user:
            query = query.filter({Resource}.user_id == user.id)
        
        # 総件数を取得
        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        
        # ページネーション適用
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return items, total

    async def get_by_id(
        self, 
        {resource}_id: int,
        user: Optional[User] = None
    ) -> Optional[{Resource}]:
        """
        IDで{Resource}を取得
        """
        query = select({Resource}).filter({Resource}.id == {resource}_id)
        
        if user:
            query = query.filter({Resource}.user_id == user.id)
            
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        data: {Resource}Create,
        user: Optional[User] = None
    ) -> {Resource}:
        """
        新規{Resource}を作成
        """
        db_obj = {Resource}(
            **data.dict(),
            user_id=user.id if user else None
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        {resource}_id: int,
        data: {Resource}Update,
        user: Optional[User] = None
    ) -> Optional[{Resource}]:
        """
        {Resource}を更新
        """
        db_obj = await self.get_by_id({resource}_id, user=user)
        if not db_obj:
            return None
            
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(
        self,
        {resource}_id: int,
        user: Optional[User] = None
    ) -> bool:
        """
        {Resource}を削除
        """
        db_obj = await self.get_by_id({resource}_id, user=user)
        if not db_obj:
            return False
            
        await self.db.delete(db_obj)
        await self.db.commit()
        return True
```

### テストテンプレート

```python
# File: backend/tests/unit/test_{resource}_service.py
import pytest
from sqlalchemy.orm import Session

from app.services.{resource} import {Resource}Service
from app.schemas.{resource} import {Resource}Create, {Resource}Update
from tests.factories import {Resource}Factory, UserFactory

class Test{Resource}Service:
    @pytest.fixture
    def service(self, db: Session) -> {Resource}Service:
        return {Resource}Service(db)

    async def test_create_{resource}(self, service: {Resource}Service, db: Session):
        # Arrange
        user = UserFactory()
        data = {Resource}Create(
            name="Test {Resource}",
            description="Test Description"
        )
        
        # Act
        result = await service.create(data, user=user)
        
        # Assert
        assert result.id is not None
        assert result.name == data.name
        assert result.description == data.description
        assert result.user_id == user.id

    async def test_get_{resource}_by_id(self, service: {Resource}Service, db: Session):
        # Arrange
        {resource} = {Resource}Factory()
        db.add({resource})
        await db.commit()
        
        # Act
        result = await service.get_by_id({resource}.id)
        
        # Assert
        assert result is not None
        assert result.id == {resource}.id

    async def test_update_{resource}(self, service: {Resource}Service, db: Session):
        # Arrange
        {resource} = {Resource}Factory()
        db.add({resource})
        await db.commit()
        
        update_data = {Resource}Update(name="Updated Name")
        
        # Act
        result = await service.update({resource}.id, update_data)
        
        # Assert
        assert result is not None
        assert result.name == "Updated Name"

    async def test_delete_{resource}(self, service: {Resource}Service, db: Session):
        # Arrange
        {resource} = {Resource}Factory()
        db.add({resource})
        await db.commit()
        
        # Act
        success = await service.delete({resource}.id)
        
        # Assert
        assert success is True
        assert await service.get_by_id({resource}.id) is None

# テスト実行コマンド（コンテナ内で実行）:
# cd /workspace/backend && uv run pytest tests/unit/test_{resource}_service.py -v
```

## 4.2 Frontend Templates

### Reactコンポーネントテンプレート

```typescript
// File: frontend/src/features/{resource}/components/{Resource}List.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { {resource}Api } from '../api/{resource}Api';
import { {Resource} } from '../types/{resource}';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorMessage } from '@/components/ErrorMessage';
import { Pagination } from '@/components/Pagination';

interface {Resource}ListProps {
  onSelect?: ({resource}: {Resource}) => void;
}

export const {Resource}List: React.FC<{Resource}ListProps> = ({ onSelect }) => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['{resources}', page, limit],
    queryFn: () => {resource}Api.list({ skip: (page - 1) * limit, limit }),
  });

  const deleteMutation = useMutation({
    mutationFn: {resource}Api.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{resources}'] });
    },
  });

  const handleDelete = async (id: number) => {
    if (confirm('削除してもよろしいですか？')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message="データの取得に失敗しました" />;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <div className="grid gap-4">
        {data.items.map(({resource}) => (
          <div
            key={{resource}.id}
            className="p-4 border rounded-lg hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start">
              <div 
                className="flex-1 cursor-pointer"
                onClick={() => onSelect?.({resource})}
              >
                <h3 className="text-lg font-semibold">{{resource}.name}</h3>
                <p className="text-gray-600">{{resource}.description}</p>
              </div>
              <button
                onClick={() => handleDelete({resource}.id)}
                className="text-red-600 hover:text-red-800"
              >
                削除
              </button>
            </div>
          </div>
        ))}
      </div>

      <Pagination
        currentPage={page}
        totalPages={Math.ceil(data.total / limit)}
        onPageChange={setPage}
      />
    </div>
  );
};
```

### API通信テンプレート

```typescript
// File: frontend/src/features/{resource}/api/{resource}Api.ts
import { apiClient } from '@/lib/apiClient';
import { 
  {Resource}, 
  {Resource}Create, 
  {Resource}Update,
  {Resource}ListResponse 
} from '../types/{resource}';

export const {resource}Api = {
  list: async (params: { skip?: number; limit?: number }): Promise<{Resource}ListResponse> => {
    const { data } = await apiClient.get('/{resources}', { params });
    return data;
  },

  get: async (id: number): Promise<{Resource}> => {
    const { data } = await apiClient.get(`/{resources}/${id}`);
    return data;
  },

  create: async (data: {Resource}Create): Promise<{Resource}> => {
    const { data: response } = await apiClient.post('/{resources}', data);
    return response;
  },

  update: async (id: number, data: {Resource}Update): Promise<{Resource}> => {
    const { data: response } = await apiClient.put(`/{resources}/${id}`, data);
    return response;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/{resources}/${id}`);
  },
};
```

### カスタムフックテンプレート

```typescript
// File: frontend/src/features/{resource}/hooks/use{Resource}.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { {resource}Api } from '../api/{resource}Api';
import { {Resource}Create, {Resource}Update } from '../types/{resource}';

export const use{Resource}List = (params?: { skip?: number; limit?: number }) => {
  return useQuery({
    queryKey: ['{resources}', params],
    queryFn: () => {resource}Api.list(params || {}),
  });
};

export const use{Resource} = (id: number) => {
  return useQuery({
    queryKey: ['{resources}', id],
    queryFn: () => {resource}Api.get(id),
    enabled: !!id,
  });
};

export const useCreate{Resource} = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: {Resource}Create) => {resource}Api.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{resources}'] });
    },
  });
};

export const useUpdate{Resource} = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: {Resource}Update }) => 
      {resource}Api.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['{resources}'] });
      queryClient.invalidateQueries({ queryKey: ['{resources}', id] });
    },
  });
};

export const useDelete{Resource} = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => {resource}Api.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{resources}'] });
    },
  });
};
```

---

# 5. 状態遷移定義

## 5.1 プロジェクト状態遷移

```mermaid
stateDiagram-v2
    [*] --> Draft: 作成
    Draft --> Active: 承認
    Draft --> Cancelled: キャンセル
    Active --> InProgress: 開始
    InProgress --> UnderReview: レビュー依頼
    UnderReview --> InProgress: 差し戻し
    UnderReview --> Completed: 承認
    InProgress --> OnHold: 一時停止
    OnHold --> InProgress: 再開
    Active --> Cancelled: キャンセル
    Completed --> Archived: アーカイブ
    Cancelled --> [*]
    Archived --> [*]
```

## 5.2 状態遷移ルール定義

```yaml
# .claude/STATE_MACHINES.yaml
entity: Project
states:
  - name: Draft
    description: 下書き状態
    allowed_transitions:
      - to: Active
        condition: has_required_fields && user.can_approve
        action: send_notification_to_members
      - to: Cancelled
        condition: user.is_owner
        
  - name: Active
    description: アクティブ状態
    allowed_transitions:
      - to: InProgress
        condition: has_assigned_member
      - to: Cancelled
        condition: user.is_owner && no_active_tasks
        
  - name: InProgress
    description: 進行中
    allowed_transitions:
      - to: UnderReview
        condition: all_tasks_completed
      - to: OnHold
        condition: user.can_manage
        
  - name: UnderReview
    description: レビュー中
    allowed_transitions:
      - to: InProgress
        condition: review_rejected
        action: notify_assignee
      - to: Completed
        condition: review_approved
        action: close_all_tasks
```

## 5.3 実装パターン

### Backend (Python)

```python
from enum import Enum
from typing import Dict, List, Optional, Callable
from datetime import datetime

class ProjectStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class StateTransition:
    def __init__(
        self, 
        from_state: ProjectStatus, 
        to_state: ProjectStatus,
        condition: Optional[Callable] = None,
        action: Optional[Callable] = None
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.action = action

class ProjectStateMachine:
    transitions: Dict[ProjectStatus, List[StateTransition]] = {
        ProjectStatus.DRAFT: [
            StateTransition(
                ProjectStatus.DRAFT,
                ProjectStatus.ACTIVE,
                condition=lambda ctx: ctx.has_required_fields() and ctx.user.can_approve(),
                action=lambda ctx: ctx.send_notification_to_members()
            ),
            StateTransition(
                ProjectStatus.DRAFT,
                ProjectStatus.CANCELLED,
                condition=lambda ctx: ctx.user.is_owner
            )
        ],
        # ... 他の遷移定義
    }
    
    @classmethod
    def can_transition(cls, project, to_state: ProjectStatus, context) -> bool:
        current_state = project.status
        possible_transitions = cls.transitions.get(current_state, [])
        
        for transition in possible_transitions:
            if transition.to_state == to_state:
                if transition.condition:
                    return transition.condition(context)
                return True
        return False
    
    @classmethod
    def transition(cls, project, to_state: ProjectStatus, context):
        if not cls.can_transition(project, to_state, context):
            raise ValueError(f"Cannot transition from {project.status} to {to_state}")
        
        # 遷移アクションの実行
        current_state = project.status
        for transition in cls.transitions[current_state]:
            if transition.to_state == to_state and transition.action:
                transition.action(context)
        
        # 状態更新
        project.status = to_state
        project.status_changed_at = datetime.utcnow()
```

---

# 6. 既存システム分析

## 6.1 旧システム分析

```yaml
# .claude/LEGACY_SYSTEM.yaml
system_info:
  name: "旧○○管理システム"
  version: "2.3.1"
  release_date: "2019-04-01"
  technology_stack:
    language: "Java 8"
    framework: "Spring Boot 1.5"
    database: "Oracle 12c"
    frontend: "jQuery + JSP"
  architecture: "モノリシック"
  deployment: "オンプレミス"
```

### 機能一覧と評価

| 機能名 | 説明 | 利用頻度 | ユーザー評価 | 移行要否 | 備考 |
|--------|------|----------|--------------|----------|------|
| ユーザー管理 | 基本的なCRUD | 高 | ★★★☆☆ | 要 | UI改善必要 |
| プロジェクト管理 | 進捗管理機能 | 高 | ★★☆☆☆ | 要（改修） | ワークフロー見直し |
| レポート出力 | Excel/PDF出力 | 中 | ★★★★☆ | 要 | 形式は維持 |
| バッチ処理 | 日次集計 | 高 | ★★★☆☆ | 要（改修） | 性能改善必要 |
| 通知機能 | メール通知のみ | 低 | ★☆☆☆☆ | 要（刷新） | Slack等追加 |

## 6.2 PoC分析

```yaml
# .claude/POC_LEARNINGS.yaml
poc_info:
  purpose: "新アーキテクチャの技術検証"
  duration: "2024-01-01 〜 2024-03-31"
  scope:
    - "認証機能のOIDC化"
    - "RESTful API設計"
    - "SPA化の検証"
    - "コンテナ化"
  technology_validation:
    - name: "FastAPI"
      result: "採用"
      reason: "高速、型安全、自動ドキュメント生成"
    - name: "React + TypeScript"
      result: "採用"
      reason: "型安全性、エコシステム"
    - name: "Keycloak"
      result: "採用"
      reason: "OIDC標準準拠、拡張性"

technical_decisions:
  adopted:
    - pattern: "Repository Pattern"
      code_example: |
        class UserRepository:
            async def get_by_id(self, user_id: int) -> Optional[User]:
                return await self.db.get(User, user_id)
      benefits:
        - "テスト容易性"
        - "DB実装の切り替え可能"
        
    - pattern: "Dependency Injection"
      implementation: "FastAPI Depends"
      benefits:
        - "疎結合"
        - "モック化容易"

  rejected:
    - pattern: "GraphQL"
      reason: "学習コスト高、REST APIで十分"
      alternative: "RESTful API with OpenAPI"
```

## 6.3 ギャップ分析

| カテゴリ | 旧システム | PoC | 新システム要件 | 対応方針 |
|----------|-----------|-----|----------------|----------|
| 認証 | 独自実装 | OIDC | OIDC + MFA | PoCベース拡張 |
| API | なし | REST | REST + GraphQL | 段階的追加 |
| UI | JSP | React SPA | React SPA | PoC継続 |
| 通知 | メールのみ | WebSocket | メール + Slack + Push | 新規開発 |
| レポート | Excel/PDF | 未実装 | Excel/PDF/BI連携 | 旧機能移植 |
| 監査ログ | ファイル出力 | 未実装 | DB + ログ基盤 | 新規開発 |

---

# 7. データモデル定義

```yaml
# .claude/DATA_MODELS.yaml
entities:
  User:
    fields:
      - name: id
        type: int
        primary_key: true
      - name: email
        type: str
        unique: true
        required: true
      - name: username
        type: str
        unique: true
        required: true
      - name: is_active
        type: bool
        default: true
      - name: created_at
        type: datetime
        auto_now_add: true
      - name: updated_at
        type: datetime
        auto_now: true
    relationships:
      - type: one_to_many
        target: Project
        field: projects
    indexes:
      - fields: [email]
      - fields: [username]
    
  Project:
    fields:
      - name: id
        type: int
        primary_key: true
      - name: name
        type: str
        required: true
        max_length: 200
      - name: description
        type: text
        nullable: true
      - name: status
        type: enum
        values: [draft, active, in_progress, under_review, on_hold, completed, cancelled, archived]
        default: draft
      - name: start_date
        type: date
        required: true
      - name: end_date
        type: date
        nullable: true
      - name: budget
        type: decimal
        precision: 15
        scale: 2
        nullable: true
    relationships:
      - type: many_to_one
        target: User
        field: owner
        on_delete: RESTRICT
      - type: many_to_many
        target: User
        field: members
        through: ProjectMember
    indexes:
      - fields: [status]
      - fields: [owner_id]
      - fields: [start_date, end_date]
      
  Task:
    fields:
      - name: id
        type: int
        primary_key: true
      - name: title
        type: str
        required: true
        max_length: 200
      - name: description
        type: text
        nullable: true
      - name: status
        type: enum
        values: [todo, in_progress, review, done]
        default: todo
      - name: priority
        type: enum
        values: [low, medium, high, urgent]
        default: medium
      - name: due_date
        type: datetime
        nullable: true
      - name: estimated_hours
        type: decimal
        precision: 5
        scale: 2
        nullable: true
      - name: actual_hours
        type: decimal
        precision: 5
        scale: 2
        nullable: true
    relationships:
      - type: many_to_one
        target: Project
        field: project
        on_delete: CASCADE
      - type: many_to_one
        target: User
        field: assignee
        nullable: true
        on_delete: SET_NULL
    indexes:
      - fields: [project_id, status]
      - fields: [assignee_id, status]
      - fields: [due_date]
```

---

# 8. API仕様定義

```yaml
# .claude/openapi.yaml
openapi: 3.0.0
info:
  title: MyApp API
  version: 1.0.0
  description: システムのREST API仕様

servers:
  - url: http://localhost:8000/api/v1
    description: 開発環境
  - url: https://api.example.com/v1
    description: 本番環境

security:
  - bearerAuth: []

paths:
  /users:
    get:
      summary: ユーザー一覧取得
      operationId: listUsers
      tags:
        - users
      parameters:
        - name: skip
          in: query
          schema:
            type: integer
            default: 0
            minimum: 0
        - name: limit
          in: query
          schema:
            type: integer
            default: 100
            minimum: 1
            maximum: 100
        - name: is_active
          in: query
          schema:
            type: boolean
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'

    post:
      summary: ユーザー作成
      operationId: createUser
      tags:
        - users
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
      responses:
        '201':
          description: 作成成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '409':
          $ref: '#/components/responses/Conflict'

  /users/{user_id}:
    get:
      summary: ユーザー詳細取得
      operationId: getUser
      tags:
        - users
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '404':
          $ref: '#/components/responses/NotFound'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    UserCreate:
      type: object
      required:
        - email
        - username
        - password
      properties:
        email:
          type: string
          format: email
        username:
          type: string
          minLength: 3
          maxLength: 30
        password:
          type: string
          minLength: 8

    UserResponse:
      type: object
      properties:
        id:
          type: integer
        email:
          type: string
        username:
          type: string
        is_active:
          type: boolean
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    UserListResponse:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/UserResponse'
        total:
          type: integer
        skip:
          type: integer
        limit:
          type: integer

    Error:
      type: object
      properties:
        error:
          type: string
        message:
          type: string
        details:
          type: object

  responses:
    BadRequest:
      description: リクエスト不正
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    Unauthorized:
      description: 認証エラー
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    NotFound:
      description: リソースが見つからない
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    Conflict:
      description: リソースの競合
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    InternalServerError:
      description: サーバーエラー
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

---

# 9. エラーカタログ

```markdown
# .claude/ERROR_CATALOG.md

## エラーコード体系

- E1xxx: 認証・認可関連
- E2xxx: ビジネスロジック関連
- E3xxx: データ検証関連
- E4xxx: 外部サービス関連
- E5xxx: システムエラー

## 認証エラー (E1xxx)

### E1001: 認証トークンが無効
- **原因**: トークン期限切れ、改ざん
- **HTTPステータス**: 401
- **対処**: 再ログイン
- **レスポンス例**:
  ```json
  {
    "error": "E1001",
    "message": "Invalid authentication token",
    "details": {
      "reason": "token_expired"
    }
  }
  ```

### E1002: 権限不足
- **原因**: リソースへのアクセス権限なし
- **HTTPステータス**: 403
- **対処**: 管理者に権限付与を依頼
- **レスポンス例**:
  ```json
  {
    "error": "E1002",
    "message": "Insufficient permissions",
    "details": {
      "required_role": "admin",
      "user_role": "member"
    }
  }
  ```

## ビジネスロジックエラー (E2xxx)

### E2001: 状態遷移エラー
- **原因**: 許可されない状態遷移
- **HTTPステータス**: 409
- **対処**: 現在の状態を確認
- **レスポンス例**:
  ```json
  {
    "error": "E2001",
    "message": "Invalid state transition",
    "details": {
      "current_state": "draft",
      "requested_state": "completed",
      "allowed_states": ["active", "cancelled"]
    }
  }
  ```

### E2002: ビジネスルール違反
- **原因**: ビジネスルールに違反する操作
- **HTTPステータス**: 422
- **対処**: 操作内容を確認
- **レスポンス例**:
  ```json
  {
    "error": "E2002",
    "message": "Business rule violation",
    "details": {
      "rule": "project_budget_exceeded",
      "max_budget": 1000000,
      "requested_budget": 1500000
    }
  }
  ```

## データ検証エラー (E3xxx)

### E3001: 必須項目未入力
- **原因**: 必須フィールドが空
- **HTTPステータス**: 400
- **対処**: 必須項目を入力
- **レスポンス例**:
  ```json
  {
    "error": "E3001",
    "message": "Required field missing",
    "details": {
      "fields": ["email", "username"]
    }
  }
  ```

### E3002: 重複データ
- **原因**: ユニーク制約違反
- **HTTPステータス**: 409
- **対処**: 別の値を使用
- **レスポンス例**:
  ```json
  {
    "error": "E3002",
    "message": "Duplicate entry",
    "details": {
      "field": "email",
      "value": "user@example.com"
    }
  }
  ```

## 外部サービスエラー (E4xxx)

### E4001: 外部API接続エラー
- **原因**: 外部サービスへの接続失敗
- **HTTPステータス**: 503
- **対処**: しばらく待って再試行
- **レスポンス例**:
  ```json
  {
    "error": "E4001",
    "message": "External service unavailable",
    "details": {
      "service": "keycloak",
      "retry_after": 30
    }
  }
  ```

## システムエラー (E5xxx)

### E5001: データベース接続エラー
- **原因**: DB接続失敗
- **HTTPステータス**: 500
- **対処**: システム管理者に連絡
- **レスポンス例**:
  ```json
  {
    "error": "E5001",
    "message": "Database connection error",
    "details": {
      "timestamp": "2024-01-01T00:00:00Z"
    }
  }
  ```
```

---

# 10. 非機能要件

## 10.1 パフォーマンス要件

### レスポンスタイム
| エンドポイント | 95%ile | 99%ile | 最大 |
|--------------|--------|--------|------|
| GET /users   | 100ms  | 200ms  | 1s   |
| POST /auth   | 200ms  | 500ms  | 2s   |
| GET /projects| 150ms  | 300ms  | 1.5s |
| 静的ファイル  | 50ms   | 100ms  | 500ms|

### スループット
- 同時接続数: 1,000
- RPS: 500 req/s (ピーク時)
- 同時実行タスク数: 100

## 10.2 可用性要件
- SLA: 99.5% (月間ダウンタイム: 約3.6時間)
- 計画メンテナンス: 月1回、深夜2時間以内
- RTO: 4時間
- RPO: 1時間

## 10.3 スケーラビリティ要件
- 水平スケール: API サーバー (最大10台)
- 垂直スケール: DB (最大 16vCPU, 64GB RAM)
- 自動スケール: CPU使用率 70% でトリガー
- データ増加率: 年間50%想定

## 10.4 セキュリティ要件

### 通信・暗号化
- 暗号化: TLS 1.3
- HSTS有効化
- 証明書: Let's Encrypt (自動更新)

### 認証・認可
- 認証: OAuth 2.0 + PKCE
- MFA: TOTP対応
- セッション: JWT (有効期限1時間)
- リフレッシュトークン: 7日間

### データ保護
- 保存時暗号化: AES-256
- パスワード: Argon2id
- PII暗号化: 必須
- バックアップ暗号化: 必須

### 監査・コンプライアンス
- 監査ログ: 7年保持
- アクセスログ: 90日保持
- GDPR準拠
- 個人情報マスキング

## 10.5 監視要件

### メトリクス収集
- APM: Prometheus + Grafana
- 収集間隔: 15秒
- 保持期間: 30日(詳細)、1年(集約)

### ログ管理
- ログ収集: ELK Stack
- ログレベル: 
  - Production: INFO
  - Staging: DEBUG
- 構造化ログ必須

### トレーシング
- 分散トレース: Jaeger
- サンプリング率: 1%
- トレース保持: 7日

### アラート
- 通知先: Slack, PagerDuty
- エスカレーション: 3段階
- 応答時間: 
  - Critical: 5分以内
  - Warning: 30分以内

## 10.6 依存関係マップ

```yaml
# .claude/DEPENDENCY_MAP.yaml
backend:
  runtime:
    python: "3.11"
    critical:
      - fastapi: "^0.109.0"  # セキュリティ更新に注意
      - sqlalchemy: "^2.0.25"  # 2.0系でAPI変更あり
      - pydantic: "^2.5.3"    # v1からの移行注意
      - alembic: "^1.13.1"
      - psycopg2-binary: "^2.9.9"
      - redis: "^5.0.1"
      - authlib: "^1.3.0"
      - httpx: "^0.26.0"
    
  infrastructure:
    - postgresql: "15.x"     # 14.xからのアップグレード可
    - redis: "7.x"          # Pub/Sub使用
    - keycloak: "22.x"      # 四半期ごとの更新
    
frontend:
  runtime:
    node: "20.11.0"         # LTS版推奨
    critical:
      - react: "^18.2.0"    # 並行レンダリング対応
      - typescript: "^5.3.3" # strictモード必須
      - vite: "^5.0.12"     # webpack からの移行
      - react-router-dom: "^6.21.3"
      - "@tanstack/react-query": "^5.17.19"  # v4からBreaking Change
      - axios: "^1.6.5"
      
security_updates:
  check_frequency: weekly
  auto_update_patch: true
  auto_update_minor: false
  notification: slack_webhook
```

---

# 11. 開発環境セットアップ（Podmanコンテナベース）

## 11.1 開発方針

### 11.1.1 ハイブリッド開発環境アーキテクチャ

**3層ハイブリッド構成の採用**

```yaml
開発環境の構成:
  常時コンテナ層:
    - PostgreSQL（データ永続性）
    - Redis（キャッシュ・Pub/Sub）
    - Keycloak（認証）
    理由: データの一貫性とセキュリティ
    
  ハイブリッド層:
    - FastAPI（ローカル開発推奨 / コンテナ切替可能）
    - バックグラウンドワーカー
    理由: 開発速度とデバッグの効率性
    
  ローカル優先層:
    - React/TypeScript（高速HMR必須）
    - 開発ツール（Storybook等）
    理由: フロントエンド開発の即時反映
```

**メリット:**
- 開発速度: 最大5倍向上（フロントエンド）
- Claude Code/Copilot: シームレスな連携
- セキュリティ: データ層は隔離維持
- 柔軟性: 必要に応じてフルコンテナに切替可能

**開発モードの選択基準:**
- **ローカル開発**: 日常的な開発作業（推奨）
- **フルコンテナ**: 環境依存の問題調査、本番環境の再現

## 11.2 前提条件

ローカルマシンに必要なもの：
- Podman 4.0以上
- Podman Compose
- Git
- VS Code または任意のエディタ（Remote Containers拡張推奨）

## 11.3 開発用コンテナ構成

### 開発用 Docker Compose

#### データ層用（常時使用）
```yaml
# infra/compose-data.yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: myapp-postgres
    environment:
      POSTGRES_PASSWORD: devpass
      POSTGRES_DB: myapp
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - myapp-network

  redis:
    image: redis:7-alpine
    container_name: myapp-redis
    ports:
      - "6379:6379"
    networks:
      - myapp-network

  keycloak:
    image: quay.io/keycloak/keycloak:22.0
    container_name: myapp-keycloak
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
    command: start-dev
    ports:
      - "8080:8080"
    networks:
      - myapp-network

volumes:
  pgdata:

networks:
  myapp-network:
    driver: bridge
```

#### フル開発環境用（オプション）
```yaml
# infra/compose-dev.yaml
version: '3.8'
services:
  # データ層は compose-data.yaml を使用
  
  # 開発用統合コンテナ（必要時のみ）
  dev-workspace:
    build:
      context: ..
      dockerfile: infra/Dockerfile.dev
    image: myapp-dev:latest
    container_name: myapp-dev-workspace
    volumes:
      - ..:/workspace:cached
      - ~/.ssh:/home/developer/.ssh:ro
      - ~/.gitconfig:/home/developer/.gitconfig:ro
    environment:
      - PYTHONPATH=/workspace/backend
      - DATABASE_URL=postgresql://postgres:devpass@localhost:5432/myapp
      - REDIS_URL=redis://localhost:6379
      - OIDC_ISSUER=http://localhost:8080/realms/myapp
    env_file:
      - ../.env
    network_mode: "host"  # ローカルのデータ層に接続
    command: /bin/bash -c "tail -f /dev/null"
```

### 開発用 Dockerfile

```dockerfile
# infra/Dockerfile.dev
FROM ubuntu:22.04

# 基本パッケージインストール
RUN apt-get update && apt-get install -y \
    curl \
    git \
    vim \
    sudo \
    build-essential \
    pkg-config \
    libssl-dev \
    && apt-get clean

# 開発用ユーザー作成
RUN useradd -m -s /bin/bash developer && \
    echo "developer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER developer
WORKDIR /home/developer

# Python (uv) セットアップ
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/developer/.cargo/bin:${PATH}"

# Node.js (Volta) セットアップ
RUN curl https://get.volta.sh | bash
ENV VOLTA_HOME="/home/developer/.volta"
ENV PATH="${VOLTA_HOME}/bin:${PATH}"
RUN volta install node@20 npm@10

# 作業ディレクトリ設定
WORKDIR /workspace

# エントリーポイント
COPY infra/docker-entrypoint-dev.sh /usr/local/bin/
RUN sudo chmod +x /usr/local/bin/docker-entrypoint-dev.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint-dev.sh"]
```

### 開発用エントリーポイント

```bash
#!/bin/bash
# infra/docker-entrypoint-dev.sh

echo "🚀 開発環境を初期化しています..."

# Backend セットアップ
if [ -f "/workspace/backend/pyproject.toml" ]; then
    echo "📦 Python依存関係をインストール中..."
    cd /workspace/backend
    uv venv
    uv pip sync requirements-dev.txt || echo "⚠️  requirements-dev.txt が見つかりません"
fi

# Frontend セットアップ
if [ -f "/workspace/frontend/package.json" ]; then
    echo "📦 Node.js依存関係をインストール中..."
    cd /workspace/frontend
    npm install
fi

echo "✅ 開発環境の準備が完了しました！"
echo "💡 ヒント: 'make dev' で開発サーバーを起動できます"
echo "💡 Python実行: cd backend && uv run python ..."
echo "💡 テスト実行: cd backend && uv run pytest"

# bashシェルを起動
exec /bin/bash
```

## 11.4 初回セットアップ手順

### 共通セットアップ
```bash
# 1. リポジトリクローン（ローカルマシンで実行）
git clone https://github.com/yourorg/yourproject.git
cd yourproject

# 2. データ層コンテナの起動（ローカルマシンで実行）
podman-compose -f infra/compose-data.yaml up -d

# 3. データベース初期化（ローカルマシンで実行）
podman exec myapp-postgres psql -U postgres -d myapp -c "CREATE EXTENSION IF NOT EXISTS uuid-ossp;"
```

### ローカル開発環境（推奨）
```bash
# 4. Python環境セットアップ（ローカルマシンで実行）
cd backend
uv venv
uv pip sync requirements-dev.txt

# 5. データベースマイグレーション（ローカルマシンで実行）
uv run alembic upgrade head

# 6. Node.js環境セットアップ（ローカルマシンで実行）
cd ../frontend
npm install

# 7. 開発サーバー起動（ローカルマシンで実行）
# Terminal 1: Backend
cd backend && uv run uvicorn app.main:app --reload

# Terminal 2: Frontend  
cd frontend && npm run dev
```

### フルコンテナ開発環境（オプション）
```bash
# 4. 開発用コンテナイメージのビルド（ローカルマシンで実行）
podman-compose -f infra/compose-dev.yaml build

# 5. 開発コンテナ起動（ローカルマシンで実行）
podman-compose -f infra/compose-dev.yaml up -d

# 6. 開発用コンテナに接続（ローカルマシンで実行）
podman exec -it myapp-dev-workspace bash

# ===== 以降はコンテナ内で実行 =====

# 7. 依存関係の確認とインストール（コンテナ内）
cd /workspace/backend
uv pip sync requirements-dev.txt  # 通常は自動実行済み

# 8. データベース初期化（コンテナ内）
cd /workspace/backend
uv run alembic upgrade head

# 9. 開発サーバー起動（コンテナ内）
cd /workspace
make dev
```

## 11.5 日常的な開発フロー

### ローカル開発フロー（推奨）
```bash
# 1. データ層起動（ローカルマシンで実行）
cd yourproject
podman-compose -f infra/compose-data.yaml up -d

# 2. 最新の変更を取得（ローカルマシンで実行）
git pull origin develop

# 3. Issue用のブランチ作成（ローカルマシンで実行）
git checkout -b feature/#123-user-authentication

# 4. 開発サーバー起動（ローカルマシンで実行）
# Terminal 1: Backend
cd backend && uv run uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# 5. 実装・テスト（ローカルマシンで実行）
# VS Code/Claude Codeで直接編集
# ホットリロードで即座に反映

# 6. テスト実行（ローカルマシンで実行）
cd backend && uv run pytest
cd frontend && npm test

# 7. 型チェック実行（ローカルマシンで実行）
cd backend && uv run mypy --strict .
cd frontend && npm run type-check

# 8. コミット・プッシュ（ローカルマシンで実行）
git add .
git commit -m "feat: add user authentication"
git push -u origin feature/#123-user-authentication

# 9. Draft PR作成（ローカルマシンで実行）
gh pr create --draft --title "[WIP] feat: user authentication (Closes #123)"
```

### フルコンテナ開発フロー（環境依存問題の調査時）
```bash
# 1. 開発環境起動
cd yourproject
podman-compose -f infra/compose-data.yaml up -d
podman-compose -f infra/compose-dev.yaml up -d

# 2. 開発コンテナに接続
podman exec -it myapp-dev-workspace bash

# ===== 以降はコンテナ内での作業 =====

# 3. 最新の変更を取得
cd /workspace
git pull origin develop

# 4. Issue用のブランチ作成
git checkout -b feature/#123-user-authentication

# 5. 開発サーバー起動（別ターミナル、コンテナ内で）
cd /workspace
make dev

# 6-9. 実装からPR作成まで（上記と同様）
```

## 11.6 VS Code Remote Containers設定

```json
// .devcontainer/devcontainer.json
{
    "name": "MyApp Development",
    "dockerComposeFile": "../infra/compose-dev.yaml",
    "service": "dev-workspace",
    "workspaceFolder": "/workspace",
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-python.python",
                "ms-python.vscode-pylance",
                "charliermarsh.ruff",
                "ms-python.mypy-type-checker",
                "dbaeumer.vscode-eslint",
                "esbenp.prettier-vscode",
                "bradlc.vscode-tailwindcss"
            ],
            "settings": {
                // uvは.venv内のPythonを使用
                "python.defaultInterpreterPath": "/workspace/backend/.venv/bin/python",
                "python.linting.enabled": true,
                "python.linting.ruffEnabled": true,
                "python.formatting.provider": "ruff",
                // ターミナルでのPython実行はuv runを推奨
                "python.terminal.activateEnvironment": false,
                "[python]": {
                    "editor.formatOnSave": true
                },
                "[typescript]": {
                    "editor.formatOnSave": true,
                    "editor.defaultFormatter": "esbenp.prettier-vscode"
                },
                // uvコマンドのヒント
                "terminal.integrated.env.linux": {
                    "PYTHONPATH": "/workspace/backend"
                }
            }
        }
    },
    // 開発コンテナ起動時のコマンド
    "postCreateCommand": "cd backend && uv venv && uv pip sync requirements-dev.txt"
}
```

## 11.7 Makefile（ハイブリッド開発対応）

```makefile
# Makefile - ローカル実行とコンテナ実行の両方に対応
# 環境変数 DEV_MODE で切り替え（local または container）

DEV_MODE ?= local

.PHONY: dev test build install typecheck help

# デフォルトターゲット
help:
	@echo "📚 利用可能なコマンド:"
	@echo "  make dev        - 開発サーバーを起動"
	@echo "  make test       - すべてのテストを実行"
	@echo "  make typecheck  - 型チェックを実行"
	@echo "  make install    - 依存関係をインストール"
	@echo "  make db-up      - データ層を起動"
	@echo "  make db-down    - データ層を停止"
	@echo ""
	@echo "🔧 開発モード: $(DEV_MODE) (DEV_MODE=container で変更可能)"

# データ層管理
db-up:
	@echo "🚀 データ層を起動します..."
	podman-compose -f infra/compose-data.yaml up -d

db-down:
	@echo "🛑 データ層を停止します..."
	podman-compose -f infra/compose-data.yaml down

# 開発サーバー起動
dev: db-up
ifeq ($(DEV_MODE),local)
	@echo "🚀 ローカル開発サーバーを起動します..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	# Backend（バックグラウンド）
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	# Frontend（フォアグラウンド）
	cd frontend && npm run dev
else
	@echo "🚀 コンテナ内開発サーバーを起動します..."
	podman exec -it myapp-dev-workspace bash -c "cd /workspace && make dev-internal"
endif

# コンテナ内部用（直接呼ばない）
dev-internal:
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	cd frontend && npm run dev -- --host 0.0.0.0 &
	wait

# 依存関係インストール
install:
ifeq ($(DEV_MODE),local)
	@echo "📦 ローカル環境に依存関係をインストールします..."
	cd backend && uv venv && uv pip sync requirements-dev.txt
	cd frontend && npm ci
else
	@echo "📦 コンテナ内に依存関係をインストールします..."
	podman exec myapp-dev-workspace bash -c "cd /workspace && make install-internal"
endif

install-internal:
	cd backend && uv venv && uv pip sync requirements-dev.txt
	cd frontend && npm ci

# テスト実行
test:
ifeq ($(DEV_MODE),local)
	@echo "🧪 ローカル環境でテストを実行します..."
	cd backend && uv run pytest
	cd frontend && npm test
else
	@echo "🧪 コンテナ内でテストを実行します..."
	podman exec -t myapp-dev-workspace bash -c "cd /workspace && make test-internal"
endif

test-internal:
	cd backend && source .venv/bin/activate && pytest
	cd frontend && npm test
	cd e2e && npx playwright test

# 型チェック
typecheck:
ifeq ($(DEV_MODE),local)
	@echo "📋 ローカル環境で型チェックを実行します..."
	cd backend && uv run mypy --strict .
	cd frontend && npm run type-check
else
	@echo "📋 コンテナ内で型チェックを実行します..."
	podman exec -t myapp-dev-workspace bash -c "cd /workspace && make typecheck-internal"
endif

typecheck-internal:
	cd backend && source .venv/bin/activate && mypy --strict .
	cd frontend && npm run type-check

# データベースマイグレーション
migrate:
ifeq ($(DEV_MODE),local)
	@echo "🗄️  データベースマイグレーションを実行します..."
	cd backend && uv run alembic upgrade head
else
	podman exec -t myapp-dev-workspace bash -c "cd /workspace/backend && source .venv/bin/activate && alembic upgrade head"
endif

# 環境クリーンアップ
clean:
	@echo "🧹 一時ファイルを削除します..."
	cd backend && rm -rf .venv __pycache__ .pytest_cache .mypy_cache htmlcov .coverage
	cd frontend && rm -rf node_modules dist coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete || true
```

## 11.8 開発環境のベストプラクティス

### ハイブリッド開発の推奨事項

1. **開発モードの使い分け**
   - **ローカル開発**: 日常的な機能開発、デバッグ作業
   - **フルコンテナ**: 環境依存の問題調査、CI/CD環境の再現

2. **データ層の管理**
   - データ層は常にコンテナで実行（一貫性保証）
   - `make db-up` で起動、`make db-down` で停止
   - データは名前付きボリュームで永続化

3. **パフォーマンス最適化**
   - フロントエンド開発はローカル実行でHMR活用
   - バックエンドもローカル実行で高速な反復開発
   - 必要時のみフルコンテナ環境を使用

4. **環境変数の管理**
   - 開発用の環境変数は `.env` ファイルで管理
   - データベース接続はローカルホスト経由
   - 秘密情報は `.gitignore` に追加

5. **定期的なメンテナンス**
   ```bash
   # データ層のイメージ更新（週次）
   podman-compose -f infra/compose-data.yaml pull
   podman-compose -f infra/compose-data.yaml up -d
   
   # 不要なイメージの削除
   podman image prune -a
   ```

### ローカル開発の利点
- **開発速度**: 5倍高速（特にフロントエンド）
- **デバッグ**: IDE/エディタとの完全な統合
- **リソース効率**: 最小限のリソース使用

### フルコンテナの使用場面
- 本番環境の問題再現
- 複雑な依存関係の検証
- チーム間の環境統一が必要な場合

## 11.9 コンテナベース開発のFAQ

### Q: なぜハイブリッド構成を採用するのか？
A: 以下の理由から最適なバランスを実現します：
- データ層の一貫性とセキュリティ（コンテナ）
- 開発速度の最大化（ローカル実行）
- 必要に応じた完全な環境再現（フルコンテナオプション）
- Claude Code/GitHub Copilotとの最適な連携

### Q: どちらの開発モードを使うべきか？
A: 用途に応じて選択してください：
- **ローカル開発（推奨）**: 
  - 日常的な開発作業
  - 高速な反復開発が必要な場合
  - フロントエンドの開発
- **フルコンテナ開発**:
  - 環境依存の問題調査
  - 本番環境の再現が必要な場合
  - CI/CD環境での動作確認

### Q: なぜuvを使うのか？
A: uvには以下の利点があります：
- 高速なパッケージインストール（pipより10倍以上速い）
- 仮想環境の自動管理
- activateが不要（`uv run` で直接実行）
- 依存関係の厳密な管理
- Rustベースで高性能

### Q: VS Codeでの開発方法は？
A: 2つの方法があります：
1. **ローカル開発（推奨）**: 通常通りVS Codeを使用
2. **Remote Containers**: フルコンテナ開発時に使用
   - 拡張機能「Remote - Containers」をインストール
   - 「Reopen in Container」を選択

### Q: パフォーマンスが遅い場合は？
A: 開発モードを確認してください：
- ローカル開発に切り替える（`make dev`）
- データ層のみコンテナで実行
- 不要なコンテナを停止（`podman ps` で確認）

### Q: デバッグ方法は？
A: 開発モードに応じて：
- **ローカル開発**: VS CodeやPyCharmで直接デバッグ
- **コンテナ開発**: 
  - Python: `uv run python -m pdb`
  - Node.js: Chrome DevToolsをポート経由で接続

### Q: データベースへの接続方法は？
A: 環境に応じて：
- **ローカル開発**: `postgresql://postgres:devpass@localhost:5432/myapp`
- **コンテナ開発**: `postgresql://postgres:devpass@postgres:5432/myapp`
- pgAdminなどのツールは `localhost:5432` で接続

### Q: uvコマンドの基本的な使い方は？
A: よく使うuvコマンド：
```bash
# 仮想環境作成
uv venv

# パッケージインストール
uv pip install package-name

# requirements.txtから一括インストール
uv pip sync requirements.txt

# パッケージ一覧表示
uv pip list

# Pythonスクリプト実行
uv run python script.py

# pytest実行
uv run pytest

# 任意のコマンドを仮想環境内で実行
uv run command-name
```

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim as builder

# uvインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml requirements.txt ./
RUN uv venv && \
    uv pip sync requirements.txt

FROM python:3.11-slim
WORKDIR /app

# uvを本番イメージにもコピー（必要に応じて）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 仮想環境をコピー
COPY --from=builder /app/.venv /app/.venv
COPY . .

# uvを使って実行
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine as builder

# voltaインストール
RUN apk add --no-cache curl bash && \
    curl https://get.volta.sh | bash
ENV VOLTA_HOME=/root/.volta
ENV PATH=$VOLTA_HOME/bin:$PATH

WORKDIR /app
COPY package.json package-lock.json ./
COPY .volta ./volta
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
```

## 11.5 型チェック設定

### TypeScript設定 (tsconfig.json)

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    
    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    
    /* Strict Type-Checking Options */
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "useUnknownInCatchVariables": true,
    "alwaysStrict": true,
    
    /* Additional Checks */
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    
    /* Paths */
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### Python設定 (pyproject.toml)

```toml
# backend/pyproject.toml
[project]
name = "myapp-backend"
version = "0.1.0"
description = "FastAPI backend"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.25",
    "alembic>=1.13.1",
    "psycopg2-binary>=2.9.9",
    "redis>=5.0.1",
    "authlib>=1.3.0",
    "httpx>=0.26.0",
    "pydantic>=2.5.3",
    "pydantic-settings>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.4",
    "pytest-asyncio>=0.23.3",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.14",
    "mypy>=1.8.0",
    "types-redis>=4.6.0.20240106",
    "types-passlib>=1.7.7.20240106",
    "httpx>=0.26.0",
]

# uvでの依存関係管理
# requirements.txt生成: uv pip compile pyproject.toml -o requirements.txt
# requirements-dev.txt生成: uv pip compile pyproject.toml --extra dev -o requirements-dev.txt
# インストール: uv pip sync requirements.txt (または requirements-dev.txt)

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
exclude = ["alembic/", "tests/"]
plugins = ["pydantic.mypy"]

# 厳格な型チェックオプション
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

# サードパーティライブラリの型定義
[[tool.mypy.overrides]]
module = "authlib.*"
ignore_missing_imports = true
```

### mypy.ini (代替設定)

```ini
# backend/mypy.ini
[mypy]
python_version = 3.11
strict = True
exclude = tests/|alembic/

# 厳格な型チェックオプション
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

# Import discovery
namespace_packages = True
explicit_package_bases = True

[mypy-authlib.*]
ignore_missing_imports = True

[mypy-redis.*]
ignore_missing_imports = True
```

### Podman Compose

```yaml
# infra/compose.yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: devpass
      POSTGRES_DB: myapp
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  keycloak:
    image: quay.io/keycloak/keycloak:22.0
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
    command: start-dev
    ports:
      - "8080:8080"

volumes:
  pgdata:
```

---

# 12. 自動化スクリプト

## 12.1 プロジェクト初期化

```bash
#!/bin/bash
# scripts/init-project.sh

echo "🚀 ハイブリッド開発環境を初期化します..."

# Podmanがインストールされているか確認
if ! command -v podman &> /dev/null; then
    echo "❌ Podmanがインストールされていません"
    echo "インストール方法: https://podman.io/getting-started/installation"
    exit 1
fi

# Podman Composeがインストールされているか確認
if ! command -v podman-compose &> /dev/null; then
    echo "❌ Podman Composeがインストールされていません"
    echo "インストール: pip install podman-compose"
    exit 1
fi

# uvがインストールされているか確認（ローカル開発用）
if ! command -v uv &> /dev/null; then
    echo "📦 uvをインストールします..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uvがインストールされました"
fi

# データ層コンテナイメージのpull
echo "🔨 データ層コンテナイメージを取得しています..."
podman-compose -f infra/compose-data.yaml pull

# 開発用コンテナイメージのビルド（オプション用）
echo "🔨 開発用コンテナイメージをビルドしています（オプション）..."
podman-compose -f infra/compose-dev.yaml build

# 環境変数ファイルの作成
if [ ! -f .env ]; then
    echo "📝 環境変数ファイルを作成しています..."
    cat > .env << 'EOF'
# Development Environment Variables
DATABASE_URL=postgresql://postgres:devpass@localhost:5432/myapp
REDIS_URL=redis://localhost:6379
OIDC_ISSUER=http://localhost:8080/realms/myapp
SECRET_KEY=dev-secret-key-change-in-production
EOF
fi

# Git hooks設定（ローカルで実行）
echo "🔗 Git hooksを設定しています..."
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# pre-commitはローカルまたはコンテナで型チェックを実行
echo "🔍 Pre-commit checks..."

# ローカル開発環境がセットアップされているか確認
if [ -d "backend/.venv" ]; then
    # ローカルで実行
    cd backend && uv run mypy --strict . || exit 1
    cd ../frontend && npm run type-check || exit 1
elif podman ps | grep -q myapp-dev-workspace; then
    # コンテナで実行
    podman exec myapp-dev-workspace bash -c "cd /workspace/backend && uv run mypy --strict ." || exit 1
    podman exec myapp-dev-workspace bash -c "cd /workspace/frontend && npm run type-check" || exit 1
else
    echo "⚠️  開発環境が見つかりません。型チェックをスキップします。"
fi

echo "✅ Pre-commit checks passed!"
EOF
chmod +x .git/hooks/pre-commit

echo "✅ ハイブリッド開発環境の初期化が完了しました！"
echo ""
echo "次のステップ:"
echo ""
echo "【推奨: ローカル開発】"
echo "1. podman-compose -f infra/compose-data.yaml up -d  # データ層起動"
echo "2. cd backend && uv venv && uv pip sync requirements-dev.txt"
echo "3. cd frontend && npm install"
echo "4. 開発開始！"
echo ""
echo "【オプション: フルコンテナ開発】"
echo "1. podman-compose -f infra/compose-dev.yaml up -d"
echo "2. podman exec -it myapp-dev-workspace bash"
echo "3. コンテナ内で make dev を実行"
```

## 12.2 機能開発開始スクリプト

```bash
#!/bin/bash
# scripts/start-feature.sh
# このスクリプトはローカルマシンで実行します

# Usage: ./scripts/start-feature.sh <issue-number> <feature-name>

ISSUE_NUMBER=$1
FEATURE_NAME=$2

if [ -z "$ISSUE_NUMBER" ] || [ -z "$FEATURE_NAME" ]; then
    echo "Usage: $0 <issue-number> <feature-name>"
    exit 1
fi

# 開発コンテナが起動しているか確認
if ! podman ps | grep -q myapp-dev-workspace; then
    echo "❌ 開発コンテナが起動していません"
    echo "実行: podman-compose -f infra/compose-dev.yaml up -d"
    exit 1
fi

echo "🚀 Issue #${ISSUE_NUMBER} の作業を開始します..."

# ブランチ作成とPR作成はコンテナ内で実行
podman exec -it myapp-dev-workspace bash -c "
    cd /workspace
    
    # 最新の変更を取得
    git pull origin develop
    
    # ブランチ作成
    BRANCH_NAME='feature/#${ISSUE_NUMBER}-${FEATURE_NAME}'
    git checkout -b \$BRANCH_NAME
    
    # 初期コミット
    touch .gitkeep
    git add .gitkeep
    git commit -m 'feat: start work on #${ISSUE_NUMBER}'
    git push -u origin \$BRANCH_NAME
"

# GitHub CLIはローカルで実行（認証情報の関係）
if command -v gh &> /dev/null; then
    gh pr create \
      --draft \
      --title "[WIP] feat: ${FEATURE_NAME} (Closes #${ISSUE_NUMBER})" \
      --body "## 概要\nIssue #${ISSUE_NUMBER} の実装\n\n## 作業計画\n- [ ] 仕様書作成\n- [ ] テスト作成\n- [ ] 実装\n- [ ] ドキュメント更新" \
      --assignee @me
else
    echo "⚠️  GitHub CLIがインストールされていません。手動でDraft PRを作成してください。"
fi

echo "✅ Branch created: feature/#${ISSUE_NUMBER}-${FEATURE_NAME}"
echo "📝 Next: podman exec -it myapp-dev-workspace bash で開発を開始"
```

## 12.3 テスト実行スクリプト

```bash
#!/bin/bash
# scripts/test.sh
# このスクリプトはローカルマシンで実行し、適切な環境でテストを実行します

set -e

echo "🧪 テストを実行します..."

# 実行環境の判定
if [ -d "backend/.venv" ] && [ -d "frontend/node_modules" ]; then
    echo "📍 ローカル環境でテストを実行します..."
    
    # ローカル環境でのテスト実行
    echo "🧪 Running Backend Tests..."
    cd backend
    
    # 型チェック
    echo "  📋 Type checking with mypy..."
    uv run mypy --strict --show-error-codes .
    
    # リンターチェック
    echo "  🔍 Linting with ruff..."
    uv run ruff check .
    
    # テスト実行
    echo "  🧪 Running pytest..."
    uv run pytest --cov=app --cov-report=term-missing --cov-report=html
    
    echo "✅ Backend checks passed!"
    
    echo ""
    echo "🧪 Running Frontend Tests..."
    cd ../frontend
    
    # 型チェック
    echo "  📋 Type checking with tsc..."
    npm run type-check
    
    # リンターチェック
    echo "  🔍 Linting with ESLint..."
    npm run lint
    
    # テスト実行
    echo "  🧪 Running vitest..."
    npm run test:ci
    
    echo "✅ Frontend checks passed!"
    
elif podman ps | grep -q myapp-dev-workspace; then
    echo "📍 コンテナ環境でテストを実行します..."
    
    # コンテナ内でのテスト実行
    podman exec -t myapp-dev-workspace bash -c '
        set -e
        
        echo "🧪 Running Backend Tests..."
        cd /workspace/backend
        
        # 型チェック
        echo "  📋 Type checking with mypy..."
        uv run mypy --strict --show-error-codes .
        
        # リンターチェック
        echo "  🔍 Linting with ruff..."
        uv run ruff check .
        
        # テスト実行
        echo "  🧪 Running pytest..."
        uv run pytest --cov=app --cov-report=term-missing --cov-report=html
        
        echo "✅ Backend checks passed!"
        
        echo ""
        echo "🧪 Running Frontend Tests..."
        cd /workspace/frontend
        
        # 型チェック
        echo "  📋 Type checking with tsc..."
        npm run type-check
        
        # リンターチェック
        echo "  🔍 Linting with ESLint..."
        npm run lint
        
        # テスト実行
        echo "  🧪 Running vitest..."
        npm run test:ci
        
        echo "✅ Frontend checks passed!"
        
        echo ""
        echo "🧪 Running E2E Tests..."
        cd /workspace/e2e
        npx playwright test --reporter=list
        
        echo "✅ All tests passed!"
    '
else
    echo "❌ 開発環境が見つかりません"
    echo "以下のいずれかを実行してください："
    echo "1. ローカル開発: cd backend && uv venv && uv pip sync requirements-dev.txt"
    echo "2. コンテナ開発: ./scripts/dev-env.sh start-full"
    exit 1
fi

# テスト結果の確認
echo ""
echo "📊 テスト結果:"
echo "- Backend カバレッジ: backend/htmlcov/index.html"
echo "- Frontend カバレッジ: frontend/coverage/index.html"
if [ -d "e2e/playwright-report" ]; then
    echo "- E2E レポート: e2e/playwright-report/index.html"
fi
```

## 12.4 開発環境管理スクリプト

```bash
#!/bin/bash
# scripts/dev-env.sh
# このスクリプトはローカルマシンで実行し、開発環境を管理します

case "$1" in
    "start")
        echo "🚀 開発環境を起動します..."
        echo "データ層（PostgreSQL, Redis, Keycloak）を起動中..."
        podman-compose -f infra/compose-data.yaml up -d
        echo "✅ データ層が起動しました"
        echo ""
        echo "📝 次のステップ:"
        echo "【ローカル開発（推奨）】"
        echo "  cd backend && uv run uvicorn app.main:app --reload"
        echo "  cd frontend && npm run dev"
        echo ""
        echo "【フルコンテナ開発】"
        echo "  ./scripts/dev-env.sh start-full"
        ;;
    
    "start-full")
        echo "🚀 フルコンテナ開発環境を起動します..."
        podman-compose -f infra/compose-data.yaml up -d
        podman-compose -f infra/compose-dev.yaml up -d
        echo "✅ フル開発環境が起動しました"
        echo "接続: podman exec -it myapp-dev-workspace bash"
        ;;
    
    "stop")
        echo "🛑 開発環境を停止します..."
        podman-compose -f infra/compose-data.yaml stop
        podman-compose -f infra/compose-dev.yaml stop 2>/dev/null
        echo "✅ 開発環境が停止しました"
        ;;
    
    "restart")
        echo "🔄 開発環境を再起動します..."
        podman-compose -f infra/compose-data.yaml restart
        echo "✅ データ層が再起動しました"
        ;;
    
    "clean")
        echo "🧹 開発環境をクリーンアップします..."
        podman-compose -f infra/compose-data.yaml down -v
        podman-compose -f infra/compose-dev.yaml down -v 2>/dev/null
        echo "✅ 開発環境がクリーンアップされました"
        ;;
    
    "logs")
        echo "📜 開発環境のログを表示します..."
        podman-compose -f infra/compose-data.yaml logs -f
        ;;
    
    "shell")
        echo "🐚 開発コンテナに接続します..."
        if ! podman ps | grep -q myapp-dev-workspace; then
            echo "⚠️  開発コンテナが起動していません"
            echo "実行: ./scripts/dev-env.sh start-full"
            exit 1
        fi
        echo "💡 Pythonコマンドは 'uv run python' を使用してください"
        echo "💡 テストは 'uv run pytest' を使用してください"
        echo "💡 型チェックは 'uv run mypy' を使用してください"
        podman exec -it myapp-dev-workspace bash
        ;;
    
    "status")
        echo "📊 開発環境のステータス:"
        echo ""
        echo "【データ層】"
        podman-compose -f infra/compose-data.yaml ps
        echo ""
        echo "【開発コンテナ（オプション）】"
        podman-compose -f infra/compose-dev.yaml ps 2>/dev/null || echo "開発コンテナは未起動"
        ;;
    
    "rebuild")
        echo "🔨 開発環境を再ビルドします..."
        podman-compose -f infra/compose-data.yaml build --no-cache
        podman-compose -f infra/compose-dev.yaml build --no-cache
        echo "✅ 開発環境が再ビルドされました"
        ;;
    
    *)
        echo "使用方法: $0 {start|start-full|stop|restart|clean|logs|shell|status|rebuild}"
        echo ""
        echo "コマンド:"
        echo "  start      - データ層のみ起動（ローカル開発用）"
        echo "  start-full - フルコンテナ環境を起動"
        echo "  stop       - 開発環境を停止"
        echo "  restart    - データ層を再起動"
        echo "  clean      - 開発環境を完全削除"
        echo "  logs       - ログを表示"
        echo "  shell      - 開発コンテナに接続"
        echo "  status     - ステータス確認"
        echo "  rebuild    - イメージを再ビルド"
        echo ""
        echo "推奨: 日常開発は 'start' + ローカル実行"
        echo "      環境問題調査は 'start-full'"
        exit 1
        ;;
esac
```

## 12.4 GitHub Actions

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # TypeScript型チェック専用ジョブ
  typescript-typecheck:
    name: TypeScript Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: volta-cli/action@v4
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run type check
        run: |
          cd frontend
          npx tsc --noEmit
      - name: Check for unused exports
        run: |
          cd frontend
          npx ts-unused-exports tsconfig.json --excludePathsFromReport=src/index.tsx

  # Python型チェック専用ジョブ
  python-typecheck:
    name: Python Type Check (mypy)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Set up Python environment
        run: |
          cd backend
          uv venv
          uv pip sync requirements-dev.txt
      - name: Run mypy strict check
        run: |
          cd backend
          uv run mypy --strict .

  backend-test:
    needs: [python-typecheck]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Set up Python
        run: |
          cd backend
          uv venv
          uv pip sync requirements-dev.txt
      - name: Run tests and checks
        run: |
          cd backend
          uv run pytest --cov=app --cov-report=xml
          uv run ruff check .
          uv run mypy --strict .  # 型チェックも含める
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-test:
    needs: [typescript-typecheck]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: volta-cli/action@v4
      - run: |
          cd frontend
          npm ci
          npm run lint
          npm run type-check  # tsc --noEmit を実行
          npm run test:ci
          npm run build

  e2e-test:
    needs: [backend-test, frontend-test]
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.40.0-focal
    steps:
      - uses: actions/checkout@v4
      - name: Run E2E tests
        run: |
          docker-compose -f infra/compose.yaml up -d
          cd e2e && npm ci && npx playwright test

  build-containers:
    if: github.ref == 'refs/heads/main'
    needs: [e2e-test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker build -t ghcr.io/${{ github.repository }}/backend:${{ github.sha }} ./backend
          docker build -t ghcr.io/${{ github.repository }}/frontend:${{ github.sha }} ./frontend
          docker push ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
          docker push ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}
```

### 型チェック専用ワークフロー (オプション)

```yaml
# .github/workflows/typecheck.yml
name: Type Check

on:
  push:
    paths:
      - '**/*.py'
      - '**/*.ts'
      - '**/*.tsx'
      - 'tsconfig*.json'
      - 'pyproject.toml'
      - 'mypy.ini'
      - 'requirements*.txt'
      - 'package*.json'
  pull_request:

jobs:
  python-types:
    name: Python Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Type check with mypy
        run: |
          cd backend
          uv venv
          uv pip sync requirements-dev.txt
          uv run mypy --strict --show-error-codes --pretty .

  typescript-types:
    name: TypeScript Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: volta-cli/action@v4
      - name: Install and type check
        run: |
          cd frontend
          npm ci
          npx tsc --noEmit --pretty
          # 追加の型チェックツール
          npx tsc-strict  # より厳格なチェック（オプション）
```

### Copilot Agent Review

```yaml
# .github/workflows/copilot-review.yml
name: Copilot Agent Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Copilot Code Review
        uses: github/copilot-pr-review@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          review-checklist: |
            - コード品質
            - セキュリティ脆弱性
            - パフォーマンス最適化
            - ベストプラクティス準拠
            - テストカバレッジ
            
      - name: Post Review Summary
        uses: actions/github-script@v7
        with:
          script: |
            const { data: reviews } = await github.rest.pulls.listReviews({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number
            });
            
            const aiReview = reviews.find(r => r.user.login === 'github-actions[bot]');
            if (aiReview) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: `## 🤖 AI Review Summary\n\n${aiReview.body}`
              });
            }
```

### 自動レビュー依頼ワークフロー

```yaml
# .github/workflows/auto-review-request.yml
name: Auto Review Request

on:
  pull_request:
    types: [opened]

# チーム構成に応じて環境変数を設定
env:
  AI_REVIEWERS: 'github-copilot[bot]'
  ALL_DEVS: 'dev-1,dev-2,dev-3,tech-lead'  # チームメンバーを記載

jobs:
  add-reviewers:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            // PR作成者を取得
            const creator = context.payload.pull_request.user.login;
            const reviewers = [];
            
            // 1. Copilotが自動でレビュー
            reviewers.push(process.env.AI_REVIEWERS);
            
            // 2. 作成者以外のメンバーから1人を自動指名
            const allDevs = process.env.ALL_DEVS.split(',').map(s => s.trim());
            const availableReviewers = allDevs.filter(dev => dev !== creator);
            
            if (availableReviewers.length > 0) {
              // ランダムに1人選択（または最初の1人）
              reviewers.push(availableReviewers[0]);
            }
            
            // レビュワーを追加
            try {
              await github.rest.pulls.requestReviewers({
                owner: context.repo.owner,
                repo: context.repo.repo,
                pull_number: context.payload.pull_request.number,
                reviewers: reviewers
              });
              
              // 成功メッセージをPRにコメント
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.payload.pull_request.number,
                body: '✅ 自動レビュー依頼を送信しました\n\n' +
                      `- AIレビュー: ${process.env.AI_REVIEWERS}\n` +
                      `- 人間レビュワー: ${reviewers[1] || 'なし'}`
              });
            } catch (error) {
              console.error('レビュワー追加エラー:', error);
              // エラー時は手動対応を促す
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.payload.pull_request.number,
                body: '⚠️ 自動レビュワー追加に失敗しました。手動でレビュワーを追加してください。'
              });
            }
```

#### 設定のカスタマイズ

**小規模チーム（5人以下）の設定例：**
```yaml
env:
  AI_REVIEWERS: 'github-copilot[bot]'
  ALL_DEVS: 'dev-1,dev-2,dev-3,tech-lead'
```

**中規模チーム（10-20人）の設定例：**
```yaml
env:
  AI_REVIEWERS: 'github-copilot[bot]'
  FRONTEND_TEAM: 'fe-lead,fe-dev-1,fe-dev-2'
  BACKEND_TEAM: 'be-lead,be-dev-1,be-dev-2'
  # ラベルに応じて適切なチームを選択する処理を追加
```

#### 動作の仕組み

PRを作成すると：
1. Copilotが自動でレビュー
2. 作成者以外のメンバーから1人を自動指名

これにより：
- レビュワー指名の手間が省ける
- レビュー漏れを防げる
- AIと人間の両方のレビューを確実に受けられる

## 12.5 Pre-commit設定

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict

  # Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: [--strict, --show-error-codes]
        additional_dependencies: 
          - types-redis
          - types-passlib
          - types-python-jose
          - types-python-dateutil
          - sqlalchemy-stubs
        pass_filenames: false
        args: [backend]

  # TypeScript/JavaScript
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        types_or: [javascript, typescript, tsx, json, yaml, markdown]
        exclude: '^(backend/|e2e/playwright-report/)'

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        types: [javascript, typescript]
        additional_dependencies:
          - eslint@8.56.0
          - typescript@5.3.3
          - '@typescript-eslint/parser@6.19.0'
          - '@typescript-eslint/eslint-plugin@6.19.0'
        args: [--max-warnings=0]

  # TypeScript 型チェック
  - repo: local
    hooks:
      - id: typescript-check
        name: TypeScript Type Check
        entry: bash -c 'cd frontend && npm run type-check'
        language: system
        files: '\.(ts|tsx)'
        pass_filenames: false
```

## 12.7 Claude Code専用ヘルパースクリプト

Claude Codeからの効率的な開発を支援するため、以下のヘルパースクリプトを提供します。

### 基本ヘルパースクリプト

```bash
#!/bin/bash
# scripts/cc.sh (Claude Code Helper)
# Claude Codeから簡単にコマンドを実行するためのラッパー
# ローカル環境とコンテナ環境を自動判別

# 実行環境の判定
if [ -d "backend/.venv" ]; then
    ENV_MODE="local"
elif podman ps | grep -q myapp-dev-workspace; then
    ENV_MODE="container"
else
    ENV_MODE="none"
fi

case "$1" in
    "run")
        # Pythonスクリプト実行
        shift
        if [ "$ENV_MODE" = "local" ]; then
            cd backend && uv run python $*
        elif [ "$ENV_MODE" = "container" ]; then
            podman exec -t myapp-dev-workspace bash -c "cd /workspace && uv run python $*"
        else
            echo "❌ 開発環境が見つかりません。セットアップを実行してください。"
            exit 1
        fi
        ;;
    
    "test")
        # テスト実行
        shift
        if [ "$ENV_MODE" = "local" ]; then
            if [ -z "$1" ]; then
                cd backend && uv run pytest
            else
                uv run pytest $*
            fi
        elif [ "$ENV_MODE" = "container" ]; then
            if [ -z "$1" ]; then
                podman exec -t myapp-dev-workspace bash -c "cd /workspace/backend && uv run pytest"
            else
                podman exec -t myapp-dev-workspace bash -c "cd /workspace && uv run pytest $*"
            fi
        else
            echo "❌ 開発環境が見つかりません。"
            exit 1
        fi
        ;;
    
    "mypy")
        # 型チェック
        shift
        if [ "$ENV_MODE" = "local" ]; then
            if [ -z "$1" ]; then
                cd backend && uv run mypy --strict .
            else
                uv run mypy --strict $*
            fi
        elif [ "$ENV_MODE" = "container" ]; then
            if [ -z "$1" ]; then
                podman exec -t myapp-dev-workspace bash -c "cd /workspace/backend && uv run mypy --strict ."
            else
                podman exec -t myapp-dev-workspace bash -c "cd /workspace && uv run mypy --strict $*"
            fi
        else
            echo "❌ 開発環境が見つかりません。"
            exit 1
        fi
        ;;
    
    "install")
        # パッケージインストール
        shift
        if [ "$ENV_MODE" = "local" ]; then
            cd backend && uv pip install $*
        elif [ "$ENV_MODE" = "container" ]; then
            podman exec -t myapp-dev-workspace bash -c "cd /workspace/backend && uv pip install $*"
        else
            echo "❌ 開発環境が見つかりません。"
            exit 1
        fi
        ;;
    
    "frontend")
        # Frontend コマンド実行
        shift
        if [ "$ENV_MODE" = "local" ]; then
            cd frontend && $*
        elif [ "$ENV_MODE" = "container" ]; then
            podman exec -t myapp-dev-workspace bash -c "cd /workspace/frontend && $*"
        else
            echo "❌ 開発環境が見つかりません。"
            exit 1
        fi
        ;;
    
    "format")
        # コードフォーマット
        if [ "$ENV_MODE" = "local" ]; then
            cd backend && uv run ruff format .
            cd ../frontend && npm run format
        elif [ "$ENV_MODE" = "container" ]; then
            podman exec -t myapp-dev-workspace bash -c "cd /workspace/backend && uv run ruff format ."
            podman exec -t myapp-dev-workspace bash -c "cd /workspace/frontend && npm run format"
        else
            echo "❌ 開発環境が見つかりません。"
            exit 1
        fi
        ;;
    
    "check")
        # 全体チェック（型、リント、テスト）
        echo "🔍 Running all checks..."
        ./scripts/test.sh
        ;;
    
    "env")
        # 環境情報表示
        echo "🔍 現在の開発環境: $ENV_MODE"
        if [ "$ENV_MODE" = "local" ]; then
            echo "📍 ローカル開発環境を使用中"
            echo "   Backend: $(cd backend && uv run python --version)"
            echo "   Frontend: Node $(cd frontend && node --version)"
        elif [ "$ENV_MODE" = "container" ]; then
            echo "📍 コンテナ開発環境を使用中"
            podman exec myapp-dev-workspace bash -c "python --version && node --version"
        else
            echo "⚠️  開発環境が見つかりません"
            echo ""
            echo "セットアップ方法:"
            echo "【ローカル開発】"
            echo "  1. ./scripts/dev-env.sh start"
            echo "  2. cd backend && uv venv && uv pip sync requirements-dev.txt"
            echo "  3. cd frontend && npm install"
            echo ""
            echo "【コンテナ開発】"
            echo "  1. ./scripts/dev-env.sh start-full"
        fi
        ;;
    
    *)
        echo "Claude Code Helper - 開発環境自動判別"
        echo ""
        echo "使用方法: $0 {run|test|mypy|install|frontend|format|check|env}"
        echo ""
        echo "例:"
        echo "  $0 run backend/app/main.py          # Pythonスクリプト実行"
        echo "  $0 test                              # 全テスト実行"
        echo "  $0 test backend/tests/test_user.py   # 特定テスト実行"
        echo "  $0 mypy backend/app/models.py        # 型チェック"
        echo "  $0 install requests fastapi          # パッケージインストール"
        echo "  $0 frontend 'npm run build'          # Frontendコマンド"
        echo "  $0 format                            # コードフォーマット"
        echo "  $0 check                             # 全チェック実行"
        echo "  $0 env                               # 環境情報表示"
        echo ""
        echo "現在の環境: $ENV_MODE"
        exit 1
        ;;
esac
```

### VSCode タスク設定（Claude Code対応）

```json
// .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Python Script",
            "type": "shell",
            "command": "./scripts/cc.sh",
            "args": ["run", "${file}"],
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "presentation": {
                "reveal": "always"
            },
            "problemMatcher": "$python"
        },
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "./scripts/cc.sh",
            "args": ["test", "${file}"],
            "group": "test",
            "presentation": {
                "reveal": "always"
            }
        },
        {
            "label": "Type Check",
            "type": "shell",
            "command": "./scripts/cc.sh",
            "args": ["mypy", "${file}"],
            "group": "test",
            "presentation": {
                "reveal": "always"
            }
        },
        {
            "label": "Format Code",
            "type": "shell",
            "command": "./scripts/cc.sh",
            "args": ["format"],
            "group": "test"
        }
    ]
}
```

### Claude Code用の.bashrc設定（オプション）

```bash
# ~/.bashrc に追加（ローカルマシン）
# Claude Code用のエイリアス

# プロジェクトディレクトリでのみ有効化
if [ -f "./scripts/cc.sh" ]; then
    alias ccrun="./scripts/cc.sh run"
    alias cctest="./scripts/cc.sh test"
    alias ccmypy="./scripts/cc.sh mypy"
    alias ccinstall="./scripts/cc.sh install"
    alias ccexec="./scripts/cc.sh exec"
    
    echo "🤖 Claude Code helpers loaded!"
    echo "   ccrun <file>     - Run Python script"
    echo "   cctest [file]    - Run tests"
    echo "   ccmypy [file]    - Type check"
    echo "   ccinstall <pkg>  - Install package"
    echo "   ccexec <cmd>     - Execute command"
fi
```

## 12.8 Claude Code向け開発ガイド

### 効率的な開発フロー

1. **初期セットアップ（一度だけ）**
```bash
# 開発環境起動
./scripts/dev-env.sh start

# エイリアス設定（オプション）
echo 'alias cc="./scripts/cc.sh"' >> ~/.bashrc
source ~/.bashrc
```

2. **日常的な使用**
```bash
# スクリプト実行
./scripts/cc.sh run backend/app/main.py

# または（エイリアス設定済みの場合）
cc run backend/app/main.py

# テスト実行
cc test

# 型チェック
cc mypy backend/app/

# パッケージ追加
cc install pandas numpy
```

3. **VSCode/Claude Code統合**
- Cmd/Ctrl + Shift + B: 現在のファイルを実行
- タスクランナーから各種コマンドを選択

### トラブルシューティング

**Q: コンテナが起動していないエラー**
```bash
# 解決策
./scripts/dev-env.sh start
```

**Q: パーミッションエラー**
```bash
# scripts/cc.sh に実行権限を付与
chmod +x scripts/cc.sh
```

**Q: 実行が遅い**
```bash
# コンテナ内でインタラクティブに作業
./scripts/dev-env.sh shell
# その後、コンテナ内で直接コマンド実行
```

---

# 13. AI駆動開発（AIDD）

## 13.1 AI-Driven Development パターン

**開発フローの革新:**

```python
# 従来のTDD
1. テスト作成 → 2. 実装 → 3. リファクタリング

# AI駆動開発（AIDD）
1. 仕様プロンプト作成 → 2. AI生成+レビュー → 3. テスト自動生成 → 4. 人間による検証
```

## 13.2 具体的なAI活用パターン

### 1. コード生成フェーズ
- **ボイラープレート**: 90%自動化
- **ビジネスロジック**: 60-70%自動化
- **テストコード**: 80%自動化

### 2. セキュリティ強化フェーズ
- **脆弱性検出**: AIによる継続的スキャン
- **ペンテスト自動化**: 攻撃シナリオ生成
- **修正提案**: 即座の対策コード生成

### 3. ドキュメント生成
- **API仕様**: OpenAPI自動生成
- **アーキテクチャ図**: コードから逆生成
- **運用手順書**: 実装から自動作成

## 13.3 AI活用による工数削減効果

**工数削減効果（AI活用時）:**

| タスク | 従来手法 | AI活用 | 削減率 |
|--------|----------|---------|--------|
| API実装 | 40時間 | 10時間 | 75% |
| テスト作成 | 20時間 | 5時間 | 75% |
| ドキュメント | 16時間 | 2時間 | 87.5% |
| セキュリティ | 24時間 | 8時間 | 66.7% |
| **合計** | **100時間** | **25時間** | **75%** |

## 13.4 AI駆動開発のベストプラクティス

### プロンプトエンジニアリング

```markdown
# 効果的なプロンプトの例

## 背景
FastAPIを使用したREST APIの開発

## 要件
- User エンティティのCRUD操作
- 認証付きエンドポイント
- ページネーション対応
- 型安全性（Pydantic使用）
- 非同期処理

## 制約
- Python 3.11
- SQLAlchemy 2.0
- 既存のプロジェクト構造に従う

## 期待する出力
1. APIエンドポイント実装
2. サービスクラス
3. 単体テスト
4. 統合テスト
```

### AI生成コードのレビューチェックリスト

- [ ] セキュリティ脆弱性の確認
- [ ] 型定義の正確性
- [ ] エラーハンドリングの適切性
- [ ] パフォーマンスの考慮
- [ ] 既存パターンとの一貫性
- [ ] テストカバレッジの確認

---

# 14. 段階的移行戦略

## 14.1 Phase 1: Quick Start（Week 1-2）

```yaml
構成:
  - DB/Redis/Keycloak: コンテナ（データ層）
  - API: ローカル開発（AIで高速実装）
  - Frontend: ローカル開発（即時反映）
目的: 動くものを最速で作る

タスク:
  - 開発環境構築: 2時間（ハイブリッド構成で簡略化）
  - 基本CRUD実装: 8時間（AI活用）
  - 認証実装: 8時間（AI活用）
  - 基本UI実装: 16時間
```

## 14.2 Phase 2: Core Implementation（Week 3-8）

```yaml
実装:
  - 認証システム: AI支援で独自実装
  - 基本CRUD: FastAPIで構築
  - リアルタイム: 必要最小限から開始
重点: ビジネスロジックの実装

主要タスク:
  - ビジネスロジック実装: 80時間
  - データモデル設計: 16時間
  - API設計・実装: 40時間
  - UI/UX実装: 60時間
  - テスト作成: 40時間（AI活用で75%削減）
```

## 14.3 Phase 3: Production Preparation（Week 9-12）

```yaml
強化:
  - 完全コンテナ化オプション追加
  - セキュリティ監査（AI活用）
  - パフォーマンス最適化
  - 監視・ログ基盤

タスク:
  - セキュリティ強化: 24時間
  - パフォーマンス最適化: 16時間
  - 監視基盤構築: 24時間
  - ドキュメント整備: 8時間（AI活用）
  - 本番環境構築: 16時間
```

## 14.4 コスト効率の再定義

**TCO（Total Cost of Ownership）比較:**

```yaml
Supabase利用:
  初期コスト: 低（$25/月〜）
  開発工数: 最小
  カスタマイズコスト: 高（制限多い）
  長期運用: ベンダーロックイン

AI支援独自実装:
  初期コスト: 中（AI利用料 + 開発時間）
  開発工数: 中（AIで75%削減）
  カスタマイズコスト: 低（完全制御）
  長期運用: 自由度高い
  
ROI分岐点: 約4-6ヶ月
```

---

# 15. AI時代のセキュリティ

## 15.1 多層防御アプローチ

```python
# レイヤー1: AIによる静的解析
- コミット時の自動スキャン
- 脆弱性パターンマッチング

# レイヤー2: 実行時保護
- 自動生成されたバリデーション
- レート制限とWAF相当機能

# レイヤー3: 継続的監視
- AIによる異常検知
- 自動インシデント対応
```

## 15.2 セキュリティ実装パターン

### 入力検証の自動生成

```python
from pydantic import BaseModel, validator, Field
from typing import Optional
import re

class UserCreate(BaseModel):
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+)
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('パスワードは大文字を含む必要があります')
        if not re.search(r'[a-z]', v):
            raise ValueError('パスワードは小文字を含む必要があります')
        if not re.search(r'[0-9]', v):
            raise ValueError('パスワードは数字を含む必要があります')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('パスワードは特殊文字を含む必要があります')
        return v
```

### AIによるセキュリティレビュー自動化

```yaml
# .github/workflows/security-scan.yml
name: AI Security Scan

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  security-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: AI Security Analysis
        run: |
          # OWASP Top 10 チェック
          # SQLインジェクション検出
          # XSS脆弱性検出
          # 認証・認可の問題検出
          
      - name: Dependency Vulnerability Scan
        run: |
          # 依存関係の脆弱性スキャン
          # CVEデータベースとの照合
          # 自動修正提案
```

---

# 16. チーム開発ワークフロー

## 16.1 AI-Augmented Team Development

```yaml
Developer + AI ペアプログラミング:
  朝会:
    - AIに前日の進捗サマリー生成依頼
    - 技術的課題の解決策提案を取得
    
  実装:
    - リアルタイムコードレビュー
    - ベストプラクティス提案
    
  レビュー:
    - AI事前レビュー → 人間の最終確認
    - セキュリティ・性能の自動チェック
```

## 16.2 実装の優先順位（AI効果を考慮）

**MoSCoW with AI Impact:**

```yaml
Must Have + AI効果大:
  - 認証基盤（テンプレート豊富）
  - CRUD API（自動生成可能）
  - 基本的なテスト（AI生成容易）

Should Have + AI効果中:
  - リアルタイム機能
  - 高度な検索
  - 監視ダッシュボード

Could Have + AI効果小:
  - 特殊なビジネスロジック
  - レガシー連携
  - カスタムUI/UX
```

## 16.3 リスク管理の新アプローチ

**AI時代のリスクマトリクス:**

| リスク | 従来の影響 | AI活用時の影響 | 対策 |
|--------|-----------|----------------|------|
| スキル不足 | 高 | 低 | AIがカバー |
| セキュリティ脆弱性 | 高 | 中 | AI監査 |
| 技術的負債 | 高 | 低 | 継続的リファクタリング |
| スケーラビリティ | 中 | 低 | AI最適化提案 |

## 16.4 将来への準備

**技術進化への対応:**

```python
# アーキテクチャの柔軟性確保
class FutureProofArchitecture:
    core_principles = {
        "modular": "マイクロサービス対応可能な設計",
        "api_first": "フロントエンド技術の変更に対応",
        "ai_native": "AI機能の統合を前提",
        "observable": "監視・分析の自動化",
    }
    
    migration_ready = {
        "database": "ORMで抽象化",
        "auth": "プロバイダー交換可能",
        "storage": "S3互換API使用",
    }
```

---

# 付録A: トラブルシューティング

## よくある問題と解決方法

### Python環境の問題
```bash
# uvが見つからない
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 依存関係の競合
cd backend
rm -rf .venv
uv venv
uv pip sync requirements.txt
```

### Node.js環境の問題
```bash
# voltaが見つからない
curl https://get.volta.sh | bash
source ~/.bashrc

# node_modulesの問題
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Podmanの問題
```bash
# コンテナが起動しない
podman system prune -a
podman-compose -f infra/compose.yaml build --no-cache
podman-compose -f infra/compose.yaml up -d
```

### 型チェック関連の問題

#### Python (mypy)
```bash
# mypy エラー: モジュールが見つからない
# 解決策1: 型スタブをインストール（uvを使用）
cd backend
uv pip install types-{package-name}

# 解決策2: ignore設定を追加
# mypy.ini に以下を追加
[mypy-{module}.*]
ignore_missing_imports = True

# キャッシュの問題
uv run mypy --no-incremental .
rm -rf .mypy_cache

# uvコマンドが見つからない
# 解決策: uvを再インストール
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 仮想環境のactivateエラー
# 解決策: uvではactivateは不要
# 誤: source .venv/bin/activate && python script.py
# 正: uv run python script.py
```

#### TypeScript
```bash
# 型定義ファイルが見つからない
npm install --save-dev @types/{package-name}

# tsconfig.json の paths が機能しない
# 解決策: baseUrl を確認
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}

# 型エラーが大量に出る
# 段階的に strict オプションを有効化
{
  "compilerOptions": {
    "strict": false,  # 一時的にfalse
    "noImplicitAny": true,  # 段階的に有効化
    "strictNullChecks": true
  }
}
```

### GitHub Actions型チェックエラー
```yaml
# タイムアウトする場合
- name: Run mypy with timeout
  run: |
    timeout 300 mypy --strict .
  continue-on-error: false

# メモリ不足
- name: Type check with limited scope
  run: |
    mypy --strict app/
    mypy --strict tests/
```

### Copilot Agentレビューが動かない
- GitHub Actionsの権限設定を確認
- Settings > Actions > General > Workflow permissions
- "Read and write permissions" を選択

### 型定義の競合
```typescript
// グローバル型定義の競合
// 解決策: namespace で分離
declare namespace MyApp {
  interface User {
    id: number;
    name: string;
  }
}

// または module augmentation を使用
declare module 'my-module' {
  export interface ExistingInterface {
    newProperty: string;
  }
}
```

---

# 付録B: ベストプラクティス

## コーディング規約

### Python (Backend)
- **型ヒント必須**
  - すべての関数に引数と戻り値の型を明記
  - 変数の型も可能な限り明示
  - `Optional`, `Union`, `List`, `Dict` など適切に使用
- docstring必須（Google Style）
- 最大行長: 100文字
- import順序: 標準ライブラリ → サードパーティ → ローカル

#### Python型定義の例
```python
from typing import List, Optional, Dict, Any
from datetime import datetime

def process_user_data(
    user_id: int,
    data: Dict[str, Any],
    timestamp: Optional[datetime] = None
) -> Optional[Dict[str, Any]]:
    """
    ユーザーデータを処理する
    
    Args:
        user_id: ユーザーID
        data: 処理対象のデータ
        timestamp: タイムスタンプ（省略時は現在時刻）
        
    Returns:
        処理結果。エラー時はNone
    """
    if timestamp is None:
        timestamp = datetime.now()
    # 処理実装
    return processed_data

# 実行方法（コンテナ内）:
# cd /workspace/backend && uv run python -m module_name
```

### TypeScript (Frontend)
- **strict mode必須**
  - `tsconfig.json` で `"strict": true`
  - `noImplicitAny`, `strictNullChecks` 等すべて有効
- 型推論に頼りすぎない（明示的な型定義推奨）
- `any` 型の使用禁止（どうしても必要な場合は `unknown` を使用）
- 関数コンポーネント使用
- カスタムフックでロジック分離
- 絶対パスインポート使用

#### TypeScript型定義の例
```typescript
// 明示的な型定義
interface UserData {
  id: number;
  name: string;
  email: string;
  roles: readonly string[];  // 読み取り専用配列
  metadata?: Record<string, unknown>;  // オプショナルなメタデータ
}

// 厳格な関数型定義
type ProcessUserData = (
  userId: number,
  data: UserData,
  options?: { timestamp?: Date }
) => Promise<UserData | null>;

// ジェネリクスの活用
function processArray<T extends { id: number }>(
  items: readonly T[],
  predicate: (item: T) => boolean
): T[] {
  return items.filter(predicate);
}

// Union型とType Guardの使用
type ApiResponse<T> = 
  | { success: true; data: T }
  | { success: false; error: string };

function isSuccessResponse<T>(
  response: ApiResponse<T>
): response is { success: true; data: T } {
  return response.success === true;
}
```

## 型安全性のベストプラクティス

### 1. 境界での検証
- API レスポンスは必ず型ガードで検証
- ユーザー入力は Zod や Yup でスキーマ検証
- 外部ライブラリの戻り値も型チェック

### 2. Null安全性
- Optional Chaining (`?.`) と Nullish Coalescing (`??`) を活用
- 早期リターンで null/undefined を処理
- デフォルト値を明示的に設定

### 3. 型の再利用
- 共通の型定義は types/ ディレクトリに集約
- ユーティリティ型（Partial, Pick, Omit等）を活用
- バックエンドとフロントエンドで型定義を共有（OpenAPI等）

### 4. エラーハンドリング
- カスタムエラークラスで型安全なエラー処理
- Result型パターンの採用検討
- Never型で網羅性チェック

## Git コミット
- 1コミット1目的
- コミットメッセージは英語
- 動詞から始める（Add, Fix, Update等）
- 50文字以内（タイトル）
- 型定義の変更は別コミット

## テスト
- テストカバレッジ90%以上
- 型のテストも記述（型レベルテスト）
- E2Eテストは主要フローのみ
- モックは最小限に
- テストデータはFactoryパターン

### 型レベルテストの例
```typescript
// TypeScript
import { expectType } from 'tsd';

// 型が正しく推論されているかテスト
const result = processUserData(1, userData);
expectType<Promise<UserData | null>>(result);

// テスト実行（コンテナ内）:
// cd /workspace/frontend && npm run type-check
```

```python
# Python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 型チェック時のみ実行されるコード
    reveal_type(process_user_data)  # mypy で型を確認

# テスト実行（コンテナ内）:
# cd /workspace/backend && uv run mypy --strict module_name.py
```

## CI/CD での型チェック
- PR時に必ず型チェックを実行
- 型エラーがあればマージ不可
- 定期的に型カバレッジを計測
- 段階的な型付けの強化

---

# 付録C: 継続的改善

このドキュメントは生きたドキュメントです。以下の場合は更新してください：

1. 新しいツールやライブラリの導入
2. 開発プロセスの改善
3. よくある問題の解決方法発見
4. ベストプラクティスの発見
5. 型安全性の向上施策

## 型安全性の段階的強化

### Phase 1: 基礎的な型付け (最初の1ヶ月)
- すべての関数に基本的な型ヒント追加
- `any` 型の使用箇所を `unknown` に置換
- 明らかな型エラーの修正

### Phase 2: 厳格化 (2-3ヶ月目)
- mypy `--strict` モード有効化
- TypeScript `strict: true` 設定
- 型カバレッジ測定開始（目標: 80%）

### Phase 3: 高度な型安全性 (3ヶ月目以降)
- 型レベルテストの導入
- Branded Types や Opaque Types の活用
- 型カバレッジ90%以上達成
- ランタイム型検証の自動化

## 定期レビュー項目

- **週次**: 型エラー数の推移確認
- **月次**: 型カバレッジレポート
- **四半期**: 型定義の最適化、共通化

更新時は必ずPRを作成し、チームレビューを受けてください。

---

最終更新日: 2024-01-XX
バージョン: 2.0.0