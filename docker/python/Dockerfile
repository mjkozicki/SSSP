# Build and test SSSP Python package
# Build context: repo root. Build: docker build -f docker/python/Dockerfile .

FROM python:3.12-slim AS build
WORKDIR /src

# No requirements.txt; stdlib only. Copy and test.
COPY python/ python/
WORKDIR /src/python
RUN python -m py_compile graph.py sssp.py && python test_sssp.py

# Minimal runtime
FROM python:3.12-alpine AS runtime
WORKDIR /app
COPY --from=build /src/python/ .
ENV PYTHONPATH=/app
# CMD ["python", "-c", "from sssp import duan_mao_shu_yin; from graph import Graph; ..."]
