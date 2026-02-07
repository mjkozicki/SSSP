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
2. **Run the benchmark harness** as usual from the repo root:
   ```bash
   python benchmark/run_benchmarks.py --output benchmark/results.json
   ```
3. **Optional instrumentation**: To send traces or metrics from the harness or from individual language runners into SigNoz, add OpenTelemetry instrumentation and point the OTLP exporter to `http://localhost:4317` (gRPC) or `http://localhost:4318` (HTTP). SigNoz’s collector will receive the data and you can query it in the UI.

SigNoz is useful for:

- Viewing traces and service maps if you instrument the benchmark or runners with OpenTelemetry.
- Correlating runs with logs/metrics once you add exporters.
- Learning the UI and data model before instrumenting.

## Links

- [SigNoz docs](https://signoz.io/docs/)
- [OpenTelemetry instrumentation](https://signoz.io/docs/instrumentation/overview/)
