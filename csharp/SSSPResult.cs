namespace SSSP;

/// <summary>
/// Result of single-source shortest path: distances and predecessor pointers.
/// Distance is double.PositiveInfinity for unreachable vertices.
/// Predecessor is -1 for source and unreachable vertices.
/// </summary>
public sealed class SSSPResult
{
    /// <summary>Distance from source to each vertex.</summary>
    public double[] Distance { get; }

    /// <summary>Predecessor on shortest path; -1 if none (source or unreachable).</summary>
    public int[] Predecessor { get; }

    public int VertexCount => Distance.Length;

    public SSSPResult(int n)
    {
        Distance = new double[n];
        Predecessor = new int[n];
    }
}
