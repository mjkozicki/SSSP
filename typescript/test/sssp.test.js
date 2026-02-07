// Run with: node --test test/sssp.test.js (after building or run with ts-node)
const { Graph, duanMaoShuYin } = require('../dist');

function dijkstra(g, source) {
  const n = g.vertexCount();
  const dist = Array.from({ length: n }, () => Infinity);
  dist[source] = 0;
  const done = Array.from({ length: n }, () => false);
  for (let round = 0; round < n; round++) {
    let u = -1;
    let best = Infinity;
    for (let i = 0; i < n; i++) {
      if (!done[i] && dist[i] < best) {
        best = dist[i];
        u = i;
      }
    }
    if (u < 0 || !isFinite(best)) break;
    done[u] = true;
    for (const [to, w] of g.outEdges(u)) {
      const d = dist[u] + w;
      if (d < dist[to]) dist[to] = d;
    }
  }
  return dist;
}

function test(name, fn) {
  try {
    fn();
    console.log('ok', name);
  } catch (e) {
    console.error('not ok', name, e.message);
    throw e;
  }
}

test('single vertex', () => {
  const g = new Graph(1);
  const r = duanMaoShuYin(g, 0);
  if (r.distance[0] !== 0) throw new Error('expected 0');
});

test('two vertices one edge', () => {
  const g = new Graph(2);
  g.addEdge(0, 1, 3);
  const r = duanMaoShuYin(g, 0);
  if (r.distance[0] !== 0 || r.distance[1] !== 3) throw new Error('distances');
  if (r.predecessor[1] !== 0) throw new Error('predecessor');
});

test('matches dijkstra', () => {
  const g = new Graph(6);
  g.addEdge(0, 1, 2);
  g.addEdge(0, 2, 5);
  g.addEdge(1, 2, 2);
  g.addEdge(1, 3, 7);
  g.addEdge(2, 3, 1);
  g.addEdge(2, 4, 6);
  g.addEdge(3, 4, 3);
  g.addEdge(3, 5, 9);
  g.addEdge(4, 5, 1);
  const ref = dijkstra(g, 0);
  const r = duanMaoShuYin(g, 0);
  for (let i = 0; i < g.vertexCount(); i++) {
    if (Math.abs(ref[i] - r.distance[i]) >= 1e-10) {
      throw new Error(`vertex ${i}: ref ${ref[i]} vs ${r.distance[i]}`);
    }
  }
});
