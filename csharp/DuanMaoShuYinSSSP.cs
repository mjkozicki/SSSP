namespace SSSP;

/// <summary>
/// O(m log^{2/3} n) deterministic SSSP for directed graphs with non-negative real weights,
/// from "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths" (Duan, Mao, Shu, Yin).
/// Comparison-addition model; no integer/word-RAM tricks.
/// </summary>
public static class DuanMaoShuYinSSSP
{
    /// <summary>Runs SSSP from source <paramref name="source"/>; returns distances and predecessors.</summary>
    public static SSSPResult Solve(Graph g, int source)
    {
        int n = g.VertexCount;
        if (n == 0) return new SSSPResult(0);
        var d = new double[n];
        var pred = new int[n];
        for (int i = 0; i < n; i++)
        {
            d[i] = double.PositiveInfinity;
            pred[i] = -1;
        }
        d[source] = 0;

        double tLog = Math.Log(Math.Max(n, 2), 2);
        int t = Math.Max(1, (int)Math.Floor(Math.Pow(tLog, 2.0 / 3.0)));
        int k = Math.Max(1, (int)Math.Floor(Math.Pow(tLog, 1.0 / 3.0)));
        int l = (int)Math.Ceiling(tLog / t);

        BMSSP(g, d, pred, l, double.PositiveInfinity, new[] { source }, n, k, t);

        var result = new SSSPResult(n);
        Array.Copy(d, result.Distance, n);
        Array.Copy(pred, result.Predecessor, n);
        return result;
    }

    /// <summary>Bounded Multi-Source Shortest Path (Algorithm 3).</summary>
    private static (double BPrime, List<int> U) BMSSP(
        Graph g, double[] d, int[] pred, int l, double B, int[] S,
        int n, int k, int t)
    {
        int twoLt = Pow2(l * t);
        if (l == 0)
            return BaseCase(g, d, pred, B, S, n, k);

        var (P, W) = FindPivots(g, d, pred, B, S, k);

        int M = Pow2((l - 1) * t);
        var D = new FrontierDSSimple(M, B);
        foreach (int x in P)
            D.Insert(x, d[x]);

        double B0Prime = P.Length > 0 ? P.Min(x => d[x]) : B;
        var USet = new HashSet<int>();
        double lastBiPrime = B0Prime;
        int iter = 0;
        const int maxIter = 100_000_000; // guard
        while (USet.Count < k * twoLt && iter < maxIter)
        {
            if (!D.TryPull(out double Bi, out int[] Si)) break;
            iter++;
            var (BiPrime, Ui) = BMSSP(g, d, pred, l - 1, Bi, Si, n, k, t);
            lastBiPrime = BiPrime;
            foreach (int u in Ui) USet.Add(u);

            var K = new List<(int key, double value)>();
            foreach (int u in Ui)
            {
                foreach (var (v, w) in g.GetOutEdges(u))
                {
                    double newD = d[u] + w;
                    if (newD > d[v]) continue;
                    Relax(d, pred, u, v, w);
                    if (d[v] >= Bi && d[v] < B)
                        D.Insert(v, d[v]);
                    else if (d[v] >= BiPrime && d[v] < Bi)
                        K.Add((v, d[v]));
                }
            }

            foreach (int x in Si)
                if (d[x] >= BiPrime && d[x] < Bi)
                    K.Add((x, d[x]));
            D.BatchPrepend(K);

            if (D.IsEmpty) return (B, USet.ToList());
            if (USet.Count > k * twoLt) return (BiPrime, USet.ToList());
        }

        double BPrime = iter > 0 ? lastBiPrime : B0Prime;
        foreach (int x in W)
            if (d[x] < BPrime) USet.Add(x);
        return (BPrime, USet.ToList());
    }

    /// <summary>Base case (Algorithm 2): singleton S, mini-Dijkstra.</summary>
    private static (double BPrime, List<int> U) BaseCase(
        Graph g, double[] d, int[] pred, double B, int[] S, int n, int k)
    {
        int x = S[0];
        var U0 = new List<int>();
        var heap = new MinHeap(n);
        heap.Insert(x, d[x]);

        while (!heap.IsEmpty && U0.Count < k + 1)
        {
            var (u, du) = heap.ExtractMin();
            U0.Add(u);
            foreach (var (v, w) in g.GetOutEdges(u))
            {
                double newD = du + w;
                if (newD >= B) continue;
                if (newD > d[v]) continue;
                Relax(d, pred, u, v, w);
                if (heap.Contains(v)) heap.DecreaseKey(v, d[v]);
                else heap.Insert(v, d[v]);
            }
        }

        if (U0.Count <= k)
            return (B, U0);
        double BPrime = U0.Max(v => d[v]);
        return (BPrime, U0.Where(v => d[v] < BPrime).ToList());
    }

    /// <summary>FindPivots (Algorithm 1).</summary>
    private static (int[] P, List<int> W) FindPivots(
        Graph g, double[] d, int[] pred, double B, int[] S, int k)
    {
        var W = new List<int>(S);
        var Wi = new List<int>(S);
        for (int i = 1; i <= k; i++)
        {
            var WiNext = new List<int>();
            foreach (int u in Wi)
            {
                foreach (var (v, w) in g.GetOutEdges(u))
                {
                    double newD = d[u] + w;
                    if (newD > d[v]) continue;
                    Relax(d, pred, u, v, w);
                    if (newD < B) WiNext.Add(v);
                }
            }
            foreach (int v in WiNext) W.Add(v);
            Wi = WiNext;
            if (W.Count > k * S.Length)
                return (S, W);
        }

        var inW = new HashSet<int>(W);
        var parent = new int[g.VertexCount];
        Array.Fill(parent, -1);
        foreach (int u in W)
        {
            foreach (var (v, w) in g.GetOutEdges(u))
                if (inW.Contains(v) && Math.Abs(d[v] - (d[u] + w)) < 1e-12)
                    if (parent[v] == -1) parent[v] = u;
        }

        var children = new List<int>[g.VertexCount];
        for (int i = 0; i < g.VertexCount; i++) children[i] = new List<int>();
        foreach (int v in W)
            if (parent[v] >= 0) children[parent[v]].Add(v);

        int[] subtreeSize = new int[g.VertexCount];
        int CountSubtree(int u)
        {
            if (subtreeSize[u] != 0) return subtreeSize[u];
            int s = 1;
            foreach (int v in children[u]) s += CountSubtree(v);
            subtreeSize[u] = s;
            return s;
        }

        var rootsInS = new List<int>();
        var hasParent = new HashSet<int>();
        foreach (int v in W) if (parent[v] >= 0) hasParent.Add(v);
        foreach (int r in S)
            if (!hasParent.Contains(r))
            {
                int size = CountSubtree(r);
                if (size >= k) rootsInS.Add(r);
            }
        return (rootsInS.ToArray(), W);
    }

    private static bool Relax(double[] d, int[] pred, int u, int v, double w)
    {
        double newD = d[u] + w;
        if (newD > d[v]) return false;
        d[v] = newD;
        pred[v] = u;
        return true;
    }

    private static int Pow2(int exp) => exp <= 0 ? 1 : (1 << Math.Min(exp, 30));

    /// <summary>Data structure from Lemma 3.3: Insert, BatchPrepend, Pull.</summary>
    private sealed class FrontierDSSimple
    {
        private readonly int _m;
        private readonly double _B;
        private readonly Dictionary<int, double> _keyToValue = new();
        private readonly List<(double value, int key)> _list = new();
        private bool _sorted = true;
        private double _lastPullBound = double.PositiveInfinity;

        public FrontierDSSimple(int m, double b)
        {
            _m = Math.Max(1, m);
            _B = b;
        }

        public void Insert(int key, double value)
        {
            if (_keyToValue.TryGetValue(key, out double old))
            {
                if (value >= old) return;
                _list.RemoveAll(e => e.key == key);
            }
            _keyToValue[key] = value;
            _list.Add((value, key));
            _sorted = false;
        }

        public void BatchPrepend(List<(int key, double value)> pairs)
        {
            foreach (var (key, value) in pairs)
            {
                if (_keyToValue.TryGetValue(key, out double old) && value >= old) continue;
                _list.RemoveAll(e => e.key == key);
                _keyToValue[key] = value;
                _list.Add((value, key));
            }
            _sorted = false;
        }

        public bool TryPull(out double bound, out int[] keys)
        {
            if (_list.Count == 0)
            {
                bound = _B;
                keys = Array.Empty<int>();
                _lastPullBound = _B;
                return false;
            }
            if (!_sorted)
            {
                _list.Sort((a, b) =>
                {
                    int c = a.value.CompareTo(b.value);
                    return c != 0 ? c : a.key.CompareTo(b.key);
                });
                _sorted = true;
            }
            int take = Math.Min(_m, _list.Count);
            keys = new int[take];
            for (int i = 0; i < take; i++)
            {
                var (v, k) = _list[i];
                keys[i] = k;
                _keyToValue.Remove(k);
            }
            _list.RemoveRange(0, take);
            bound = _list.Count > 0 ? _list[0].value : _B;
            _lastPullBound = bound;
            return true;
        }

        public bool IsEmpty => _list.Count == 0;
        public double LastPullBound => _lastPullBound;
    }
}

/// <summary>Binary min-heap for (vertex, distance) with DecreaseKey.</summary>
internal sealed class MinHeap
{
    private readonly List<(int v, double d)> _heap = new();
    private readonly int[] _index; // vertex -> index in _heap, or -1

    public MinHeap(int maxVertex)
    {
        _index = new int[maxVertex];
        Array.Fill(_index, -1);
    }

    public bool IsEmpty => _heap.Count == 0;
    public bool Contains(int v) => v >= 0 && v < _index.Length && _index[v] >= 0;

    public void Insert(int v, double d)
    {
        _index[v] = _heap.Count;
        _heap.Add((v, d));
        Up(_heap.Count - 1);
    }

    public (int v, double d) ExtractMin()
    {
        var top = _heap[0];
        _index[top.v] = -1;
        _heap[0] = _heap[_heap.Count - 1];
        _heap.RemoveAt(_heap.Count - 1);
        if (_heap.Count > 0) _index[_heap[0].v] = 0;
        if (_heap.Count > 0) Down(0);
        return top;
    }

    public void DecreaseKey(int v, double newD)
    {
        int i = _index[v];
        if (i < 0 || _heap[i].d <= newD) return;
        _heap[i] = (v, newD);
        Up(i);
    }

    private void Up(int i)
    {
        while (i > 0)
        {
            int p = (i - 1) / 2;
            if (_heap[p].d <= _heap[i].d) break;
            Swap(i, p);
            i = p;
        }
    }

    private void Down(int i)
    {
        while (true)
        {
            int l = 2 * i + 1, r = 2 * i + 2, small = i;
            if (l < _heap.Count && _heap[l].d < _heap[small].d) small = l;
            if (r < _heap.Count && _heap[r].d < _heap[small].d) small = r;
            if (small == i) break;
            Swap(i, small);
            i = small;
        }
    }

    private void Swap(int i, int j)
    {
        var a = _heap[i]; var b = _heap[j];
        _heap[i] = b; _heap[j] = a;
        _index[a.v] = j; _index[b.v] = i;
    }
}
