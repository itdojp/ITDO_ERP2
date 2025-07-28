# Phase 4: Generation 実装計画

## 実装概要
Phase 3で作成した163個のテストケースをすべてグリーンにする実装を行います。

## 実装優先順位

### 1. MVP機能（最優先）
Phase 3のテストを段階的にグリーンにしていきます。

#### Step 1: 基本的なデータモデルとスキーマ
- [ ] SQLAlchemyモデル作成
  - `app/models/user.py` の拡張（MFA関連フィールド追加）
  - `app/models/session.py` （新規作成）
  - `app/models/mfa.py` （新規作成）
- [ ] Pydanticスキーマ作成
  - `app/schemas/auth.py`
  - `app/schemas/session.py`
  - `app/schemas/mfa.py`

#### Step 2: 基本認証API
- [ ] `/api/v1/auth/login` - メール/パスワードログイン
- [ ] `/api/v1/auth/logout` - ログアウト
- [ ] `/api/v1/auth/refresh` - トークンリフレッシュ
- [ ] `/api/v1/auth/me` - 現在のユーザー情報

#### Step 3: ユーザー管理API
- [ ] `/api/v1/users` - ユーザーCRUD
- [ ] `/api/v1/users/{id}/profile` - プロファイル更新
- [ ] `/api/v1/users/{id}/password` - パスワード変更

#### Step 4: セッション管理
- [ ] セッション作成・保存
- [ ] 同時セッション数制限（3セッション）
- [ ] セッションタイムアウト機能
- [ ] アイドルタイムアウト機能

### 2. 拡張機能（第2優先）

#### Step 5: Google SSO
- [ ] Google OAuth2設定
- [ ] `/api/v1/auth/google` - Google認証開始
- [ ] `/api/v1/auth/google/callback` - コールバック処理

#### Step 6: MFA実装
- [ ] TOTP生成・検証
- [ ] QRコード生成
- [ ] バックアップコード生成
- [ ] `/api/v1/auth/mfa/setup` - MFA設定
- [ ] `/api/v1/auth/mfa/verify` - MFA検証

#### Step 7: 高度なセッション機能
- [ ] `/api/v1/sessions` - セッション一覧
- [ ] `/api/v1/sessions/{id}` - セッション詳細・無効化
- [ ] `/api/v1/sessions/settings` - セッション設定

#### Step 8: パスワードリセット
- [ ] `/api/v1/auth/password-reset` - リセット要求
- [ ] `/api/v1/auth/password-reset/confirm` - リセット実行

### 3. フロントエンド実装

#### Step 9: React コンポーネント
- [ ] `LoginForm` - ログインフォーム
- [ ] `MFAForm` - MFA認証フォーム
- [ ] `SessionSettings` - セッション設定

#### Step 10: 統合とE2Eテスト
- [ ] API統合
- [ ] エラーハンドリング
- [ ] ローディング状態
- [ ] レスポンシブデザイン

## 実装方針

### TDD サイクル
1. **Red**: テストを実行し、失敗を確認
2. **Green**: 最小限のコードでテストをパス
3. **Refactor**: コードを改善（テストは維持）

### コード品質基準
- テストカバレッジ: 80%以上
- 型安全性: TypeScript/mypy strict mode
- エラーハンドリング: すべてのエラーケースを処理
- ドキュメント: OpenAPI仕様に準拠

### 実装の注意点
1. **既存コードとの整合性**
   - 既存のUserモデルを拡張（置き換えない）
   - 既存の認証フローと互換性を保つ
   - 既存のテストを壊さない

2. **セキュリティ**
   - パスワードハッシュ: bcrypt使用
   - JWT署名: HS256
   - TOTP: 60秒の時刻ずれを許容
   - セッショントークン: 暗号学的に安全な乱数

3. **パフォーマンス**
   - データベースクエリの最適化
   - 適切なインデックス設定
   - キャッシュの活用（Redis）

## 作業見積もり
- MVP機能（Step 1-4）: 4-6時間
- 拡張機能（Step 5-8）: 4-6時間
- フロントエンド（Step 9-10）: 3-4時間
- **合計**: 11-16時間

## 成功基準
- [ ] すべてのテスト（163個）がグリーン
- [ ] テストカバレッジ80%以上
- [ ] すべてのAPIエンドポイントが動作
- [ ] Lintエラーなし
- [ ] 型チェックエラーなし