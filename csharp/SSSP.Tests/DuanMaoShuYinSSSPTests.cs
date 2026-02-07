using SSSP;
using Xunit;

namespace SSSP.Tests;

public sealed class DuanMaoShuYinSSSPTests
{
    private static double[] Dijkstra(Graph g, int source)
    {
        int n = g.VertexCount;
        var dist = new double[n];
        for (int i = 0; i < n; i++) dist[i] = double.PositiveInfinity;
        dist[source] = 0;
        var done = new bool[n];
        for (int round = 0; round < n; round++)
        {
            int u = -1;
            double best = double.PositiveInfinity;
            for (int i = 0; i < n; i++)
                if (!done[i] && dist[i] < best) { best = dist[i]; u = i; }
            if (u < 0) break;
            done[u] = true;
            foreach (var (to, w) in g.GetOutEdges(u))
            {
                double d = dist[u] + w;
                if (d < dist[to]) dist[to] = d;
            }
        }
        return dist;
    }

    [Fact]
    public void Single_vertex()
    {
        var g = new Graph(1);
        var result = DuanMaoShuYinSSSP.Solve(g, 0);
        Assert.Equal(0, result.Distance[0]);
    }

    [Fact]
    public void Two_vertices_one_edge()
    {
        var g = new Graph(2);
        g.AddEdge(0, 1, 3);
        var result = DuanMaoShuYinSSSP.Solve(g, 0);
        Assert.Equal(0, result.Distance[0]);
        Assert.Equal(3, result.Distance[1]);
        Assert.Equal(0, result.Predecessor[1]);
    }

    [Fact]
    public void Matches_Dijkstra_small_graph()
    {
        var g = new Graph(6);
        g.AddEdge(0, 1, 2); g.AddEdge(0, 2, 5);
        g.AddEdge(1, 2, 2); g.AddEdge(1, 3, 7);
        g.AddEdge(2, 3, 1); g.AddEdge(2, 4, 6);
        g.AddEdge(3, 4, 3); g.AddEdge(3, 5, 9);
        g.AddEdge(4, 5, 1);
        var dijkstra = Dijkstra(g, 0);
        var result = DuanMaoShuYinSSSP.Solve(g, 0);
        for (int i = 0; i < g.VertexCount; i++)
            Assert.Equal(dijkstra[i], result.Distance[i], precision: 10);
    }

    [Fact]
    public void Matches_Dijkstra_with_parallel_edges()
    {
        var g = new Graph(4);
        g.AddEdge(0, 1, 1); g.AddEdge(0, 2, 4);
        g.AddEdge(1, 3, 2); g.AddEdge(2, 3, 1);
        var dijkstra = Dijkstra(g, 0);
        var result = DuanMaoShuYinSSSP.Solve(g, 0);
        for (int i = 0; i < g.VertexCount; i++)
            Assert.Equal(dijkstra[i], result.Distance[i], precision: 10);
    }
}
