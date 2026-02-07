package sssp;

import java.util.ArrayList;
import java.util.List;

/** Directed graph with non-negative edge weights. Vertices are 0..vertexCount()-1. */
public final class Graph {
    private final List<List<double[]>> outEdges; // each double[] is {to, weight}
    private int edgeCount;

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

    public void addEdge(int from, int to, double weight) {
        if (weight < 0) throw new IllegalArgumentException("edge weights must be non-negative");
        outEdges.get(from).add(new double[]{to, weight});
        edgeCount++;
    }

    public List<double[]> outEdges(int u) {
        return outEdges.get(u);
    }
}
