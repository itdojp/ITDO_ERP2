#!/bin/bash
# Setup environment for ITDO ERP Backend

echo "Setting up ITDO ERP Backend environment..."

# Ensure uv is in PATH
if ! command -v uv &> /dev/null; then
    echo "Adding uv to PATH..."
    export PATH="$HOME/.local/bin:$PATH"
fi

# Verify uv is working
if command -v uv &> /dev/null; then
    echo "✓ uv is available (version: $(uv --version))"
else
    echo "✗ uv not found. Please install uv first."
    exit 1
fi

# Setup virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Install dependencies
echo "Installing dependencies..."
uv pip sync requirements-dev.txt

# Setup environment variables
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env with your configuration"
fi

echo "✓ Environment setup complete!"
echo ""
echo "To activate the environment in your shell:"
echo "  source ~/.local/bin/env"
echo ""
echo "To run the application:"
echo "  uv run uvicorn app.main:app --reload"
echo ""
echo "To run tests:"
echo "  uv run pytest"