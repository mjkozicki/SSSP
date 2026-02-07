/**
 * O(m log^{2/3} n) SSSP (Duan–Mao–Shu–Yin) for directed graphs with non-negative weights.
 */

import { Graph } from './graph';

const MAX_ITER = 100_000_000;
const EPS = 1e-12;

export interface SsspResult {
  distance: number[];
  predecessor: (number | null)[];
}

/**
 * Dijkstra's algorithm: O((V+E) log V) SSSP. Same result type as duanMaoShuYin.
 * See https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
 */
export function dijkstra(g: Graph, source: number): SsspResult {
  const n = g.vertexCount();
  if (n === 0) return { distance: [], predecessor: [] };

  const d = Array.from({ length: n }, () => Infinity);
  const pred: (number | null)[] = Array.from({ length: n }, () => null);
  d[source] = 0;

  const heap: [number, number][] = []; // [dist, v] min-heap
  const push = (dist: number, v: number) => {
    heap.push([dist, v]);
    let i = heap.length - 1;
    while (i > 0) {
      const p = Math.floor((i - 1) / 2);
      if (heap[p][0] <= heap[i][0]) break;
      [heap[i], heap[p]] = [heap[p], heap[i]];
      i = p;
    }
  };
  const pop = (): [number, number] | null => {
    if (heap.length === 0) return null;
    const top = heap[0];
    heap[0] = heap[heap.length - 1];
    heap.pop();
    let i = 0;
    while (true) {
      const l = 2 * i + 1, r = 2 * i + 2;
      let small = i;
      if (l < heap.length && heap[l][0] < heap[small][0]) small = l;
      if (r < heap.length && heap[r][0] < heap[small][0]) small = r;
      if (small === i) break;
      [heap[i], heap[small]] = [heap[small], heap[i]];
      i = small;
    }
    return top;
  };

  push(0, source);
  while (heap.length > 0) {
    const top = pop()!;
    const [du, u] = top;
    if (du > d[u]) continue;
    const adj = g.outEdges(u);
    for (let i = 0; i < adj.length; i++) {
      const [v, w] = adj[i];
      const newD = d[u] + w;
      if (newD < d[v]) {
        d[v] = newD;
        pred[v] = u;
        push(newD, v);
      }
    }
  }
  return { distance: d, predecessor: pred };
}

export function duanMaoShuYin(g: Graph, source: number): SsspResult {
  const n = g.vertexCount();
  if (n === 0) return { distance: [], predecessor: [] };

  const d = Array.from({ length: n }, () => Infinity);
  const pred: (number | null)[] = Array.from({ length: n }, () => null);
  d[source] = 0;

  const tLog = Math.log(Math.max(n, 2)) / Math.LN2;
  const t = Math.max(1, Math.floor(tLog ** (2 / 3)));
  const k = Math.max(1, Math.floor(tLog ** (1 / 3)));
  const l = Math.ceil(tLog / t);

  const s = [source];
  bmssp(g, d, pred, l, Infinity, s, n, k, t);

  return { distance: d, predecessor: pred };
}

function relax(d: number[], pred: (number | null)[], u: number, v: number, w: number): void {
  const newD = d[u] + w;
  if (newD >= d[v]) return;
  d[v] = newD;
  pred[v] = u;
}

function pow2(exp: number): number {
  if (exp <= 0) return 1;
  return 1 << Math.min(exp, 30);
}

class MinHeap {
  private heap: [number, number][] = [];
  private index: number[] = [];

  constructor(maxVertex: number) {
    this.index = Array.from({ length: maxVertex }, () => -1);
  }

  isEmpty(): boolean {
    return this.heap.length === 0;
  }

  contains(v: number): boolean {
    return v < this.index.length && this.index[v] >= 0;
  }

  insert(v: number, dist: number): void {
    const i = this.heap.length;
    this.index[v] = i;
    this.heap.push([v, dist]);
    this.siftUp(i);
  }

  extractMin(): [number, number] {
    const top = this.heap[0];
    this.index[top[0]] = -1;
    this.heap[0] = this.heap[this.heap.length - 1];
    this.heap.pop();
    if (this.heap.length > 0) {
      this.index[this.heap[0][0]] = 0;
      this.siftDown(0);
    }
    return top;
  }

  decreaseKey(v: number, newD: number): void {
    const i = this.index[v];
    if (i < 0 || this.heap[i][1] <= newD) return;
    this.heap[i] = [v, newD];
    this.siftUp(i);
  }

  private siftUp(i: number): void {
    while (i > 0) {
      const p = Math.floor((i - 1) / 2);
      if (this.heap[p][1] <= this.heap[i][1]) break;
      this.swap(i, p);
      i = p;
    }
  }

  private siftDown(i: number): void {
    while (true) {
      const l = 2 * i + 1;
      const r = 2 * i + 2;
      let small = i;
      if (l < this.heap.length && this.heap[l][1] < this.heap[small][1]) small = l;
      if (r < this.heap.length && this.heap[r][1] < this.heap[small][1]) small = r;
      if (small === i) break;
      this.swap(i, small);
      i = small;
    }
  }

  private swap(i: number, j: number): void {
    const a = this.heap[i];
    const b = this.heap[j];
    this.heap[i] = b;
    this.heap[j] = a;
    this.index[a[0]] = j;
    this.index[b[0]] = i;
  }
}

class FrontierDS {
  private m: number;
  private b: number;
  private keyToValue = new Map<number, number>();
  private list: [number, number][] = [];
  private sorted = true;

  constructor(m: number, b: number) {
    this.m = Math.max(m, 1);
    this.b = b;
  }

  insert(key: number, value: number): void {
    const old = this.keyToValue.get(key);
    if (old !== undefined && value >= old) return;
    this.list = this.list.filter(([, k]) => k !== key);
    this.keyToValue.set(key, value);
    this.list.push([value, key]);
    this.sorted = false;
  }

  batchPrepend(pairs: [number, number][]): void {
    for (const [key, value] of pairs) {
      const old = this.keyToValue.get(key);
      if (old !== undefined && value >= old) continue;
      this.list = this.list.filter(([, k]) => k !== key);
      this.keyToValue.set(key, value);
      this.list.push([value, key]);
    }
    this.sorted = false;
  }

  pull(): { bound: number; keys: number[] } | null {
    if (this.list.length === 0) return null;
    if (!this.sorted) {
      this.list.sort((a, b) => (a[0] !== b[0] ? a[0] - b[0] : a[1] - b[1]));
      this.sorted = true;
    }
    const take = Math.min(this.m, this.list.length);
    const keys = this.list.slice(0, take).map(([, k]) => k);
    keys.forEach((k) => this.keyToValue.delete(k));
    this.list = this.list.slice(take);
    const bound = this.list.length > 0 ? this.list[0][0] : this.b;
    return { bound, keys };
  }

  isEmpty(): boolean {
    return this.list.length === 0;
  }
}

function baseCase(
  g: Graph,
  d: number[],
  pred: (number | null)[],
  b: number,
  s: number[],
  n: number,
  k: number
): [number, number[]] {
  const x = s[0];
  const u0: number[] = [];
  const heap = new MinHeap(n);
  heap.insert(x, d[x]);

  while (!heap.isEmpty() && u0.length < k + 1) {
    const [u, du] = heap.extractMin();
    u0.push(u);
    for (const [v, wE] of g.outEdges(u)) {
      const newD = du + wE;
      if (newD >= b || newD > d[v]) continue;
      relax(d, pred, u, v, wE);
      if (heap.contains(v)) heap.decreaseKey(v, d[v]);
      else heap.insert(v, d[v]);
    }
  }

  if (u0.length <= k) return [b, u0];
  const bPrime = Math.max(...u0.map((v) => d[v]));
  return [bPrime, u0.filter((v) => d[v] < bPrime)];
}

function countSubtree(u: number, children: number[][], size: number[]): number {
  if (size[u] !== 0) return size[u];
  let s = 1;
  for (const v of children[u]) s += countSubtree(v, children, size);
  size[u] = s;
  return s;
}

function findPivots(
  g: Graph,
  d: number[],
  pred: (number | null)[],
  b: number,
  s: number[],
  k: number
): [number[], number[]] {
  let w = [...s];
  let wi = [...s];

  for (let round = 1; round <= k; round++) {
    const wiNext: number[] = [];
    for (const u of wi) {
      for (const [v, wE] of g.outEdges(u)) {
        const newD = d[u] + wE;
        if (newD > d[v]) continue;
        relax(d, pred, u, v, wE);
        if (newD < b) wiNext.push(v);
      }
    }
    w = w.concat(wiNext);
    wi = wiNext;
    if (w.length > k * s.length) return [[...s], w];
  }

  const inW = new Set(w);
  const parent: (number | null)[] = Array.from({ length: g.vertexCount() }, () => null);
  for (const u of w) {
    for (const [v, wE] of g.outEdges(u)) {
      if (inW.has(v) && Math.abs(d[v] - (d[u] + wE)) < EPS && parent[v] === null)
        parent[v] = u;
    }
  }

  const children: number[][] = Array.from({ length: g.vertexCount() }, () => []);
  for (const v of w) if (parent[v] !== null) children[parent[v]!].push(v);

  const subtreeSize = Array.from({ length: g.vertexCount() }, () => 0);
  const hasParent = new Set(w.filter((v) => parent[v] !== null));
  const rootsInS = s.filter(
    (r) => !hasParent.has(r) && countSubtree(r, children, subtreeSize) >= k
  );
  return [rootsInS, w];
}

function bmssp(
  g: Graph,
  d: number[],
  pred: (number | null)[],
  l: number,
  b: number,
  s: number[],
  n: number,
  k: number,
  t: number
): [number, number[]] {
  const twoLt = pow2(l * t);
  if (l === 0) return baseCase(g, d, pred, b, s, n, k);

  const [p, w] = findPivots(g, d, pred, b, s, k);
  const m = Math.max(pow2((l - 1) * t), 1);
  const ds = new FrontierDS(m, b);
  for (const x of p) ds.insert(x, d[x]);

  let b0Prime = b;
  for (const x of p) if (d[x] < b0Prime) b0Prime = d[x];

  const uSet = new Set<number>();
  let lastBiPrime = b0Prime;
  let iter = 0;

  while (uSet.size < k * twoLt && iter < MAX_ITER) {
    const pullResult = ds.pull();
    if (pullResult === null) break;
    const { bound: bi, keys: si } = pullResult;
    iter++;
    const [biPrime, ui] = bmssp(g, d, pred, l - 1, bi, si, n, k, t);
    lastBiPrime = biPrime;
    for (const u of ui) uSet.add(u);

    const kList: [number, number][] = [];
    for (const u of ui) {
      const adj = g.outEdges(u);
      for (let i = 0; i < adj.length; i++) {
        const [v, wE] = adj[i];
        const newD = d[u] + wE;
        if (newD > d[v]) continue;
        relax(d, pred, u, v, wE);
        if (d[v] >= bi && d[v] < b) ds.insert(v, d[v]);
        else if (d[v] >= biPrime && d[v] < bi) kList.push([v, d[v]]);
      }
    }
    for (const x of si) if (d[x] >= biPrime && d[x] < bi) kList.push([x, d[x]]);
    ds.batchPrepend(kList);

    if (ds.isEmpty()) return [b, [...uSet]];
    if (uSet.size > k * twoLt) return [biPrime, [...uSet]];
  }

  const bPrime = iter > 0 ? lastBiPrime : b0Prime;
  for (const x of w) if (d[x] < bPrime) uSet.add(x);
  return [bPrime, [...uSet]];
}
