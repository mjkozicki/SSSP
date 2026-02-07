/**
 * Load graph from file, run SSSP(0). Writes result to RESULT_FILE when set. Path = argv[1] or GRAPH_FILE env.
 * Run from repo root: node benchmark/runners/run_ts.mjs benchmark/data/graph.txt
 * (After building: node --experimental-vm-modules or node with dist)
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
const content = readFileSync(path, "utf8");
const lines = content.trim().split("\n");
const [n, m] = lines[0].split(" ").map(Number);
const g = new Graph(n);
for (let i = 1; i <= m; i++) {
  const [u, v, w] = lines[i].split(" ");
  g.addEdge(Number(u), Number(v), Number(w));
}
const algo = (process.env.SSSP_ALGORITHM || "duan_mao_shu_yin").trim().toLowerCase();
const fixedIters = Math.max(0, parseInt(process.env.SSSP_ITERATIONS || "0", 10) || 0);
const minSec = Math.max(0, parseFloat(process.env.SSSP_MIN_SECONDS || "0") || 0);
const maxSec = Math.max(0, parseFloat(process.env.SSSP_MAX_SECONDS || "30") || 30);
let iterations = 1;
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
const resultFile = process.env.RESULT_FILE;
if (resultFile) {
  writeFileSync(resultFile, JSON.stringify({ iterations }));
}
