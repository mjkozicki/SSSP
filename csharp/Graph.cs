namespace SSSP;

/// <summary>
/// Directed graph with non-negative edge weights for SSSP.
/// Vertices are 0..VertexCount-1.
/// </summary>
public sealed class Graph
{
    /// <summary>Number of vertices.</summary>
    public int VertexCount { get; }

    /// <summary>Number of edges.</summary>
    public int EdgeCount => _edgeCount;

    private int _edgeCount;
    /// <summary>Out-neighbors: for each vertex u, list of (v, weight) for edge u→v.</summary>
    private readonly List<(int to, double weight)>[] _outEdges;

    public Graph(int vertexCount)
    {
        VertexCount = vertexCount;
        _outEdges = new List<(int to, double weight)>[vertexCount];
        for (int i = 0; i < vertexCount; i++)
            _outEdges[i] = new List<(int to, double weight)>();
    }

    /// <summary>Adds directed edge (from, to) with given weight. Weight must be non-negative.</summary>
    public void AddEdge(int from, int to, double weight)
    {
        if (weight < 0)
            throw new ArgumentOutOfRangeException(nameof(weight), "Edge weights must be non-negative.");
        _outEdges[from].Add((to, weight));
        _edgeCount++;
    }

    /// <summary>Gets outgoing edges from vertex u.</summary>
    public IReadOnlyList<(int to, double weight)> GetOutEdges(int u) => _outEdges[u];

    /// <summary>Out-degree of vertex u.</summary>
    public int OutDegree(int u) => _outEdges[u].Count;
}
