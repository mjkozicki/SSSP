/** Directed graph with non-negative edge weights. Vertices are 0..vertexCount-1.
 * Call compact() after adding all edges for cache-friendly traversal. */
export class Graph {
  private _outEdges: [number, number][][] = [];
  private edgeCount = 0;
  private _compact = false;
  private _edges: [number, number][] = [];
  private _offsets: number[] = [];

  constructor(vertexCount: number) {
    this._outEdges = Array.from({ length: vertexCount }, () => []);
  }

  vertexCount(): number {
    return this._outEdges.length;
  }

  getEdgeCount(): number {
    return this.edgeCount;
  }

  /** No-op after compact(). */
  addEdge(from: number, to: number, weight: number): void {
    if (this._compact) return;
    if (weight < 0) throw new Error('edge weights must be non-negative');
    this._outEdges[from].push([to, weight]);
    this.edgeCount++;
  }

  /** Build a single flat edge array for better cache locality. Call once after adding all edges. */
  compact(): void {
    if (this._compact) return;
    const n = this.vertexCount();
    this._offsets = [0];
    for (let u = 0; u < n; u++) {
      this._offsets.push(this._offsets[u] + this._outEdges[u].length);
    }
    this._edges = [];
    for (let u = 0; u < n; u++) {
      for (const e of this._outEdges[u]) this._edges.push(e);
    }
    this._compact = true;
  }

  outEdges(u: number): [number, number][] {
    if (this._compact) {
      return this._edges.slice(this._offsets[u], this._offsets[u + 1]);
    }
    return this._outEdges[u];
  }
}
