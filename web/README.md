# SSSP Benchmark Web UI

Web interface to run the benchmark test suite, view historical runs, chart metrics over time, and inspect results.

## Features

- **Run test suite** — Start the full benchmark (all languages) from the browser, with optional Docker image build. Before running you can choose:
  - **Algorithm** — Duan–Mao–Shu–Yin or Dijkstra (passed to the harness as `--algorithm`).
  - **Timed run (≥10 s)** — When enabled, each language runs repeated SSSP iterations for at least 10 seconds (passed as `--min-seconds 10`) for more stable timing.
  The UI uses **WebSocket** to show live progress: first “Building images” (per-language build status), then “Running tests” (per-language run status and metrics).
- **Historical test suite runs** — Table of past sessions (session id, date, **algorithm**, languages, run count) with “View results” to load that session’s runs into the results table.
- **Metrics over time** — Three line charts: wall time (s), peak memory (MiB), and total CPU (s) by session, with one series per language.
- **Test suite results** — Session selector and table of runs: language, wall_sec, peak_mem_mb, total_cpu_sec, **runs** (iteration count for timed runs), error.

## Metrics explained

The UI and charts show the same metrics the harness collects from each Docker run (via `docker stats` and wall-clock timing):

| Metric | Meaning |
|--------|--------|
| **Wall time (s)** | Total **elapsed (wall-clock) time** for that language’s benchmark run. From container start until the process exits. Lower is better. |
| **Peak memory (MiB)** | **Maximum memory** (RSS) used by the container during the run, in **mebibytes** (MiB). Sampled periodically; the peak over the run is stored. Lower is better for memory use. |
| **Total CPU (s)** | **Integrated CPU time** over the run: the harness samples the container’s CPU% at an interval (e.g. 0.5 s), then approximates total CPU seconds as the area under that curve. Can exceed wall time on multi-core systems (e.g. 200% CPU → 2 s CPU per 1 s wall). Indicates how much CPU work the run used. |
| **Runs** | For **timed runs** (when "Timed run (≥10 s)" was enabled), the number of SSSP iterations completed in that run. Shown as "—" for single-run (non-timed) sessions. |
| **Error** | If the run failed (non-zero exit, timeout, or crash), the error message or exit details are shown here; successful runs show “—”. |

Charts plot these metrics **by session** (one point per language per session), so you can compare languages and see how metrics change across runs (e.g. after code changes or with “Timed run” enabled).

## Requirements

- Python 3.9+
- Flask and simple-websocket (see `web/requirements.txt`)
- Node.js 18+ and npm (for building the Astro frontend)
- Benchmark SQLite DB at `benchmark/data/benchmark.db` (created when you run the benchmark harness or the web-triggered run at least once)
- Docker (required when you trigger a test run from the UI; images are built automatically if you use “Run test suite” with the default behavior)

## Run the app

The UI is an **Astro** static frontend; Flask serves it from `web/dist/` when that build exists.

**Production (recommended):** build the frontend, then start Flask. From the **repo root**:

```bash
pip install -r web/requirements.txt
cd web && npm install && npm run build && cd ..
python web/app.py
```

The app binds to an available port and prints the URL (e.g. `Web UI available at http://localhost:54321`). Open that URL in your browser.

If you run `python web/app.py` without building the Astro app, Flask returns a 503 with instructions to run `npm run build` in `web/`.

**Frontend-only dev:** from `web/` run `npm run dev` for the Astro dev server. To use the API and WebSocket, run Flask as above (with `npm run build` first) and open the app via the Flask URL.

The app reads and writes the same SQLite database used by `benchmark/run_benchmarks.py`. Any run you start from the UI runs the harness with `--build`, the selected **algorithm** (`--algorithm dijkstra` or `--algorithm duan_mao_shu_yin`), optional **`--min-seconds 10`** when “Timed run (≥10 s)” is checked, and `PROGRESS_URL` set so the UI receives live build and run progress over WebSocket; when the run finishes, history and charts refresh automatically.
