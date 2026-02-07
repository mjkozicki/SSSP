# SSSP Benchmark Web UI

Web interface to run the benchmark test suite, view historical runs, chart metrics over time, and inspect results.

## Features

- **Run test suite** — Start the full benchmark (all languages) from the browser. Shows status while running and disables the button until the run finishes.
- **Historical test suite runs** — Table of past sessions (session id, date, languages, run count) with “View results” to load that session’s runs into the results table.
- **Metrics over time** — Three line charts: wall time (s), peak memory (MiB), and total CPU (s) by session, with one series per language.
- **Test suite results** — Session selector and table of runs: language, wall_sec, peak_mem_mb, total_cpu_sec, error.

## Requirements

- Python 3.10+
- Flask (see `requirements.txt`)
- Benchmark SQLite DB at `benchmark/data/benchmark.db` (created when you run the benchmark harness at least once)
- Docker (only needed when you trigger a test run from the UI)

## Run the app

From the **repo root**:

```bash
pip install -r web/requirements.txt
python web/app.py
```

Then open http://localhost:{port}. (shown in console when run)

The app reads and writes the same SQLite database used by `benchmark/run_benchmarks.py`, so any run you start from the UI will appear in the history and charts after it completes.
