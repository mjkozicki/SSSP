# Benchmark image: PHP runner script + sssp.php
# Build from repo root: docker build -f benchmark/docker/Dockerfile.php .

FROM php:8.3-cli-alpine
WORKDIR /app
COPY php/ php/
COPY benchmark/runners/run_php.php /app/run_php.php
ENV GRAPH_FILE=/data/graph.txt
ENV REPO_ROOT=/app
# run_php.php looks for sssp at $REPO_ROOT/php/sssp.php
ENTRYPOINT ["php", "/app/run_php.php"]
