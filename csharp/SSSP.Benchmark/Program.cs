using SSSP;

string path = Environment.GetEnvironmentVariable("GRAPH_FILE") ?? (args.Length > 0 ? args[0] : "") ?? "";
if (string.IsNullOrEmpty(path) || !File.Exists(path))
{
    Console.Error.WriteLine("Usage: benchmark <graph.txt>");
    Environment.Exit(1);
}

var g = LoadGraph(path);
var algo = (Environment.GetEnvironmentVariable("SSSP_ALGORITHM") ?? "duan_mao_shu_yin").Trim().ToLowerInvariant();
int fixedIters = int.TryParse(Environment.GetEnvironmentVariable("SSSP_ITERATIONS") ?? "", System.Globalization.NumberStyles.Integer, System.Globalization.CultureInfo.InvariantCulture, out var fi) ? fi : 0;
var minSecRaw = Environment.GetEnvironmentVariable("SSSP_MIN_SECONDS");
double minSec = double.TryParse(minSecRaw, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out var ms) ? ms : 0;
var maxSecRaw = Environment.GetEnvironmentVariable("SSSP_MAX_SECONDS");
double maxSec = double.TryParse(maxSecRaw, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out var mx) ? mx : 30;
SSSPResult r;
int iterations = 1;
if (fixedIters > 0)
{
    r = algo == "dijkstra" ? Dijkstra.Solve(g, 0) : DuanMaoShuYinSSSP.Solve(g, 0);
    for (int i = 1; i < fixedIters; i++)
        r = algo == "dijkstra" ? Dijkstra.Solve(g, 0) : DuanMaoShuYinSSSP.Solve(g, 0);
    iterations = fixedIters;
}
else if (minSec > 0)
{
    var sw = System.Diagnostics.Stopwatch.StartNew();
    r = algo == "dijkstra" ? Dijkstra.Solve(g, 0) : DuanMaoShuYinSSSP.Solve(g, 0);
    iterations = 1;
    while (sw.Elapsed.TotalSeconds < minSec && sw.Elapsed.TotalSeconds < maxSec)
    {
        r = algo == "dijkstra" ? Dijkstra.Solve(g, 0) : DuanMaoShuYinSSSP.Solve(g, 0);
        iterations++;
    }
}
else
{
    r = algo == "dijkstra" ? Dijkstra.Solve(g, 0) : DuanMaoShuYinSSSP.Solve(g, 0);
}
var resultFile = Environment.GetEnvironmentVariable("RESULT_FILE");
if (!string.IsNullOrEmpty(resultFile))
    File.WriteAllText(resultFile, $"{{\"iterations\":{iterations}}}");

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
