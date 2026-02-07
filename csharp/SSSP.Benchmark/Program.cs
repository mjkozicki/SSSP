using SSSP;

string path = Environment.GetEnvironmentVariable("GRAPH_FILE") ?? (args.Length > 0 ? args[0] : "") ?? "";
if (string.IsNullOrEmpty(path) || !File.Exists(path))
{
    Console.Error.WriteLine("Usage: benchmark <graph.txt>");
    Environment.Exit(1);
}

var g = LoadGraph(path);
var r = DuanMaoShuYinSSSP.Solve(g, 0);
int reachable = r.Distance.Count(d => double.IsFinite(d));
Console.WriteLine($"DONE {r.VertexCount} {reachable}");

static Graph LoadGraph(string path)
{
    using var f = File.OpenText(path);
    var first = f.ReadLine()!.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    int n = int.Parse(first[0]), m = int.Parse(first[1]);
    var g = new Graph(n);
    for (int i = 0; i < m; i++)
    {
        var line = f.ReadLine()!.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        g.AddEdge(int.Parse(line[0]), int.Parse(line[1]), double.Parse(line[2]));
    }
    return g;
}
