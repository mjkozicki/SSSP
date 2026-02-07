#!/usr/bin/env bash
# Run from repo root: ./setup.sh [--build-docker]
# Installs Python (web) and Node (TypeScript) deps, generates benchmark dataset, optionally builds Docker images.

set -e
cd "$(dirname "$0")"
REPO_ROOT="$(pwd)"

BUILD_DOCKER=false
for arg in "$@"; do
  case "$arg" in
    --build-docker) BUILD_DOCKER=true ;;
    -h|--help)
      echo "Usage: $0 [--build-docker]"
      echo "  --build-docker  Build all sssp-bench-* Docker images (optional; can be done later via benchmark or web UI)"
      exit 0
      ;;
  esac
done

echo "== SSSP setup (from $REPO_ROOT) =="

# Python deps (web UI + benchmark scripts)
echo ""
echo "Installing Python dependencies (web/requirements.txt)..."
python3 -m pip install --user -r web/requirements.txt 2>/dev/null || pip install -r web/requirements.txt

# TypeScript deps
echo ""
echo "Installing TypeScript/Node dependencies..."
(cd typescript && npm install)

# Benchmark data dir and dataset
echo ""
echo "Generating benchmark dataset (50k-vertex graph)..."
python3 benchmark/generate_dataset.py 2>/dev/null || python benchmark/generate_dataset.py
echo "Dataset: benchmark/data/graph.txt"

# Optional: build Docker benchmark images
if "$BUILD_DOCKER"; then
  echo ""
  echo "Building Docker benchmark images (this may take a while)..."
  for lang in csharp rust cplusplus go java php python typescript; do
    echo "  Building sssp-bench-$lang..."
    docker build -f "benchmark/docker/Dockerfile.$lang" -t "sssp-bench-$lang" . --quiet 2>/dev/null || docker build -f "benchmark/docker/Dockerfile.$lang" -t "sssp-bench-$lang" .
  done
  echo "Docker images ready."
fi

echo ""
echo "Setup complete."
echo ""
echo "Next steps:"
echo "  • Run tests per language: see README.md (e.g. cd csharp && dotnet test; cd rust && cargo test; etc.)"
echo "  • Run benchmark:  python benchmark/run_benchmarks.py [--build]"
echo "  • Start web UI:   python web/app.py   (then open the URL printed)"
if ! "$BUILD_DOCKER"; then
  echo "  • Build Docker images later:  ./setup.sh --build-docker   or use the web UI / run_benchmarks.py --build"
fi
