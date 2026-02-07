# Benchmark image: PHP runner script + sssp.php
# Build from repo root: docker build -f benchmark/docker/Dockerfile.php .
# Uses Ubuntu + apt PHP to avoid Docker Hub 500s on official php image; switch to FROM php:8.3-cli when registry is stable.

FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends php-cli && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY php/ php/
COPY benchmark/runners/run_php.php /app/run_php.php
ENV GRAPH_FILE=/data/graph.txt
ENV REPO_ROOT=/app
# run_php.php looks for sssp at $REPO_ROOT/php/sssp.php
ENTRYPOINT ["php", "/app/run_php.php"]
