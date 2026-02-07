package sssp;

public final class Main {
    public static void main(String[] args) {
        Graph g = new Graph(6);
        g.addEdge(0, 1, 2);
        g.addEdge(0, 2, 5);
        g.addEdge(1, 2, 2);
        g.addEdge(1, 3, 7);
        g.addEdge(2, 3, 1);
        g.addEdge(2, 4, 6);
        g.addEdge(3, 4, 3);
        g.addEdge(3, 5, 9);
        g.addEdge(4, 5, 1);
        SsspResult r = DuanMaoShuYinSSSP.solve(g, 0);
        for (int i = 0; i < r.vertexCount(); i++) {
            System.out.println("dist[" + i + "] = " + r.getDistance()[i]);
        }
    }
}
