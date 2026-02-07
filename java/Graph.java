package sssp;

import java.util.ArrayList;
import java.util.List;

/** Directed graph with non-negative edge weights. Vertices are 0..vertexCount()-1.
 * Call compact() after adding all edges for cache-friendly traversal. */
public final class Graph {
    private final List<List<double[]>> outEdges; // each double[] is {to, weight}
    private int edgeCount;
    private boolean compact;
    private List<double[]> edges;  // flat [to, weight] after compact
    private int[] offsets;        // length vertexCount+1

    public Graph(int vertexCount) {
        outEdges = new ArrayList<>(vertexCount);
        for (int i = 0; i < vertexCount; i++) {
            outEdges.add(new ArrayList<>());
        }
    }

    public int vertexCount() {
        return outEdges.size();
    }

    public int edgeCount() {
        return edgeCount;
    }

    /** No-op after compact(). */
    public void addEdge(int from, int to, double weight) {
        if (compact) return;
        if (weight < 0) throw new IllegalArgumentException("edge weights must be non-negative");
        outEdges.get(from).add(new double[]{to, weight});
        edgeCount++;
    }

    /** Builds a single flat edge list for better cache locality. Call once after adding all edges. */
    public void compact() {
        if (compact) return;
        int n = outEdges.size();
        offsets = new int[n + 1];
        for (int u = 0; u < n; u++) {
            offsets[u + 1] = offsets[u] + outEdges.get(u).size();
        }
        edges = new ArrayList<>(edgeCount);
        for (int u = 0; u < n; u++) {
            for (double[] e : outEdges.get(u)) {
                edges.add(new double[]{e[0], e[1]});
            }
        }
        compact = true;
    }

    public List<double[]> outEdges(int u) {
        if (compact) {
            return edges.subList(offsets[u], offsets[u + 1]);
        }
        return outEdges.get(u);
    }
}
