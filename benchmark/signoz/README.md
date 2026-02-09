# SigNoz for local analysis

[SigNoz](https://signoz.io) is an open-source APM you can run locally to inspect traces, metrics, and logs. Use it to analyze benchmark runs or any service you instrument with OpenTelemetry.

## Prerequisites

- **Docker** and **Docker Compose**
- **4GB+ memory** allocated to Docker
- Ports **8080**, **4317**, **4318** free (UI, OTLP gRPC, OTLP HTTP)

## Quick start (from repo root)

```bash
cd benchmark/signoz
./install.sh
```

Then open **http://localhost:8080** in your browser. First load can take a minute.

To stop SigNoz:

```bash
cd benchmark/signoz/_signoz/deploy/docker
docker compose down
```

## Manual install

If you prefer not to use the script:

```bash
git clone -b main https://github.com/SigNoz/signoz.git benchmark/signoz/_signoz
cd benchmark/signoz/_signoz/deploy
./install.sh
# or: cd docker && docker compose up -d --remove-orphans
```

See [SigNoz Docker docs](https://signoz.io/docs/install/docker/) for details.

## Using SigNoz with SSSP benchmarks

1. **Run SigNoz** (as above) and leave the UI open at http://localhost:8080.
2. **Run the benchmark harness** with OTEL env set so instrumented languages send traces (from repo root):
   ```bash
   export OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4318
   export OTEL_SERVICE_NAME=sssp-bench
   python benchmark/run_benchmarks.py --output benchmark/results.json
   ```
   The harness passes all `OTEL_*` env vars into each container. Instrumented: Python, TypeScript, Go, C#, Java. Each emits one span `sssp.benchmark` with attributes `sssp.algorithm` and `sssp.iterations`. In SigNoz, open **Traces** and filter by service name.
3. **Optional**: Add instrumentation for PHP/Rust/C++ or use agents (e.g. Java agent).

## Links

- [SigNoz docs](https://signoz.io/docs/)
- [OpenTelemetry instrumentation](https://signoz.io/docs/instrumentation/overview/)
