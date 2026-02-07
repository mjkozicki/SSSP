#!/usr/bin/env bash
# Install and start SigNoz locally using the official Docker setup.
# Run from benchmark/signoz. Requires Docker and Docker Compose.
# UI: http://localhost:8080

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
SIGNOZ_DIR="_signoz"

if [[ ! -d "$SIGNOZ_DIR" ]]; then
  echo "Cloning SigNoz (main branch)..."
  git clone -b main --depth 1 https://github.com/SigNoz/signoz.git "$SIGNOZ_DIR"
fi

echo "Starting SigNoz (Docker Compose)..."
cd "$SIGNOZ_DIR/deploy"
if [[ -f install.sh ]]; then
  ./install.sh
else
  cd docker
  docker compose up -d --remove-orphans
fi

echo "SigNoz is starting. Open http://localhost:8080 when containers are ready (docker ps to check)."
