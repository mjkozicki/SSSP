# Run SSSP PHP (single-file implementation)
# Build context: repo root. Build: docker build -f docker/php/Dockerfile .

FROM php:8.3-cli-alpine
WORKDIR /app

COPY php/ php/
WORKDIR /app/php

# Run a quick sanity check (no built-in test runner in repo)
RUN php -r "
  require 'sssp.php';
  \$g = new Graph(2);
  \$g->addEdge(0, 1, 3.0);
  \$r = duan_mao_shu_yin(\$g, 0);
  assert(\$r->distance[0] === 0.0);
  assert(\$r->distance[1] === 3.0);
  echo 'OK';
"
