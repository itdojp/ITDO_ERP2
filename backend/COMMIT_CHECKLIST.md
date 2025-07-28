# Phase 4 コミットチェックリスト

## 📋 コミット対象ファイル一覧

### Backend - Models
- [ ] `app/models/user.py` - MFA/セッション関連フィールド追加
- [ ] `app/models/mfa.py` - 新規作成
- [ ] `app/models/session.py` - 新規作成  
- [ ] `app/models/password_reset.py` - 新規作成

### Backend - Services
- [ ] `app/services/auth.py` - 認証サービス
- [ ] `app/services/mfa_service.py` - 新規作成
- [ ] `app/services/session_service.py` - 新規作成
- [ ] `app/services/google_auth_service.py` - 新規作成
- [ ] `app/services/security_service.py` - 新規作成
- [ ] `app/services/password_reset_service.py` - 新規作成
- [ ] `app/services/email_service.py` - 新規作成

### Backend - API Endpoints
- [ ] `app/api/v1/auth.py` - 認証エンドポイント
- [ ] `app/api/v1/users.py` - ユーザー管理（既存を更新）
- [ ] `app/api/v1/sessions.py` - 新規作成
- [ ] `app/api/v1/mfa.py` - 新規作成
- [ ] `app/api/v1/security.py` - 新規作成
- [ ] `app/api/v1/password_reset.py` - 新規作成
- [ ] `app/api/v1/router.py` - ルーター更新

### Backend - Schemas
- [ ] `app/schemas/auth.py` - 認証スキーマ
- [ ] `app/schemas/user.py` - ユーザースキーマ（更新）
- [ ] `app/schemas/session.py` - 新規作成
- [ ] `app/schemas/mfa.py` - 新規作成
- [ ] `app/schemas/security.py` - 新規作成
- [ ] `app/schemas/password_reset.py` - 新規作成

### Backend - Database
- [ ] `alembic/versions/007_add_authentication_models.py` - 新規マイグレーション

### Backend - Tests
- [ ] `test_auth_api_direct.py`
- [ ] `test_auth_minimal.py`
- [ ] `test_auth_simple.py`
- [ ] `test_google_sso.py`
- [ ] `test_mfa_complete.py`
- [ ] `test_password_reset.py`
- [ ] `test_session_management.py`
- [ ] `test_user_api.py`
- [ ] `test_advanced_session.py`
- [ ] `test_phase4_summary.py`

### Frontend - Components
- [ ] `src/components/auth/LoginForm.tsx`
- [ ] `src/components/auth/RegisterForm.tsx`
- [ ] `src/components/auth/MFAVerification.tsx`
- [ ] `src/components/auth/ForgotPassword.tsx`
- [ ] `src/components/auth/ResetPassword.tsx`
- [ ] `src/components/auth/MFASetup.tsx`
- [ ] `src/components/auth/ProtectedRoute.tsx`
- [ ] `src/components/auth/SessionManager.tsx`
- [ ] `src/components/auth/SecuritySettings.tsx`
- [ ] `src/components/auth/index.ts`
- [ ] `src/components/auth/README.md`

### Frontend - Hooks & Services
- [ ] `src/hooks/useAuth.ts`
- [ ] `src/hooks/__tests__/useAuth.test.ts`

### Frontend - E2E Tests
- [ ] `e2e/tests/auth/auth-login.spec.ts`
- [ ] `e2e/tests/auth/auth-mfa.spec.ts`
- [ ] `e2e/tests/auth/auth-register.spec.ts`
- [ ] `e2e/tests/auth/auth-password-reset.spec.ts`
- [ ] `e2e/tests/auth/auth-mfa-setup.spec.ts`
- [ ] `e2e/tests/auth/auth-session-management.spec.ts`
- [ ] `e2e/tests/auth/auth-complete-flow.spec.ts`
- [ ] `e2e/tests/helpers/test-data.ts`
- [ ] `e2e/tests/helpers/auth-helper.ts`
- [ ] `e2e/tests/helpers/api-client.ts`
- [ ] `e2e/run-auth-tests.sh`

### Documentation
- [ ] `PHASE_4_COMPLETION_SUMMARY.md`
- [ ] `PHASE_4_NEXT_ACTIONS.md`
- [ ] `PHASE_4_ISSUE_REPORT.md`
- [ ] `COMMIT_CHECKLIST.md`

### Scripts
- [ ] `run-auth-integration-test.sh`

## 🔧 コミット前の確認事項

### 1. コード品質
```bash
# Backend
cd backend
uv run ruff check app/
uv run ruff format app/
uv run mypy app/ --ignore-missing-imports

# Frontend
cd frontend
npm run lint
npm run typecheck
```

### 2. テスト実行
```bash
# Backend unit tests
cd backend
uv run pytest tests/test_auth*.py -v

# Frontend tests
cd frontend
npm test
```

### 3. 環境変数テンプレート
`.env.example` に以下を追加:
```env
# Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

# Session
SESSION_TIMEOUT_MINUTES=480
REMEMBER_ME_DURATION_DAYS=30
MAX_CONCURRENT_SESSIONS=5

# MFA
MFA_ISSUER_NAME=ITDO ERP

# Security
PASSWORD_RESET_TIMEOUT_HOURS=1
ACCOUNT_LOCKOUT_THRESHOLD=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30
```

## 📝 推奨コミットメッセージ

```
feat: Implement complete authentication system (Phase 4)

- Add user authentication with email/password and Google SSO
- Implement MFA with TOTP and backup codes
- Add comprehensive session management
- Create password reset functionality
- Add risk-based authentication and security features
- Create React components for all auth flows
- Add 60+ E2E test scenarios

BREAKING CHANGE: User model schema updated with authentication fields
Closes #645
```

## ✅ 最終確認

- [ ] すべてのテストが合格している
- [ ] コード品質チェックが完了している
- [ ] ドキュメントが更新されている
- [ ] 環境変数の例が追加されている
- [ ] マイグレーションファイルが作成されている

## 🚀 次のステップ

1. 上記ファイルをコミット
2. PR作成とレビュー依頼
3. CI/CDパイプラインでのテスト確認
4. マージ後、Phase 5の準備