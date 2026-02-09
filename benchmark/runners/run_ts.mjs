/**
 * Load graph from file, run SSSP(0). Writes result to RESULT_FILE when set. Path = argv[1] or GRAPH_FILE env.
 * When OTEL_EXPORTER_OTLP_ENDPOINT is set (e.g. SigNoz), emits a trace span for the run.
 * Run from repo root: node benchmark/runners/run_ts.mjs benchmark/data/graph.txt
 */
import { readFileSync, writeFileSync } from "fs";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const path = process.argv[2] || process.env.GRAPH_FILE || "";
if (!path) {
  console.error("Usage: node run_ts.mjs <graph.txt>");
  process.exit(1);
}
// In Docker: /app/run_ts.mjs and /app/dist. From repo root: ../../typescript/dist
let lib;
try {
  lib = require("./dist");
} catch {
  lib = require("../../typescript/dist");
}
const { Graph, dijkstra, duanMaoShuYin } = lib;

function initTracer() {
  const endpoint = (process.env.OTEL_EXPORTER_OTLP_ENDPOINT || "").trim();
  if (!endpoint) return null;
  try {
    const { trace } = require("@opentelemetry/api");
    const { NodeTracerProvider } = require("@opentelemetry/sdk-trace-node");
    const { OTLPTraceExporter } = require("@opentelemetry/exporter-trace-otlp-http");
    const { BatchSpanProcessor } = require("@opentelemetry/sdk-trace-node");
    const { Resource } = require("@opentelemetry/resources");
    const resource = new Resource({
      "service.name": process.env.OTEL_SERVICE_NAME || "sssp-bench-typescript",
    });
    const provider = new NodeTracerProvider({ resource });
    const exporter = new OTLPTraceExporter();
    provider.addSpanProcessor(new BatchSpanProcessor(exporter));
    provider.register();
    return { tracer: trace.getTracer("sssp-bench-typescript", "1.0.0"), provider };
  } catch {
    return null;
  }
}

const content = readFileSync(path, "utf8");
const lines = content.trim().split("\n");
const [n, m] = lines[0].split(" ").map(Number);
const g = new Graph(n);
for (let i = 1; i <= m; i++) {
  const [u, v, w] = lines[i].split(" ");
  g.addEdge(Number(u), Number(v), Number(w));
}
g.compact();
const algo = (process.env.SSSP_ALGORITHM || "duan_mao_shu_yin").trim().toLowerCase();
const fixedIters = Math.max(0, parseInt(process.env.SSSP_ITERATIONS || "0", 10) || 0);
const minSec = Math.max(0, parseFloat(process.env.SSSP_MIN_SECONDS || "0") || 0);
const maxSec = Math.max(0, parseFloat(process.env.SSSP_MAX_SECONDS || "30") || 30);
let iterations = 1;

function runBenchmark() {
  if (fixedIters > 0) {
    let r = algo === "dijkstra" ? dijkstra(g, 0) : duanMaoShuYin(g, 0);
    for (let i = 1; i < fixedIters; i++) {
      r = algo === "dijkstra" ? dijkstra(g, 0) : duanMaoShuYin(g, 0);
    }
    iterations = fixedIters;
  } else if (minSec > 0) {
    const start = performance.now();
    iterations = 0;
    let r;
    while ((performance.now() - start) / 1000 < minSec && (performance.now() - start) / 1000 < maxSec) {
      r = algo === "dijkstra" ? dijkstra(g, 0) : duanMaoShuYin(g, 0);
      iterations++;
    }
  } else {
    const r = algo === "dijkstra" ? dijkstra(g, 0) : duanMaoShuYin(g, 0);
  }
}

const otel = initTracer();
if (otel) {
  otel.tracer.startActiveSpan("sssp.benchmark", { attributes: { "sssp.algorithm": algo } }, (span) => {
    try {
      runBenchmark();
      span.setAttribute("sssp.iterations", iterations);
    } finally {
      span.end();
    }
  });
  otel.provider.forceFlush(() => {
    const resultFile = process.env.RESULT_FILE;
    if (resultFile) writeFileSync(resultFile, JSON.stringify({ iterations }));
  });
} else {
  runBenchmark();
  const resultFile = process.env.RESULT_FILE;
  if (resultFile) writeFileSync(resultFile, JSON.stringify({ iterations }));
}
