package sssp;

import java.io.*;
import java.util.*;

/** Reads graph from file (n m then u v w lines), runs SSSP(0), prints DONE. */
public final class Benchmark {
    public static void main(String[] args) throws IOException {
        String path = args.length > 0 ? args[0] : System.getenv("GRAPH_FILE");
        if (path == null || path.isEmpty()) {
            System.err.println("Usage: java sssp.Benchmark <graph.txt>");
            System.exit(1);
        }
        Graph g = loadGraph(path);
        SsspResult r = DuanMaoShuYinSSSP.solve(g, 0);
        int reachable = 0;
        for (double d : r.getDistance())
            if (Double.isFinite(d)) reachable++;
        System.out.println("DONE " + r.vertexCount() + " " + reachable);
    }

    static Graph loadGraph(String path) throws IOException {
        try (Scanner sc = new Scanner(new File(path))) {
            int n = sc.nextInt(), m = sc.nextInt();
            Graph g = new Graph(n);
            for (int i = 0; i < m; i++)
                g.addEdge(sc.nextInt(), sc.nextInt(), sc.nextDouble());
            return g;
        }
    }
}
