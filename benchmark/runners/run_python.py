#!/usr/bin/env python3
"""Load graph from file, run SSSP(0). Writes result to RESULT_FILE when set. Path = argv[1] or GRAPH_FILE env.
When OTEL_EXPORTER_OTLP_ENDPOINT is set (e.g. SigNoz), emits a trace span for the run."""
import json
import os
import sys
import time

# Assume repo layout: benchmark/runners/run_python.py, python/ at repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "python"))

from graph import Graph
from sssp import dijkstra, duan_mao_shu_yin

# Optional OpenTelemetry: init only when OTEL_EXPORTER_OTLP_ENDPOINT is set
_tracer = None

def _init_tracer():
    global _tracer
    if _tracer is not None:
        return _tracer
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return None
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        resource = Resource.create({"service.name": os.environ.get("OTEL_SERVICE_NAME", "sssp-bench-python")})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("sssp-bench-python", "1.0.0")
        return _tracer
    except Exception:
        return None


def load_graph(path: str) -> Graph:
    with open(path) as f:
        line = f.readline()
        n, m = map(int, line.split())
        g = Graph(n)
        for _ in range(m):
            u, v, w = f.readline().split()
            g.add_edge(int(u), int(v), float(w))
    g.compact()
    return g


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GRAPH_FILE", "")
    if not path or not os.path.isfile(path):
        print("Usage: run_python.py <graph.txt>", file=sys.stderr)
        sys.exit(1)
    g = load_graph(path)
    algo = os.environ.get("SSSP_ALGORITHM", "duan_mao_shu_yin").strip().lower()
    fixed_iters = int(os.environ.get("SSSP_ITERATIONS", "0") or "0")
    min_sec = float(os.environ.get("SSSP_MIN_SECONDS", "0") or "0")
    max_sec = float(os.environ.get("SSSP_MAX_SECONDS", "30") or "30")

    tracer = _init_tracer()
    span_attrs = {"sssp.algorithm": algo}
    iterations = 1

    def run_benchmark():
        nonlocal iterations
        if fixed_iters > 0:
            r = dijkstra(g, 0) if algo == "dijkstra" else duan_mao_shu_yin(g, 0)
            for _ in range(fixed_iters - 1):
                r = dijkstra(g, 0) if algo == "dijkstra" else duan_mao_shu_yin(g, 0)
            iterations = fixed_iters
        elif min_sec > 0:
            start = time.perf_counter()
            iterations = 0
            while (time.perf_counter() - start) < min_sec:
                if (time.perf_counter() - start) >= max_sec:
                    break
                r = dijkstra(g, 0) if algo == "dijkstra" else duan_mao_shu_yin(g, 0)
                iterations += 1
        else:
            r = dijkstra(g, 0) if algo == "dijkstra" else duan_mao_shu_yin(g, 0)
        return r

    if tracer is not None:
        with tracer.start_as_current_span("sssp.benchmark", attributes=span_attrs) as span:
            run_benchmark()
            span.set_attribute("sssp.iterations", iterations)
    else:
        run_benchmark()

    result_file = os.environ.get("RESULT_FILE")
    if result_file:
        with open(result_file, "w") as f:
            json.dump({"iterations": iterations}, f)


if __name__ == "__main__":
    main()
