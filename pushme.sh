#!/bin/bash
# pushme.sh
# Deploy the Supply Chain Portal FastAPI app to Posit Connect

set -e

# Ensure rsconnect (from pip install --user) is on PATH
export PATH="$HOME/.local/bin:$PATH"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# 1. Build frontend and bundle into backend/static
echo "Building frontend..."
cd dashboard
npm ci
npm run build
cd ..

echo "Copying frontend to backend/static..."
python backend/scripts/prepare_frontend.py

# 2. Install rsconnect package for Python
echo "Installing rsconnect-python..."
pip install rsconnect-python

# 3. Load environment variables (CONNECT_SERVER, CONNECT_API_KEY)
if [ -f .env ]; then
  echo "Loading .env..."
  set -a
  source .env
  set +a
else
  echo "Warning: .env not found. Set CONNECT_SERVER and CONNECT_API_KEY."
fi

if [ -z "$CONNECT_SERVER" ] || [ -z "$CONNECT_API_KEY" ]; then
  echo "Error: CONNECT_SERVER and CONNECT_API_KEY must be set in .env"
  echo "Example:"
  echo "  CONNECT_SERVER=https://your-connect-server.example.com"
  echo "  CONNECT_API_KEY=your_api_key"
  exit 1
fi

# 4. Deploy FastAPI app to Posit Connect
# Use Python 3.12.4 to match typical Connect server (override if your server differs)
PYTHON_VERSION="${CONNECT_PYTHON_VERSION:-3.12.4}"
echo "Deploying to Posit Connect (Python $PYTHON_VERSION)..."
rsconnect deploy fastapi \
  --server "$CONNECT_SERVER" \
  --api-key "$CONNECT_API_KEY" \
  --entrypoint main:app \
  --override-python-version "$PYTHON_VERSION" \
  backend/

echo "Deployment complete."
