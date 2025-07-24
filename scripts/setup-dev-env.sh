#!/bin/bash
# ITDO ERP v2 開発環境セットアップスクリプト

set -e

echo "🚀 ITDO ERP v2 開発環境セットアップを開始します..."

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 成功/失敗メッセージ
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# 1. 必須コマンドの確認
echo "📋 必須コマンドを確認中..."

check_command() {
    if command -v $1 &> /dev/null; then
        success "$1 が見つかりました"
    else
        error "$1 が見つかりません。インストールしてください。"
    fi
}

check_command git
check_command python3
check_command node
check_command npm
check_command make

# 2. Python環境のセットアップ
echo -e "\n🐍 Python環境をセットアップ中..."

# uvのインストール確認
if command -v uv &> /dev/null; then
    success "uv が見つかりました"
else
    warning "uv が見つかりません。インストールします..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Backend依存関係のインストール
if [ -d "backend" ]; then
    echo "Backend依存関係をインストール中..."
    cd backend
    uv sync || warning "Backend依存関係のインストールに失敗しました"
    cd ..
    success "Backend環境の準備完了"
else
    warning "backendディレクトリが見つかりません"
fi

# 3. Frontend環境のセットアップ
echo -e "\n⚛️ Frontend環境をセットアップ中..."

if [ -d "frontend" ]; then
    echo "Frontend依存関係をインストール中..."
    cd frontend
    npm install || warning "Frontend依存関係のインストールに失敗しました"
    cd ..
    success "Frontend環境の準備完了"
else
    warning "frontendディレクトリが見つかりません"
fi

# 4. 環境変数ファイルの作成
echo -e "\n🔧 環境変数ファイルを作成中..."

# Backend .env
if [ ! -f "backend/.env" ]; then
    cat > backend/.env << 'ENV'
DATABASE_URL=postgresql://user:password@localhost:5432/itdo_erp
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
DEBUG=true
ENV
    success "backend/.env を作成しました"
else
    warning "backend/.env は既に存在します"
fi

# Frontend .env
if [ ! -f "frontend/.env" ]; then
    cat > frontend/.env << 'ENV'
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=ITDO ERP v2
ENV
    success "frontend/.env を作成しました"
else
    warning "frontend/.env は既に存在します"
fi

# 5. Gitフックのセットアップ
echo -e "\n🔗 Gitフックをセットアップ中..."

# pre-commitフックの作成
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
# Pre-commit hook for ITDO ERP v2

echo "🔍 Pre-commit checks..."

# Backend checks
if [ -d "backend" ]; then
    cd backend
    echo "Running Python linting..."
    uv run ruff check . || exit 1
    cd ..
fi

# Frontend checks
if [ -d "frontend" ]; then
    cd frontend
    echo "Running TypeScript checks..."
    npm run lint || exit 1
    cd ..
fi

echo "✅ All checks passed!"
HOOK

chmod +x .git/hooks/pre-commit
success "Pre-commitフックを設定しました"

# 6. 開発用ディレクトリの作成
echo -e "\n📁 開発用ディレクトリを作成中..."

mkdir -p logs
mkdir -p temp
mkdir -p docs/api
mkdir -p scripts/backup

success "開発用ディレクトリを作成しました"

# 7. セットアップ完了
echo -e "\n✅ セットアップが完了しました！"
echo -e "\n📝 次のステップ:"
echo "1. データベースを起動: make start-data"
echo "2. 開発サーバーを起動: make dev"
echo "3. ブラウザで確認: http://localhost:3000"
echo -e "\n💡 ヒント: 'make help' で使用可能なコマンドを確認できます"