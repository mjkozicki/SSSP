<?php
/**
 * Load graph from file, run SSSP(0), print DONE. Path = argv[1] or GRAPH_FILE env.
 * Run from repo root: php benchmark/runners/run_php.php benchmark/data/graph.txt
 */
$repoRoot = getenv('REPO_ROOT') ?: dirname(__DIR__, 2);
$ssspPath = is_file($repoRoot . '/php/sssp.php') ? $repoRoot . '/php/sssp.php' : $repoRoot . '/sssp.php';
require_once $ssspPath;

$path = $argc > 1 ? $argv[1] : (getenv('GRAPH_FILE') ?: '');
if (!$path || !is_file($path)) {
    fwrite(STDERR, "Usage: run_php.php <graph.txt>\n");
    exit(1);
}

$f = fopen($path, 'r');
$line = fgets($f);
[$n, $m] = array_map('intval', explode(' ', trim($line)));
$g = new Graph($n);
for ($i = 0; $i < $m; $i++) {
    $line = fgets($f);
    [$u, $v, $w] = explode(' ', trim($line));
    $g->addEdge((int)$u, (int)$v, (float)$w);
}
fclose($f);

$algo = strtolower(trim((string) (getenv('SSSP_ALGORITHM') ?: 'duan_mao_shu_yin')));
$minSec = (float) (getenv('SSSP_MIN_SECONDS') ?: 0);
if ($minSec > 0) {
    $start = microtime(true);
    $iters = 0;
    while ((microtime(true) - $start) < $minSec) {
        $r = ($algo === 'dijkstra') ? dijkstra($g, 0) : duan_mao_shu_yin($g, 0);
        $iters++;
    }
    $reachable = count(array_filter($r->distance, fn($d) => $d !== INF));
    echo "DONE ", $r->vertexCount(), " ", $reachable, " ", $iters, "\n";
} else {
    $r = ($algo === 'dijkstra') ? dijkstra($g, 0) : duan_mao_shu_yin($g, 0);
    $reachable = count(array_filter($r->distance, fn($d) => $d !== INF));
    echo "DONE ", $r->vertexCount(), " ", $reachable, "\n";
}
