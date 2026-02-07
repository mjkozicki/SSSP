#!/usr/bin/env python3
"""Load graph from file, run SSSP(0), print DONE. Path = argv[1] or GRAPH_FILE env."""
import os
import sys

# Assume repo layout: benchmark/runners/run_python.py, python/ at repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "python"))

from graph import Graph
from sssp import duan_mao_shu_yin


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
    r = duan_mao_shu_yin(g, 0)
    print("DONE", r.vertex_count(), sum(1 for d in r.distance if d != float("inf")))


if __name__ == "__main__":
    main()
