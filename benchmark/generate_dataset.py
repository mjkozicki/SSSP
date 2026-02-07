#!/usr/bin/env python3
"""
Generate a benchmark graph emulating a globally distributed network of 50k servers.
Deterministic (seed=42). Output: first line "n m", then m lines "u v weight" (0-indexed).
"""

import random
import sys
from pathlib import Path

# Fixed seed for reproducibility
SEED = 42
N = 50_000

# Emulate global distribution: ~20 regions (continents/DCs), intra-region dense, inter-region sparse
NUM_REGIONS = 20
INTRA_EDGES_PER_NODE = (2, 8)   # edges within region (low latency)
INTER_EDGES_PER_NODE = (0, 2)   # edges to other regions (higher latency)
INTRA_LATENCY_MS = (0.5, 5.0)   # ms within region
INTER_LATENCY_MS = (20.0, 150.0)  # ms between regions (continental)


def main():
    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "graph.txt"

    random.seed(SEED)
    n = N
    region_size = n // NUM_REGIONS
    # Assign each vertex to a region
    region_of = [i // region_size for i in range(n)]
    if region_of[-1] >= NUM_REGIONS:
        region_of[-1] = NUM_REGIONS - 1

    edges = []
    for u in range(n):
        r_u = region_of[u]
        # Intra-region: random neighbors in same region
        intra_count = random.randint(*INTRA_EDGES_PER_NODE)
        for _ in range(intra_count):
            v = random.randint(0, n - 1)
            if region_of[v] != r_u:
                continue
            if u == v:
                continue
            w = random.uniform(*INTRA_LATENCY_MS)
            edges.append((u, v, w))
        # Inter-region: few random edges to other regions
        inter_count = random.randint(*INTER_EDGES_PER_NODE)
        for _ in range(inter_count):
            v = random.randint(0, n - 1)
            if region_of[v] == r_u:
                continue
            if u == v:
                continue
            w = random.uniform(*INTER_LATENCY_MS)
            edges.append((u, v, w))

    m = len(edges)
    with open(out_path, "w") as f:
        f.write(f"{n} {m}\n")
        for u, v, w in edges:
            f.write(f"{u} {v} {w}\n")

    print(f"Wrote {out_path}: n={n} m={m}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
