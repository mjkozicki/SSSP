#!/usr/bin/env python3
"""
Benchmark harness: run each language's Docker benchmark image sequentially and collect:
  - Overall user runtime (wall clock)
  - Peak memory allocation
  - Sum of total CPU time over all threads (from docker stats CPU% integrated over time)
  - Individual CPU utilization (time series of CPU% and memory samples)

Dataset: 50k-server global network graph (generate with generate_dataset.py).
Usage: from repo root, run: python benchmark/run_benchmarks.py [--build] [--output results.json]
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from urllib.request import Request, urlopen

try:
    from benchmark.db import init_db, insert_run, insert_session, DB_PATH
except ImportError:
    from db import init_db, insert_run, insert_session, DB_PATH

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "benchmark" / "data"
GRAPH_PATH = DATA_DIR / "graph.txt"

LANGUAGES = [
    "csharp",
    "rust",
    "cplusplus",
    "go",
    "java",
    "php",
    "python",
    "typescript",
]

# Dockerfile paths relative to repo root
DOCKERFILES = {
    "csharp": "benchmark/docker/Dockerfile.csharp",
    "rust": "benchmark/docker/Dockerfile.rust",
    "cplusplus": "benchmark/docker/Dockerfile.cplusplus",
    "go": "benchmark/docker/Dockerfile.go",
    "java": "benchmark/docker/Dockerfile.java",
    "php": "benchmark/docker/Dockerfile.php",
    "python": "benchmark/docker/Dockerfile.python",
    "typescript": "benchmark/docker/Dockerfile.typescript",
}

STATS_INTERVAL = 0.5  # seconds between docker stats samples


def _post_progress(progress_url, data):
    """POST JSON to the web UI progress endpoint (fire-and-forget)."""
    if not progress_url:
        return
    try:
        req = Request(
            progress_url.rstrip("/") + "/api/progress",
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urlopen(req, timeout=2)
    except Exception:
        pass


def ensure_dataset():
    if not GRAPH_PATH.is_file():
        print("Generating benchmark dataset (50k servers)...", flush=True)
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "benchmark" / "generate_dataset.py")],
            cwd=REPO_ROOT,
            check=True,
        )
    else:
        print(f"Using existing dataset: {GRAPH_PATH}", flush=True)


def build_images(build: bool, progress_url=None):
    if not build:
        return
    _post_progress(progress_url, {"event": "build_started", "languages": LANGUAGES})
    for lang in LANGUAGES:
        df = DOCKERFILES[lang]
        tag = f"sssp-bench-{lang}"
        print(f"Building {tag} ...", flush=True)
        _post_progress(progress_url, {"event": "building", "language": lang})
        subprocess.run(
            ["docker", "build", "-f", df, "-t", tag, "."],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
        _post_progress(progress_url, {"event": "built", "language": lang})
    _post_progress(progress_url, {"event": "build_finished"})


ALGORITHMS = ("dijkstra", "duan_mao_shu_yin")


def run_container_and_collect_stats(
    image: str,
    timeout_sec: int = 600,
    algorithm: str = "duan_mao_shu_yin",
    min_seconds: float = 0,
):
    """Run container with -v data:/data (detached), collect stats, then wait. Return wall time and stats."""
    if algorithm not in ALGORITHMS:
        algorithm = "duan_mao_shu_yin"
    stats_samples = []
    stats_stop = threading.Event()
    container_id = [None]

    def stats_loop():
        start = time.perf_counter()
        while not stats_stop.is_set() and container_id[0]:
            try:
                out = subprocess.run(
                    [
                        "docker", "stats", container_id[0],
                        "--no-stream", "--format", "{{.CPUPerc}}\t{{.MemUsage}}",
                    ],
                    capture_output=True, text=True, timeout=5, cwd=REPO_ROOT,
                )
                if out.returncode == 0 and out.stdout.strip():
                    parts = out.stdout.strip().split("\t")
                    cpu_s = (parts[0].rstrip("%").strip() or "0").replace(",", ".")
                    mem_part = (parts[1].split("/")[0].strip().rstrip("MiB").strip() or "0").replace(",", ".") if len(parts) > 1 else "0"
                    try:
                        cpu_pct = float(cpu_s)
                    except ValueError:
                        cpu_pct = 0.0
                    try:
                        mem_mb = float(mem_part)
                    except ValueError:
                        mem_mb = 0.0
                    stats_samples.append({
                        "elapsed_sec": round(time.perf_counter() - start, 2),
                        "cpu_pct": round(cpu_pct, 2),
                        "mem_mb": round(mem_mb, 2),
                    })
            except Exception:
                pass
            for _ in range(int(STATS_INTERVAL * 10)):
                if stats_stop.is_set():
                    break
                time.sleep(0.1)

    # Run detached to get container ID, then collect stats and wait
    cmd = [
        "docker", "run", "-d", "--rm",
        "-v", f"{DATA_DIR}:/data:ro",
        "-e", "GRAPH_FILE=/data/graph.txt",
        "-e", f"SSSP_ALGORITHM={algorithm}",
        image,
        "/data/graph.txt",
    ]
    if min_seconds > 0:
        cmd = cmd[:-2] + ["-e", f"SSSP_MIN_SECONDS={min_seconds}"] + cmd[-2:]
    start_wall = time.perf_counter()
    out = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        return None, [], None, None, out.stderr or "docker run failed"
    cid = out.stdout.strip()
    container_id[0] = cid

    stats_thread = threading.Thread(target=stats_loop)
    stats_thread.start()
    try:
        wait_out = subprocess.run(
            ["docker", "wait", cid],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=REPO_ROOT,
        )
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", cid], capture_output=True)
        stats_stop.set()
        stats_thread.join()
        return time.perf_counter() - start_wall, stats_samples, None, None, "timeout"
    stats_stop.set()
    stats_thread.join(timeout=2)
    wall_sec = time.perf_counter() - start_wall

    # Get exit code
    exit_code = int(wait_out.stdout.strip()) if wait_out.stdout.strip() else -1
    if exit_code != 0:
        logs = subprocess.run(
            ["docker", "logs", cid],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        return wall_sec, stats_samples, None, None, f"exit {exit_code}: " + (logs.stderr or logs.stdout or "")

    peak_mem_mb = max((s["mem_mb"] for s in stats_samples), default=0)
    total_cpu_sec = 0.0
    for i in range(1, len(stats_samples)):
        dt = stats_samples[i]["elapsed_sec"] - stats_samples[i - 1]["elapsed_sec"]
        avg_cpu = (stats_samples[i]["cpu_pct"] + stats_samples[i - 1]["cpu_pct"]) / 2
        total_cpu_sec += (avg_cpu / 100.0) * dt
    if len(stats_samples) == 1:
        total_cpu_sec = (stats_samples[0]["cpu_pct"] / 100.0) * wall_sec

    return wall_sec, stats_samples, peak_mem_mb, total_cpu_sec, None


def main():
    ap = argparse.ArgumentParser(description="Run SSSP benchmarks in Docker and collect metrics")
    ap.add_argument("--build", action="store_true", help="Build all benchmark images first")
    ap.add_argument("--output", default="benchmark/results.json", help="Output JSON file")
    ap.add_argument("--no-json", action="store_true", help="Do not write JSON output")
    ap.add_argument("--timeout", type=int, default=600, help="Timeout per run (seconds)")
    ap.add_argument("--lang", choices=LANGUAGES, help="Run only this language")
    ap.add_argument("--algorithm", choices=ALGORITHMS, default="duan_mao_shu_yin", help="SSSP algorithm: dijkstra or duan_mao_shu_yin")
    ap.add_argument("--min-seconds", type=float, default=0, metavar="SEC", help="Run repeated iterations until at least SEC seconds elapsed (e.g. 10 for 10s timed run)")
    ap.add_argument("--progress-url", default=os.environ.get("PROGRESS_URL"), help="Web UI base URL for progress (e.g. http://127.0.0.1:5000)")
    args = ap.parse_args()

    progress_url = args.progress_url
    algorithm = args.algorithm
    min_seconds = max(0.0, args.min_seconds)
    os.chdir(REPO_ROOT)
    ensure_dataset()
    init_db()
    build_images(args.build, progress_url)

    languages = [args.lang] if args.lang else LANGUAGES
    session_id = insert_session(languages, algorithm)
    results = {}

    _post_progress(progress_url, {"event": "suite_started", "languages": languages})

    for lang in languages:
        image = f"sssp-bench-{lang}"
        print(f"\n--- {lang} ---", flush=True)
        _post_progress(progress_url, {"event": "started", "language": lang})
        wall, utilization, peak_mem, total_cpu, err = run_container_and_collect_stats(
            image, args.timeout, algorithm, min_seconds
        )
        if err:
            print(f"  Error: {err}", flush=True)
            results[lang] = {"error": err, "wall_sec": wall}
            insert_run(session_id, lang, wall, None, None, err, utilization or [])
            _post_progress(progress_url, {
                "event": "completed", "language": lang,
                "wall_sec": wall, "peak_mem_mb": None, "total_cpu_sec": None, "error": err,
            })
        else:
            results[lang] = {
                "wall_sec": round(wall, 3),
                "peak_mem_mb": round(peak_mem, 2) if peak_mem is not None else None,
                "total_cpu_sec": round(total_cpu, 3) if total_cpu is not None else None,
                "cpu_utilization": utilization,
            }
            insert_run(session_id, lang, wall, peak_mem, total_cpu, None, utilization or [])
            print(f"  wall_sec={results[lang]['wall_sec']} peak_mem_mb={results[lang]['peak_mem_mb']} total_cpu_sec={results[lang]['total_cpu_sec']}", flush=True)
            _post_progress(progress_url, {
                "event": "completed", "language": lang,
                "wall_sec": wall, "peak_mem_mb": peak_mem, "total_cpu_sec": total_cpu, "error": None,
            })

    _post_progress(progress_url, {"event": "suite_finished", "session_id": session_id})

    if not args.no_json:
        out_path = REPO_ROOT / args.output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nWrote {out_path}", flush=True)
    print(f"Results stored in SQLite: {DB_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
