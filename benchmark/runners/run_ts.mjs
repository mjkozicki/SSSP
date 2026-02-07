/**
 * Load graph from file, run SSSP(0), print DONE. Path = argv[1] or GRAPH_FILE env.
 * Run from repo root: node benchmark/runners/run_ts.mjs benchmark/data/graph.txt
 * (After building: node --experimental-vm-modules or node with dist)
 */
import { readFileSync } from "fs";
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
const { Graph, duanMaoShuYin } = lib;
const content = readFileSync(path, "utf8");
const lines = content.trim().split("\n");
const [n, m] = lines[0].split(" ").map(Number);
const g = new Graph(n);
for (let i = 1; i <= m; i++) {
  const [u, v, w] = lines[i].split(" ");
  g.addEdge(Number(u), Number(v), Number(w));
}
const r = duanMaoShuYin(g, 0);
const reachable = r.distance.filter((d) => isFinite(d)).length;
console.log("DONE", r.distance.length, reachable);
