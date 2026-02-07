using System.Runtime.CompilerServices;

namespace SSSP;

/// <summary>
/// Dijkstra's algorithm for single-source shortest paths.
/// O((V+E) log V) with a min-priority queue; non-negative edge weights.
/// See https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
/// </summary>
public static class Dijkstra
{
    /// <summary>Runs SSSP from source; returns distances and predecessors (-1 for source/unreachable).</summary>
    [MethodImpl(MethodImplOptions.NoInlining)]
    public static SSSPResult Solve(Graph g, int source)
    {
        int n = g.VertexCount;
        if (n == 0) return new SSSPResult(0);

        var dist = new double[n];
        var pred = new int[n];
        for (int i = 0; i < n; i++)
        {
            dist[i] = double.PositiveInfinity;
            pred[i] = -1;
        }
        dist[source] = 0;

        int capacity = Math.Min(n, 4096);
        var pq = new PriorityQueue<int, double>(capacity);
        pq.Enqueue(source, 0);
        while (pq.Count > 0)
        {
            pq.TryDequeue(out int u, out double du);
            if (du > dist[u]) continue;
            var edges = g.GetOutEdges(u);
            for (int i = 0; i < edges.Count; i++)
            {
                var (v, w) = edges[i];
                double newD = dist[u] + w;
                if (newD < dist[v])
                {
                    dist[v] = newD;
                    pred[v] = u;
                    pq.Enqueue(v, newD);
                }
            }
        }

        var result = new SSSPResult(n);
        Array.Copy(dist, result.Distance, n);
        Array.Copy(pred, result.Predecessor, n);
        return result;
    }
}
