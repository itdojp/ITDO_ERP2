# ITDO ERP System - 開発環境構築手順書

## 概要

本手順書は、ITDO ERP Systemの開発環境を0から構築するための完全なガイドです。ハイブリッド開発環境（データ層はコンテナ、開発層はローカル実行推奨）の構築を目標とします。

**対象読者**: 生成AI、開発者
**推定作業時間**: 30-60分
**前提OS**: Linux (WSL2推奨)

## 技術スタック

- **Backend**: Python 3.11 + FastAPI + uv
- **Frontend**: React 18 + TypeScript 5 + Vite
- **Database**: PostgreSQL 15 + Redis 7
- **Authentication**: Keycloak
- **Container**: Podman/Docker
- **開発環境**: ハイブリッド構成

## 前提条件チェック

### 必須ツール

以下のツールが利用可能であることを確認してください：

```bash
# Node.js (18以上)
node --version

# Python (3.11以上) 
python3 --version

# Git
git --version

# Podman または Docker
podman --version || docker --version
```

### 追加インストールが必要なツール

以下は手順内でインストールします：
- uv (Pythonパッケージマネージャー)
- podman-compose (コンテナオーケストレーション)

## 手順1: プロジェクト基盤の準備

### 1.1 プロジェクトディレクトリ構造の作成

```bash
# プロジェクトルートに移動
cd /path/to/your/project

# 基本ディレクトリ構造を作成
mkdir -p backend/{app/{api/v1,core,models,schemas,services},tests/{unit,integration},alembic,docs}
mkdir -p frontend/{src/{components,features,hooks,services,types},tests,docs,public}
mkdir -p e2e/{tests,fixtures}
mkdir -p infra/init-scripts
mkdir -p scripts docs .github/{workflows,ISSUE_TEMPLATE} .claude
```

**説明**: 
- `backend/`: FastAPIバックエンドコード
- `frontend/`: Reactフロントエンドコード  
- `infra/`: インフラ設定（Docker Compose等）
- `scripts/`: 自動化スクリプト

### 1.2 基本設定ファイルの作成

#### .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.tox/
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/
.ruff_cache/

# Virtual Environment
.venv/
venv/
ENV/
env/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*
.pnpm-debug.log*
dist/
dist-ssr/
*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
logs/
*.log

# Database
*.db
*.sqlite3

# Testing
coverage/
.nyc_output/
test-results/
playwright-report/
playwright/.cache/

# Temporary files
tmp/
temp/
.cache/

# Build outputs
backend/dist/
frontend/build/
frontend/dist/
e2e/test-results/
e2e/playwright-report/
EOF
```

#### README.md

```bash
cat > README.md << 'EOF'
# ITDO ERP System v2

## Overview

現代的な技術スタックを使用した新世代ERPシステムです。

## Technology Stack

- **Backend**: Python 3.11 + FastAPI
- **Frontend**: React 18 + TypeScript 5
- **Database**: PostgreSQL 15
- **Cache**: Redis
- **Authentication**: Keycloak (OAuth2 / OpenID Connect)
- **Container**: Podman
- **Python Package Manager**: uv
- **Node.js Version Manager**: Volta

## Quick Start

```bash
# 1. プロジェクト初期化
./scripts/init-project.sh

# 2. データ層起動
podman-compose -f infra/compose-data.yaml up -d

# 3. 開発サーバー起動（ローカル）
# Backend
cd backend && uv run uvicorn app.main:app --reload

# Frontend (別ターミナル)
cd frontend && npm run dev
```

## Development Environment

ハイブリッド開発環境を採用：
- **データ層**: 常にコンテナで実行（PostgreSQL, Redis, Keycloak）
- **開発層**: ローカル実行推奨（高速な開発イテレーション）

## Documentation

- [Architecture](docs/architecture.md)
- [Development Guide](docs/development-guide.md)
- [API Specification](backend/docs/api-spec.md)

## License

Proprietary
EOF
```

## 手順2: Python開発環境（Backend）の構築

### 2.1 uvのインストール

```bash
# uvをインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# パスを設定
source $HOME/.local/bin/env
export PATH="$HOME/.local/bin:$PATH"

# インストール確認
uv --version
```

**説明**: uvは高速なPythonパッケージマネージャーで、従来のpip/virtualenvより効率的です。

### 2.2 Backend基本構造の作成

#### pyproject.toml

```bash
cat > backend/pyproject.toml << 'EOF'
[project]
name = "itdo-erp-backend"
version = "0.1.0"
description = "ITDO ERP System Backend"
authors = [
    {name = "ITDO Team", email = "erpdevelop@itdo.jp"},
]
dependencies = [
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.23",
    "alembic>=1.12.1",
    "psycopg2-binary>=2.9.9",
    "redis>=5.0.1",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "httpx>=0.25.2",
    "celery>=5.3.4",
    "python-keycloak>=3.7.0",
]
requires-python = ">=3.11"
readme = "README.md"
license = {text = "MIT"}

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
    "pytest-cov>=4.1.0",
    "black>=23.11.0",
    "isort>=5.12.0",
    "flake8>=6.1.0",
    "mypy>=1.7.1",
    "pre-commit>=3.5.0",
    "httpx>=0.25.2",
    "factory-boy>=3.3.0",
    "pytest-mock>=3.12.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
line_length = 88

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
addopts = "-v --cov=app --cov-report=html --cov-report=term-missing"
asyncio_mode = "auto"
EOF
```

#### Backend README.md

```bash
cat > backend/README.md << 'EOF'
# ITDO ERP Backend

FastAPI based backend for ITDO ERP System.

## Setup

```bash
uv venv
uv pip sync requirements-dev.txt
```

## Run

```bash
uv run uvicorn app.main:app --reload
```
EOF
```

### 2.3 依存関係ファイルの生成

```bash
cd backend

# 仮想環境作成
export PATH="$HOME/.local/bin:$PATH"
uv venv

# 依存関係ファイル生成
uv pip compile pyproject.toml -o requirements.txt
uv pip compile pyproject.toml --extra dev -o requirements-dev.txt

# 開発用依存関係をインストール
uv pip sync requirements-dev.txt

cd ..
```

### 2.4 Backend基本コードの作成

#### 設定ファイル (app/core/config.py)

```bash
cat > backend/app/core/config.py << 'EOF'
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ITDO ERP System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS設定
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # データベース設定
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "itdo_user"
    POSTGRES_PASSWORD: str = "itdo_password"
    POSTGRES_DB: str = "itdo_erp"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_SERVER')}:"
            f"{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
        )

    # Redis設定
    REDIS_URL: str = "redis://localhost:6379"

    # Keycloak設定
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "itdo-erp"
    KEYCLOAK_CLIENT_ID: str = "itdo-erp-client"
    KEYCLOAK_CLIENT_SECRET: str = ""

    # セキュリティ設定
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 開発環境フラグ
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
EOF
```

#### データベース接続 (app/core/database.py)

```bash
cat > backend/app/core/database.py << 'EOF'
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF
```

#### APIルーター (app/api/v1/router.py)

```bash
cat > backend/app/api/v1/router.py << 'EOF'
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db

api_router = APIRouter()


@api_router.get("/ping")
async def ping() -> dict[str, str]:
    return {"message": "pong"}


@api_router.get("/db-test")
async def db_test(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        result = db.execute(text("SELECT 1 as test")).fetchone()
        return {"status": "success", "result": result[0] if result else None}
    except Exception as e:
        return {"status": "error", "error": str(e)}
EOF
```

#### メインアプリケーション (app/main.py)

```bash
cat > backend/app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーターの登録
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "ITDO ERP System API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
EOF
```

#### __init__.pyファイル群

```bash
# 必要な__init__.pyファイルを作成
touch backend/app/__init__.py
touch backend/app/core/__init__.py
touch backend/app/api/__init__.py
touch backend/app/api/v1/__init__.py
```

## 手順3: Frontend環境の構築

### 3.1 package.json

```bash
cat > frontend/package.json << 'EOF'
{
  "name": "itdo-erp-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "coverage": "vitest run --coverage",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.1",
    "axios": "^1.6.2",
    "@tanstack/react-query": "^4.36.1",
    "react-hook-form": "^7.48.2",
    "react-table": "^7.8.0",
    "@types/react-table": "^7.7.17",
    "lucide-react": "^0.294.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "@vitejs/plugin-react": "^4.1.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.53.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.4",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "typescript": "^5.2.2",
    "vite": "^4.5.0",
    "vitest": "^0.34.6",
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^6.1.4",
    "@testing-library/user-event": "^14.5.1",
    "@vitest/ui": "^0.34.6",
    "@vitest/coverage-v8": "^0.34.6",
    "jsdom": "^22.1.0"
  },
  "volta": {
    "node": "18.18.2",
    "npm": "9.8.1"
  }
}
EOF
```

**重要**: `@tanstack/react-query`を使用（react-queryは非推奨）

### 3.2 TypeScript設定

#### tsconfig.json

```bash
cat > frontend/tsconfig.json << 'EOF'
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

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    /* Path mapping */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src", "vite.config.ts"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF
```

#### tsconfig.node.json

```bash
cat > frontend/tsconfig.node.json << 'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOF
```

### 3.3 Vite設定

```bash
cat > frontend/vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
EOF
```

### 3.4 TailwindCSS設定

```bash
cat > frontend/tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF
```

```bash
cat > frontend/postcss.config.js << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF
```

### 3.5 Frontend基本コードの作成

#### index.html

```bash
cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ITDO ERP System</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF
```

#### src/main.tsx

```bash
cat > frontend/src/main.tsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOF
```

#### src/App.tsx

```bash
cat > frontend/src/App.tsx << 'EOF'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { HomePage } from '@/pages/HomePage'
import './App.css'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  )
}

export default App
EOF
```

#### CSS設定

```bash
cat > frontend/src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
EOF
```

```bash
touch frontend/src/App.css
```

#### コンポーネントとサービス

```bash
cat > frontend/src/components/Layout.tsx << 'EOF'
import { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold">ITDO ERP System</h1>
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}
EOF
```

```bash
cat > frontend/src/pages/HomePage.tsx << 'EOF'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/services/api'

export function HomePage() {
  const { data, isLoading, error } = useQuery(
    'health-check',
    () => apiClient.get('/health')
  )

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error connecting to backend</div>

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
        <h2 className="text-2xl font-bold mb-4">Welcome to ITDO ERP System</h2>
        <p className="text-gray-600 mb-4">
          Backend connection status: {data?.data?.status || 'Unknown'}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-2">Module 1</h3>
            <p className="text-gray-600">Coming soon...</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-2">Module 2</h3>
            <p className="text-gray-600">Coming soon...</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-2">Module 3</h3>
            <p className="text-gray-600">Coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  )
}
EOF
```

```bash
cat > frontend/src/services/api.ts << 'EOF'
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
EOF
```

#### テスト設定

```bash
mkdir -p frontend/src/test
cat > frontend/src/test/setup.ts << 'EOF'
import '@testing-library/jest-dom'
EOF
```

### 3.6 Frontend依存関係のインストール

```bash
cd frontend
npm install
cd ..
```

## 手順4: データ層（コンテナ）の構築

### 4.1 podman-composeのインストール

```bash
export PATH="$HOME/.local/bin:$PATH"
uv tool install podman-compose
```

**説明**: podman-composeはDocker Composeと互換性のあるPodman用ツールです。

### 4.2 Docker Compose設定（データ層）

```bash
cat > infra/compose-data.yaml << 'EOF'
version: '3.8'

services:
  postgres:
    image: docker.io/postgres:15-alpine
    container_name: itdo-postgres
    environment:
      POSTGRES_DB: itdo_erp
      POSTGRES_USER: itdo_user
      POSTGRES_PASSWORD: itdo_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - itdo-network
    restart: unless-stopped

  redis:
    image: docker.io/redis:7-alpine
    container_name: itdo-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - itdo-network
    restart: unless-stopped
    command: redis-server --appendonly yes

  keycloak:
    image: quay.io/keycloak/keycloak:latest
    container_name: itdo-keycloak
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak_db
      KC_DB_USERNAME: keycloak_user
      KC_DB_PASSWORD: keycloak_password
    ports:
      - "8080:8080"
    depends_on:
      - postgres
    networks:
      - itdo-network
    restart: unless-stopped
    command: start-dev

  pgadmin:
    image: docker.io/dpage/pgadmin4:latest
    container_name: itdo-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: erpdevelop@itdo.jp
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "8081:80"
    depends_on:
      - postgres
    networks:
      - itdo-network
    restart: unless-stopped
    volumes:
      - pgadmin_data:/var/lib/pgadmin

volumes:
  postgres_data:
  redis_data:
  pgadmin_data:

networks:
  itdo-network:
    driver: bridge
EOF
```

**重要**: 
- イメージ名は完全修飾名を使用（docker.io/postgres:15-alpine等）
- Podmanでのレジストリ解決問題を回避

### 4.3 データベース初期化スクリプト

```bash
cat > infra/init-scripts/init-keycloak-db.sql << 'EOF'
-- Keycloak用のデータベースとユーザーを作成
CREATE DATABASE keycloak_db;
CREATE USER keycloak_user WITH PASSWORD 'keycloak_password';
GRANT ALL PRIVILEGES ON DATABASE keycloak_db TO keycloak_user;
EOF
```

### 4.4 開発用Docker Compose設定（フルコンテナオプション）

```bash
cat > infra/compose-dev.yaml << 'EOF'
version: '3.8'

services:
  # データ層（compose-data.yamlと同じ）
  postgres:
    image: docker.io/postgres:15-alpine
    container_name: itdo-postgres-dev
    environment:
      POSTGRES_DB: itdo_erp
      POSTGRES_USER: itdo_user
      POSTGRES_PASSWORD: itdo_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - itdo-network-dev
    restart: unless-stopped

  redis:
    image: docker.io/redis:7-alpine
    container_name: itdo-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data_dev:/data
    networks:
      - itdo-network-dev
    restart: unless-stopped
    command: redis-server --appendonly yes

  keycloak:
    image: quay.io/keycloak/keycloak:latest
    container_name: itdo-keycloak-dev
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak_db
      KC_DB_USERNAME: keycloak_user
      KC_DB_PASSWORD: keycloak_password
    ports:
      - "8080:8080"
    depends_on:
      - postgres
    networks:
      - itdo-network-dev
    restart: unless-stopped
    command: start-dev

  # 開発環境用ワークスペース
  workspace:
    build:
      context: ..
      dockerfile: infra/Dockerfile.dev
    container_name: itdo-workspace-dev
    volumes:
      - ../:/workspace
      - node_modules:/workspace/frontend/node_modules
      - python_cache:/workspace/backend/.venv
    working_dir: /workspace
    ports:
      - "3000:3000"  # React dev server
      - "8000:8000"  # FastAPI
      - "8001:8001"  # FastAPI docs
    depends_on:
      - postgres
      - redis
      - keycloak
    networks:
      - itdo-network-dev
    environment:
      - DATABASE_URL=postgresql://itdo_user:itdo_password@postgres:5432/itdo_erp
      - REDIS_URL=redis://redis:6379
      - KEYCLOAK_URL=http://keycloak:8080
    stdin_open: true
    tty: true
    command: sleep infinity

volumes:
  postgres_data_dev:
  redis_data_dev:
  node_modules:
  python_cache:

networks:
  itdo-network-dev:
    driver: bridge
EOF
```

### 4.5 開発用Dockerfile

```bash
cat > infra/Dockerfile.dev << 'EOF'
FROM python:3.11-slim

# システムパッケージの更新とNode.js 18のインストール
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# uvのインストール
RUN pip install uv

# 作業ディレクトリの設定
WORKDIR /workspace

# Python依存関係のインストール用のキャッシュ層
COPY backend/pyproject.toml backend/requirements*.txt ./backend/
RUN cd backend && uv venv && uv pip sync requirements-dev.txt

# Node.js依存関係のインストール用のキャッシュ層
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci

# 開発用のエントリーポイント
COPY infra/docker-entrypoint-dev.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint-dev.sh

# デフォルトコマンド
CMD ["docker-entrypoint-dev.sh"]
EOF
```

```bash
cat > infra/docker-entrypoint-dev.sh << 'EOF'
#!/bin/bash
set -e

echo "開発環境の初期化を開始します..."

# データベースの接続待機
echo "データベース接続を待機中..."
until nc -z postgres 5432; do
    echo "PostgreSQLの起動を待機中..."
    sleep 2
done

echo "Redis接続を待機中..."
until nc -z redis 6379; do
    echo "Redisの起動を待機中..."
    sleep 2
done

echo "Keycloak接続を待機中..."
until nc -z keycloak 8080; do
    echo "Keycloakの起動を待機中..."
    sleep 2
done

echo "全サービスが利用可能になりました。"
echo "開発環境の準備が完了しました。"
echo ""
echo "利用可能なコマンド:"
echo "  make dev        - 開発サーバーを起動"
echo "  make test       - テストを実行"
echo "  make lint       - リントを実行"
echo "  make typecheck  - 型チェックを実行"
echo ""

# シェルを開始
exec "$@"
EOF

chmod +x infra/docker-entrypoint-dev.sh
```

## 手順5: 自動化スクリプトの作成

### 5.1 プロジェクト初期化スクリプト

```bash
cat > scripts/init-project.sh << 'EOF'
#!/bin/bash

# ITDO ERP System - Project Initialization Script
# This script initializes the development environment

set -e

echo "🚀 ITDO ERP System プロジェクト初期化開始"

# Check if running in correct directory
if [ ! -f "README.md" ]; then
    echo "❌ エラー: プロジェクトルートディレクトリで実行してください"
    exit 1
fi

# Check requirements
echo "📋 必要なツールの確認中..."

# Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ エラー: uv がインストールされていません"
    echo "インストール方法: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check podman or docker
if ! command -v podman &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ エラー: podman または docker がインストールされていません"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ エラー: Node.js がインストールされていません"
    echo "推奨: Volta を使用してインストール"
    exit 1
fi

echo "✅ 必要なツールが確認されました"

# Backend setup
echo "🐍 Backend環境のセットアップ中..."
cd backend

# Create virtual environment
echo "Python仮想環境を作成中..."
uv venv

# Install dependencies
echo "Python依存関係をインストール中..."
uv pip sync requirements-dev.txt 2>/dev/null || echo "requirements.txt が見つかりません。後でインストールしてください。"

cd ..

# Frontend setup
echo "⚛️ Frontend環境のセットアップ中..."
cd frontend

# Install dependencies
echo "Node.js依存関係をインストール中..."
npm install

cd ..

# Create environment file
echo "🔧 環境設定ファイルを作成中..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Development Environment Configuration
DEBUG=true

# Database Configuration
DATABASE_URL=postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp
POSTGRES_SERVER=localhost
POSTGRES_USER=itdo_user
POSTGRES_PASSWORD=itdo_password
POSTGRES_DB=itdo_erp

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Keycloak Configuration
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=itdo-erp
KEYCLOAK_CLIENT_ID=itdo-erp-client
KEYCLOAK_CLIENT_SECRET=

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Frontend API URL
VITE_API_URL=http://localhost:8000
EOF
    echo "✅ .env ファイルを作成しました"
else
    echo "ℹ️  .env ファイルは既に存在します"
fi

# Create Makefile
echo "📝 Makefile を作成中..."
cat > Makefile << 'MAKEFILE_EOF'
.PHONY: help dev test lint typecheck clean

help:
	@echo "利用可能なコマンド:"
	@echo "  make dev        - 開発サーバーを起動"
	@echo "  make test       - テストを実行"
	@echo "  make lint       - リントを実行"
	@echo "  make typecheck  - 型チェックを実行"
	@echo "  make clean      - 一時ファイルを削除"

dev:
	@echo "開発サーバーを起動中..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "停止するには Ctrl+C を押してください"
	@(cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

test:
	@echo "バックエンドテストを実行中..."
	@cd backend && uv run pytest
	@echo "フロントエンドテストを実行中..."
	@cd frontend && npm test

lint:
	@echo "バックエンドリントを実行中..."
	@cd backend && uv run black . && uv run isort .
	@echo "フロントエンドリントを実行中..."
	@cd frontend && npm run lint

typecheck:
	@echo "バックエンド型チェックを実行中..."
	@cd backend && uv run mypy --strict .
	@echo "フロントエンド型チェックを実行中..."
	@cd frontend && npm run typecheck

clean:
	@echo "一時ファイルを削除中..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf backend/.pytest_cache frontend/node_modules/.cache
MAKEFILE_EOF

echo "✅ Makefile を作成しました"

echo ""
echo "🎉 プロジェクト初期化が完了しました！"
echo ""
echo "次のステップ:"
echo "1. データ層を起動: podman-compose -f infra/compose-data.yaml up -d"
echo "2. 開発サーバーを起動: make dev"
echo "3. ブラウザで http://localhost:3000 にアクセス"
echo ""
echo "その他のコマンド:"
echo "  make help  - 利用可能なコマンドを表示"
echo "  make test  - テストを実行"
echo "  make lint  - コードフォーマットを実行"
echo ""
EOF

chmod +x scripts/init-project.sh
```

### 5.2 開発環境管理スクリプト

```bash
cat > scripts/dev-env.sh << 'EOF'
#!/bin/bash

# ITDO ERP System - Development Environment Management Script
# This script manages the development environment containers

set -e

COMPOSE_FILE="infra/compose-data.yaml"
DEV_COMPOSE_FILE="infra/compose-dev.yaml"

usage() {
    echo "Usage: $0 {start|stop|restart|logs|shell|status|full-start|full-stop}"
    echo ""
    echo "Commands:"
    echo "  start       - データ層のみ起動 (推奨)"
    echo "  stop        - データ層のみ停止"
    echo "  restart     - データ層の再起動"
    echo "  logs        - ログを表示"
    echo "  shell       - データベースシェルに接続"
    echo "  status      - コンテナの状態を確認"
    echo "  full-start  - フルコンテナ開発環境を起動"
    echo "  full-stop   - フルコンテナ開発環境を停止"
    echo ""
    echo "推奨開発フロー:"
    echo "1. ./scripts/dev-env.sh start"
    echo "2. make dev (別ターミナル)"
    exit 1
}

start_data_layer() {
    echo "🐘 データ層を起動中..."
    podman-compose -f $COMPOSE_FILE up -d
    echo "✅ データ層が起動しました"
    echo ""
    echo "利用可能なサービス:"
    echo "  PostgreSQL: localhost:5432"
    echo "  Redis: localhost:6379"
    echo "  Keycloak: http://localhost:8080"
    echo "  PgAdmin: http://localhost:8081"
    echo ""
    echo "次のステップ: make dev で開発サーバーを起動"
}

stop_data_layer() {
    echo "🛑 データ層を停止中..."
    podman-compose -f $COMPOSE_FILE down
    echo "✅ データ層が停止しました"
}

restart_data_layer() {
    echo "🔄 データ層を再起動中..."
    podman-compose -f $COMPOSE_FILE restart
    echo "✅ データ層が再起動しました"
}

show_logs() {
    echo "📋 ログを表示中..."
    podman-compose -f $COMPOSE_FILE logs -f
}

connect_db_shell() {
    echo "🐘 PostgreSQL シェルに接続中..."
    podman exec -it itdo-postgres psql -U itdo_user -d itdo_erp
}

show_status() {
    echo "📊 コンテナの状態:"
    podman-compose -f $COMPOSE_FILE ps
}

start_full_dev() {
    echo "🚀 フルコンテナ開発環境を起動中..."
    podman-compose -f $DEV_COMPOSE_FILE up -d
    echo "✅ フルコンテナ開発環境が起動しました"
    echo ""
    echo "利用可能なサービス:"
    echo "  PostgreSQL: localhost:5432"
    echo "  Redis: localhost:6379"
    echo "  Keycloak: http://localhost:8080"
    echo "  Development Workspace: podman exec -it itdo-workspace-dev bash"
    echo ""
    echo "ワークスペースに接続: ./scripts/dev-env.sh shell"
}

stop_full_dev() {
    echo "🛑 フルコンテナ開発環境を停止中..."
    podman-compose -f $DEV_COMPOSE_FILE down
    echo "✅ フルコンテナ開発環境が停止しました"
}

connect_dev_shell() {
    echo "🐚 開発ワークスペースに接続中..."
    podman exec -it itdo-workspace-dev bash
}

case "${1:-}" in
    start)
        start_data_layer
        ;;
    stop)
        stop_data_layer
        ;;
    restart)
        restart_data_layer
        ;;
    logs)
        show_logs
        ;;
    shell)
        if podman ps --format "table {{.Names}}" | grep -q "itdo-workspace-dev"; then
            connect_dev_shell
        else
            connect_db_shell
        fi
        ;;
    status)
        show_status
        ;;
    full-start)
        start_full_dev
        ;;
    full-stop)
        stop_full_dev
        ;;
    *)
        usage
        ;;
esac
EOF

chmod +x scripts/dev-env.sh
```

## 手順6: GitHub関連設定

### 6.1 Issueテンプレート

```bash
cat > .github/ISSUE_TEMPLATE/feature_request.md << 'EOF'
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
EOF
```

```bash
cat > .github/ISSUE_TEMPLATE/bug_report.md << 'EOF'
---
name: バグレポート
about: バグや不具合の報告
title: ''
labels: 'bug'
assignees: ''
---

## 概要
<!-- バグの簡潔な説明 -->

## 再現手順
<!-- バグを再現する手順 -->
1. 
2. 
3. 

## 期待される動作
<!-- 本来どのように動作すべきか -->

## 実際の動作
<!-- 実際にどのような動作になったか -->

## 環境
- OS: 
- ブラウザ: 
- Node.js: 
- Python: 

## スクリーンショット
<!-- エラー画面などのスクリーンショット -->

## ログ
<!-- 関連するエラーログなど -->
```
ログを貼り付け
```

## その他
<!-- その他の情報 -->
EOF
```

### 6.2 PRテンプレート

```bash
cat > .github/pull_request_template.md << 'EOF'
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
EOF
```

## 手順7: 環境設定ファイル

### 7.1 環境変数設定

```bash
cat > .env.example << 'EOF'
# Development Environment Configuration
DEBUG=true

# Database Configuration
DATABASE_URL=postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp
POSTGRES_SERVER=localhost
POSTGRES_USER=itdo_user
POSTGRES_PASSWORD=itdo_password
POSTGRES_DB=itdo_erp

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Keycloak Configuration
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=itdo-erp
KEYCLOAK_CLIENT_ID=itdo-erp-client
KEYCLOAK_CLIENT_SECRET=

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Frontend API URL
VITE_API_URL=http://localhost:8000
EOF
```

## 手順8: 環境構築の実行

### 8.1 初期化スクリプトの実行

```bash
# スクリプトに実行権限を付与
chmod +x scripts/*.sh

# プロジェクト初期化を実行
./scripts/init-project.sh
```

### 8.2 データ層の起動

```bash
# データ層コンテナを起動
export PATH="$HOME/.local/bin:$PATH"
podman-compose -f infra/compose-data.yaml up -d

# 起動状態を確認
podman-compose -f infra/compose-data.yaml ps
```

### 8.3 開発サーバーの起動

```bash
# バックエンドサーバーを起動（ターミナル1）
cd backend && uv run uvicorn app.main:app --reload

# フロントエンドサーバーを起動（ターミナル2）
cd frontend && npm run dev

# または Makefileを使用
make dev
```

## 手順9: 動作確認

### 9.1 データ層の確認

```bash
# PostgreSQL接続テスト
podman exec -it itdo-postgres psql -U itdo_user -d itdo_erp -c "SELECT version();"

# Redis接続テスト
podman exec -it itdo-redis redis-cli ping
```

### 9.2 Backend API の確認

```bash
# 基本エンドポイント
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/ping
curl http://localhost:8000/api/v1/db-test
```

### 9.3 Frontend の確認

ブラウザで以下にアクセス：
- Frontend: http://localhost:3000
- Backend API Docs: http://localhost:8000/api/v1/docs
- PgAdmin: http://localhost:8081 (erpdevelop@itdo.jp / admin)
- Keycloak: http://localhost:8080 (admin / admin)

## トラブルシューティング

### よくある問題と解決方法

#### 1. uvが見つからない
```bash
# PATH設定が不足している場合
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

#### 2. podman-compose が見つからない
```bash
# uvでインストール
uv tool install podman-compose
```

#### 3. イメージプルエラー
```bash
# 完全修飾名を使用
# ❌ postgres:15-alpine
# ✅ docker.io/postgres:15-alpine
```

#### 4. pydantic設定エラー
```bash
# BaseSettingsは pydantic_settings からインポート
from pydantic_settings import BaseSettings
```

#### 5. Frontend依存関係エラー
```bash
# react-query は非推奨、@tanstack/react-query を使用
npm install @tanstack/react-query
```

#### 6. ポート競合
```bash
# 使用中のポートを確認
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :3000
```

## 次のステップ

環境構築完了後の開発フロー：

1. **Issue作成**: 新機能やバグ修正のためのIssue
2. **Draft PR作成**: 作業開始時にDraft PRを作成
3. **開発作業**: ローカル環境で開発
4. **テスト実行**: `make test` でテストを実行
5. **コード品質チェック**: `make lint && make typecheck`
6. **PR準備**: Draft解除してレビュー依頼

## 最終確認チェックリスト

- [ ] 全依存関係がインストール済み
- [ ] データ層コンテナが起動中
- [ ] Backend APIが応答
- [ ] Frontend アプリケーションが表示
- [ ] データベース接続が正常
- [ ] 開発用スクリプトが実行可能
- [ ] 環境変数ファイルが設定済み
- [ ] GitHub関連ファイルが配置済み

---

**構築完了！** 本格的な開発作業を開始できます。