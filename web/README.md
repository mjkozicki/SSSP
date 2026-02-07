# SSSP Benchmark Web UI

Web interface to run the benchmark test suite, view historical runs, chart metrics over time, and inspect results.

## Features

- **Run test suite** — Start the full benchmark (all languages) from the browser, with optional Docker image build. The UI uses **WebSocket** to show live progress: first “Building images” (per-language build status), then “Running tests” (per-language run status and metrics).
- **Historical test suite runs** — Table of past sessions (session id, date, languages, run count) with “View results” to load that session’s runs into the results table.
- **Metrics over time** — Three line charts: wall time (s), peak memory (MiB), and total CPU (s) by session, with one series per language.
- **Test suite results** — Session selector and table of runs: language, wall_sec, peak_mem_mb, total_cpu_sec, error.

## Requirements

- Python 3.9+
- Flask and simple-websocket (see `web/requirements.txt`)
- Benchmark SQLite DB at `benchmark/data/benchmark.db` (created when you run the benchmark harness or the web-triggered run at least once)
- Docker (required when you trigger a test run from the UI; images are built automatically if you use “Run test suite” with the default behavior)

## Run the app

From the **repo root**:

```bash
pip install -r web/requirements.txt
python web/app.py
```

The app binds to an available port and prints the URL (e.g. `Web UI available at http://localhost:54321`). Open that URL in your browser.

The app reads and writes the same SQLite database used by `benchmark/run_benchmarks.py`. Any run you start from the UI runs the harness with `--build` and `PROGRESS_URL` set so the UI receives live build and run progress over WebSocket; when the run finishes, history and charts refresh automatically.
