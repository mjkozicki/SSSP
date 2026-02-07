package sssp;

import java.util.*;

/**
 * Dijkstra's algorithm for single-source shortest paths.
 * O((V+E) log V) with a min-priority queue; non-negative edge weights.
 * See https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
 */
public final class Dijkstra {

    public static SsspResult solve(Graph g, int source) {
        int n = g.vertexCount();
        if (n == 0) {
            return new SsspResult(new double[0], new Integer[0]);
        }
        double[] d = new double[n];
        Integer[] pred = new Integer[n];
        Arrays.fill(d, Double.POSITIVE_INFINITY);
        d[source] = 0;

        int cap = Math.min(n, 4096);
        PriorityQueue<VertexDist> pq = new PriorityQueue<>(cap, Comparator.comparingDouble(a -> a.dist));
        pq.add(new VertexDist(0.0, source));
        while (!pq.isEmpty()) {
            VertexDist cur = pq.poll();
            double du = cur.dist;
            int u = cur.v;
            if (du > d[u]) continue;
            List<double[]> adj = g.outEdges(u);
            for (int i = 0; i < adj.size(); i++) {
                double[] e = adj.get(i);
                int v = (int) e[0];
                double w = e[1];
                double newD = d[u] + w;
                if (newD < d[v]) {
                    d[v] = newD;
                    pred[v] = u;
                    pq.add(new VertexDist(newD, v));
                }
            }
        }
        return new SsspResult(d, pred);
    }

    private static final class VertexDist {
        final double dist;
        final int v;

        VertexDist(double dist, int v) {
            this.dist = dist;
            this.v = v;
        }
    }
}
