namespace SSSP;

/// <summary>
/// Directed graph with non-negative edge weights for SSSP.
/// Vertices are 0..VertexCount-1.
/// After building, call Compact() for cache-friendly traversal (optional).
/// </summary>
public sealed class Graph
{
    /// <summary>Number of vertices.</summary>
    public int VertexCount { get; }

    /// <summary>Number of edges.</summary>
    public int EdgeCount => _edgeCount;

    private int _edgeCount;
    private bool _compact;
    /// <summary>Out-neighbors during build; unused after Compact().</summary>
    private readonly List<(int to, double weight)>[] _outEdges;
    /// <summary>CSR: flat edge targets (after Compact).</summary>
    internal int[]? _edgesTo;
    /// <summary>CSR: flat edge weights (after Compact).</summary>
    internal double[]? _edgesWeight;
    /// <summary>CSR: offset for vertex u is _offsets[u]; length VertexCount+1 (after Compact).</summary>
    private int[]? _offsets;

    public Graph(int vertexCount)
    {
        VertexCount = vertexCount;
        _outEdges = new List<(int to, double weight)>[vertexCount];
        for (int i = 0; i < vertexCount; i++)
            _outEdges[i] = new List<(int to, double weight)>();
    }

    /// <summary>Adds directed edge (from, to) with given weight. Weight must be non-negative. No-op after Compact().</summary>
    public void AddEdge(int from, int to, double weight)
    {
        if (_compact) return;
        if (weight < 0)
            throw new ArgumentOutOfRangeException(nameof(weight), "Edge weights must be non-negative.");
        _outEdges[from].Add((to, weight));
        _edgeCount++;
    }

    /// <summary>Compacts adjacency lists into a single flat CSR for better cache locality. Call once after adding all edges.</summary>
    public void Compact()
    {
        if (_compact) return;
        _offsets = new int[VertexCount + 1];
        for (int u = 0; u < VertexCount; u++)
            _offsets[u + 1] = _offsets[u] + _outEdges[u].Count;
        _edgesTo = new int[_edgeCount];
        _edgesWeight = new double[_edgeCount];
        for (int u = 0, pos = 0; u < VertexCount; u++)
        {
            foreach (var (to, w) in _outEdges[u])
            {
                _edgesTo[pos] = to;
                _edgesWeight[pos] = w;
                pos++;
            }
        }
        _compact = true;
    }

    /// <summary>Gets outgoing edges from vertex u.</summary>
    public OutEdgesView GetOutEdges(int u)
    {
        if (_compact)
            return new OutEdgesView(this, _offsets![u], _offsets[u + 1] - _offsets[u]);
        return new OutEdgesView(_outEdges[u]);
    }

    /// <summary>Out-degree of vertex u.</summary>
    public int OutDegree(int u)
    {
        if (_compact)
            return _offsets![u + 1] - _offsets[u];
        return _outEdges[u].Count;
    }
}

/// <summary>View over outgoing edges (list or compact slice). Supports foreach and indexing without boxing.</summary>
public readonly struct OutEdgesView
{
    private readonly Graph? _g;
    private readonly List<(int to, double weight)>? _list;
    private readonly int _start;
    private readonly int _count;

    internal OutEdgesView(Graph g, int start, int count)
    {
        _g = g;
        _list = null;
        _start = start;
        _count = count;
    }

    internal OutEdgesView(List<(int to, double weight)> list)
    {
        _g = null;
        _list = list;
        _start = 0;
        _count = list.Count;
    }

    public int Count => _count;

    public (int to, double weight) this[int index]
    {
        get
        {
            if (_list != null)
                return _list[index];
            return (_g!._edgesTo![_start + index], _g!._edgesWeight![_start + index]);
        }
    }

    public Enumerator GetEnumerator() => new Enumerator(this);

    public struct Enumerator
    {
        private readonly OutEdgesView _view;
        private int _i;

        internal Enumerator(OutEdgesView view)
        {
            _view = view;
            _i = -1;
        }

        public (int to, double weight) Current =>
            _view._list != null
                ? _view._list[_i]
                : (_view._g!._edgesTo![_view._start + _i], _view._g!._edgesWeight![_view._start + _i]);

        public bool MoveNext() => ++_i < _view._count;
    }
}
