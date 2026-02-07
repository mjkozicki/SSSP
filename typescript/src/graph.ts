/** Directed graph with non-negative edge weights. Vertices are 0..vertexCount-1. */
export class Graph {
  private _outEdges: [number, number][][] = [];
  private edgeCount = 0;

  constructor(vertexCount: number) {
    this._outEdges = Array.from({ length: vertexCount }, () => []);
  }

  vertexCount(): number {
    return this._outEdges.length;
  }

  getEdgeCount(): number {
    return this.edgeCount;
  }

  addEdge(from: number, to: number, weight: number): void {
    if (weight < 0) throw new Error('edge weights must be non-negative');
    this._outEdges[from].push([to, weight]);
    this.edgeCount++;
  }

  outEdges(u: number): [number, number][] {
    return this._outEdges[u];
  }
}
