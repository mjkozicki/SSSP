package sssp;

/** Result of single-source shortest path. Predecessor is null for source or unreachable. */
public final class SsspResult {
    private final double[] distance;
    private final Integer[] predecessor;

    public SsspResult(double[] distance, Integer[] predecessor) {
        this.distance = distance;
        this.predecessor = predecessor;
    }

    public double[] getDistance() {
        return distance;
    }

    public Integer[] getPredecessor() {
        return predecessor;
    }

    public int vertexCount() {
        return distance.length;
    }
}
