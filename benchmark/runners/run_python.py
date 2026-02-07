#!/usr/bin/env python3
"""Load graph from file, run SSSP(0). Writes result to RESULT_FILE when set. Path = argv[1] or GRAPH_FILE env."""
import json
import os
import sys
import time

# Assume repo layout: benchmark/runners/run_python.py, python/ at repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "python"))

from graph import Graph
from sssp import dijkstra, duan_mao_shu_yin


def load_graph(path: str) -> Graph:
    with open(path) as f:
        line = f.readline()
        n, m = map(int, line.split())
        g = Graph(n)
        for _ in range(m):
            u, v, w = f.readline().split()
            g.add_edge(int(u), int(v), float(w))
    return g


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GRAPH_FILE", "")
    if not path or not os.path.isfile(path):
        print("Usage: run_python.py <graph.txt>", file=sys.stderr)
        sys.exit(1)
    g = load_graph(path)
    algo = os.environ.get("SSSP_ALGORITHM", "duan_mao_shu_yin").strip().lower()
    min_sec = float(os.environ.get("SSSP_MIN_SECONDS", "0") or "0")
    max_sec = float(os.environ.get("SSSP_MAX_SECONDS", "30") or "30")
    iterations = 1
    if min_sec > 0:
        start = time.perf_counter()
        iterations = 0
        while (time.perf_counter() - start) < min_sec:
            if (time.perf_counter() - start) >= max_sec:
                break
            if algo == "dijkstra":
                r = dijkstra(g, 0)
            else:
                r = duan_mao_shu_yin(g, 0)
            iterations += 1
    else:
        if algo == "dijkstra":
            r = dijkstra(g, 0)
        else:
            r = duan_mao_shu_yin(g, 0)
    result_file = os.environ.get("RESULT_FILE")
    if result_file:
        with open(result_file, "w") as f:
            json.dump({"iterations": iterations}, f)


if __name__ == "__main__":
    main()
