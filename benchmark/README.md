# SSSP Benchmark

Benchmark harness that runs an SSSP implementation (Duan–Mao–Shu–Yin or Dijkstra) in each language inside Docker and collects:

- **Overall user runtime** — wall clock time (seconds)
- **Peak memory allocation** — maximum RSS (MiB) during the run
- **Sum of total CPU time over all threads** — CPU seconds (from `docker stats` CPU% integrated over time)
- **Individual CPU utilization** — time series of `(elapsed_sec, cpu_pct, mem_mb)` samples

## Dataset

The benchmark uses a **50k-vertex graph** that emulates a globally distributed network:

- **50,000 servers** (vertices)
- **~20 regions** (e.g. data centers / continents)
- **Intra-region edges:** 2–8 per node, latency 0.5–5 ms
- **Inter-region edges:** 0–2 per node, latency 20–150 ms
- **Deterministic** (seed=42) so all languages run on the same graph

### Generate the dataset

From the repo root:

```bash
python benchmark/generate_dataset.py
```

This writes `benchmark/data/graph.txt` (format: first line `n m`, then `m` lines `u v weight`).

## Build benchmark images

From the repo root, build all benchmark images (optional; the harness can do this with `--build`):

```bash
for lang in csharp rust cplusplus go java php python typescript; do
  docker build -f benchmark/docker/Dockerfile.$lang -t sssp-bench-$lang .
done
```

## Run the harness

From the repo root:

```bash
# Generate dataset (if missing), then run each language sequentially and write results
python benchmark/run_benchmarks.py --build --output benchmark/results.json

# Without rebuilding images (use existing sssp-bench-* images)
python benchmark/run_benchmarks.py --output benchmark/results.json

# Choose algorithm: Dijkstra or Duan–Mao–Shu–Yin (default)
python benchmark/run_benchmarks.py --algorithm dijkstra --output benchmark/results.json

# Timed run: repeat SSSP iterations for at least 10 seconds per language (for stable timing)
python benchmark/run_benchmarks.py --min-seconds 10 --output benchmark/results.json

# Run only one language
python benchmark/run_benchmarks.py --lang rust --output benchmark/results.json
```

**CLI options:**

| Option | Description |
|--------|-------------|
| `--build` | Build all benchmark Docker images before running. |
| `--algorithm {dijkstra\|duan_mao_shu_yin}` | SSSP algorithm to run (default: `duan_mao_shu_yin`). |
| `--min-seconds SEC` | Run repeated iterations until at least *SEC* seconds have elapsed per language (default: 0 = single run). |
| `--lang <lang>` | Run only this language (e.g. `rust`, `python`). |
| `--timeout N` | Timeout per run in seconds (default: 600). |
| `--output FILE` | Write JSON results to *FILE* (default: `benchmark/results.json`). Use `--no-json` to skip. |
| `--progress-url URL` | Base URL for progress POSTs (used when started from the web UI). |

**Requirements:** Docker, Python 3. The harness will:

1. Ensure `benchmark/data/graph.txt` exists (run `generate_dataset.py` if not).
2. Optionally build each `sssp-bench-<lang>` image (if `--build`); when started from the **web UI** with progress URL set, the UI receives live “building” / “built” events per language.
3. For each language: run `docker run -d -v benchmark/data:/data:ro ... sssp-bench-<lang> /data/graph.txt`, sample `docker stats` every 0.5s, then `docker wait`. If `PROGRESS_URL` is set (e.g. when started from the web UI), the harness POSTs “started” / “completed” per language so the UI can show live run progress.
4. Store results in **benchmark/data/benchmark.db** (SQLite) and optionally write **benchmark/results.json** (use `--no-json` to skip JSON).
   - `wall_sec` — wall clock time
   - `peak_mem_mb` — peak memory (MiB)
   - `total_cpu_sec` — integrated CPU time (seconds)
   - `cpu_utilization` — list of `{elapsed_sec, cpu_pct, mem_mb}` for plotting

## Container environment

Each benchmark container receives:

- **`GRAPH_FILE`** — path to the graph file (e.g. `/data/graph.txt`).
- **`SSSP_ALGORITHM`** — `dijkstra` or `duan_mao_shu_yin` (which SSSP to run).
- **`SSSP_MIN_SECONDS`** — when set to a positive number, the runner repeats SSSP(0) until wall-clock time ≥ that many seconds, then prints `DONE n reachable iterations`; otherwise it runs once and prints `DONE n reachable`.

## SQLite results

The harness writes every run into **benchmark/data/benchmark.db**:

- **sessions** — one row per full benchmark run: `created_at`, `languages`, `algorithm` (e.g. `dijkstra` or `duan_mao_shu_yin`).
- **runs** — one row per language: `session_id`, `language`, `wall_sec`, `peak_mem_mb`, `total_cpu_sec`, `error` (if any).
- **utilization** — time series per run: `run_id`, `elapsed_sec`, `cpu_pct`, `mem_mb`.

Example query for the latest run:

```sql
SELECT r.language, r.wall_sec, r.peak_mem_mb, r.total_cpu_sec
FROM runs r
JOIN sessions s ON r.session_id = s.id
ORDER BY s.id DESC
LIMIT 10;
```

## Results format (JSON)

Example `results.json`:

```json
{
  "rust": {
    "wall_sec": 12.345,
    "peak_mem_mb": 256.5,
    "total_cpu_sec": 11.2,
    "cpu_utilization": [
      {"elapsed_sec": 0.5, "cpu_pct": 98.0, "mem_mb": 120.0},
      ...
    ]
  },
  ...
}
```

## Runners and Dockerfiles

- **Runners:** Each implementation has a benchmark entrypoint that reads the graph file (from `GRAPH_FILE` or argv), selects the algorithm from `SSSP_ALGORITHM` (default: Duan–Mao–Shu–Yin), runs SSSP(0) once or in a timed loop when `SSSP_MIN_SECONDS` is set, and prints `DONE n reachable` or `DONE n reachable iterations`.
- **Dockerfiles:** `benchmark/docker/Dockerfile.<lang>` build a minimal image that runs that entrypoint; they expect the graph at `/data/graph.txt` (volume mount).

| Language   | Runner / entrypoint                          |
|-----------|-----------------------------------------------|
| C#        | `SSSP.Benchmark` console app                  |
| Rust      | `cargo build --bin benchmark`                 |
| C++       | `benchmark` executable (CMake target)        |
| Go        | `go build ./cmd/benchmark`                    |
| Java      | `sssp.Benchmark`                              |
| PHP       | `php run_php.php`                             |
| Python    | `python run_python.py`                        |
| TypeScript| `node run_ts.mjs`                             |
