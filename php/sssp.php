<?php

declare(strict_types=1);

/**
 * O(m log^{2/3} n) SSSP for directed graphs (Duan–Mao–Shu–Yin).
 * Graph: vertices 0..n-1, non-negative edge weights.
 */

const MAX_ITER = 100_000_000;
const EPS = 1e-12;

class Graph {
    /** @var list<list<array{0: int, 1: float}>> */
    private array $outEdges = [];
    private int $edgeCount = 0;

    public function __construct(int $vertexCount) {
        $this->outEdges = array_fill(0, $vertexCount, []);
    }

    public function vertexCount(): int {
        return count($this->outEdges);
    }

    public function edgeCount(): int {
        return $this->edgeCount;
    }

    public function addEdge(int $from, int $to, float $weight): void {
        if ($weight < 0) throw new InvalidArgumentException('edge weights must be non-negative');
        $this->outEdges[$from][] = [$to, $weight];
        $this->edgeCount++;
    }

    /** @return list<array{0: int, 1: float}> */
    public function outEdges(int $u): array {
        return $this->outEdges[$u];
    }
}

class SsspResult {
    /** @var list<float> */
    public array $distance;
    /** @var list<int|null> */
    public array $predecessor;

    /** @param list<float> $distance @param list<int|null> $predecessor */
    public function __construct(array $distance, array $predecessor) {
        $this->distance = $distance;
        $this->predecessor = $predecessor;
    }

    public function vertexCount(): int {
        return count($this->distance);
    }
}

function duan_mao_shu_yin(Graph $g, int $source): SsspResult {
    $n = $g->vertexCount();
    if ($n === 0) return new SsspResult([], []);

    $d = array_fill(0, $n, INF);
    $pred = array_fill(0, $n, null);
    $d[$source] = 0.0;

    $tLog = log(max($n, 2)) / log(2.0);
    $t = max(1, (int)floor($tLog ** (2/3)));
    $k = max(1, (int)floor($tLog ** (1/3)));
    $l = (int)ceil($tLog / $t);

    $s = [$source];
    bmssp($g, $d, $pred, $l, INF, $s, $n, $k, $t);

    return new SsspResult($d, $pred);
}

function relax(array &$d, array &$pred, int $u, int $v, float $w): void {
    $newD = $d[$u] + $w;
    if ($newD > $d[$v]) return;
    $d[$v] = $newD;
    $pred[$v] = $u;
}

function pow2(int $exp): int {
    if ($exp <= 0) return 1;
    return 1 << min($exp, 30);
}

function bmssp(Graph $g, array &$d, array &$pred, int $l, float $b, array $s, int $n, int $k, int $t): array {
    $twoLt = pow2($l * $t);
    if ($l === 0) return base_case($g, $d, $pred, $b, $s, $n, $k);

    [$p, $w] = find_pivots($g, $d, $pred, $b, $s, $k);
    $m = max(pow2(($l - 1) * $t), 1);
    $ds = new FrontierDS($m, $b);
    foreach ($p as $x) $ds->insert($x, $d[$x]);

    $b0Prime = $b;
    foreach ($p as $x) if ($d[$x] < $b0Prime) $b0Prime = $d[$x];

    $uSet = [];
    $lastBiPrime = $b0Prime;
    $iter = 0;

    while (count($uSet) < $k * $twoLt && $iter < MAX_ITER) {
        $pull = $ds->pull();
        if ($pull === null) break;
        [$bi, $si] = $pull;
        $iter++;
        [$biPrime, $ui] = bmssp($g, $d, $pred, $l - 1, $bi, $si, $n, $k, $t);
        $lastBiPrime = $biPrime;
        foreach ($ui as $u) $uSet[$u] = true;

        $kList = [];
        foreach ($ui as $u) {
            foreach ($g->outEdges($u) as $e) {
                [$v, $wE] = $e;
                $newD = $d[$u] + $wE;
                if ($newD > $d[$v]) continue;
                relax($d, $pred, $u, $v, $wE);
                if ($d[$v] >= $bi && $d[$v] < $b) $ds->insert($v, $d[$v]);
                elseif ($d[$v] >= $biPrime && $d[$v] < $bi) $kList[] = [$v, $d[$v]];
            }
        }
        foreach ($si as $x) if ($d[$x] >= $biPrime && $d[$x] < $bi) $kList[] = [$x, $d[$x]];
        $ds->batchPrepend($kList);

        if ($ds->isEmpty()) return [$b, array_keys($uSet)];
        if (count($uSet) > $k * $twoLt) return [$biPrime, array_keys($uSet)];
    }

    $bPrime = $iter > 0 ? $lastBiPrime : $b0Prime;
    foreach ($w as $x) if ($d[$x] < $bPrime) $uSet[$x] = true;
    return [$bPrime, array_keys($uSet)];
}

function base_case(Graph $g, array &$d, array &$pred, float $b, array $s, int $n, int $k): array {
    $x = $s[0];
    $u0 = [];
    $heap = new MinHeap($n);
    $heap->insert($x, $d[$x]);

    while (!$heap->isEmpty() && count($u0) < $k + 1) {
        [$u, $du] = $heap->extractMin();
        $u0[] = $u;
        foreach ($g->outEdges($u) as $e) {
            [$v, $wE] = $e;
            $newD = $du + $wE;
            if ($newD >= $b || $newD > $d[$v]) continue;
            relax($d, $pred, $u, $v, $wE);
            if ($heap->contains($v)) $heap->decreaseKey($v, $d[$v]);
            else $heap->insert($v, $d[$v]);
        }
    }

    if (count($u0) <= $k) return [$b, $u0];
    $bPrime = $b;
    foreach ($u0 as $v) if ($d[$v] > $bPrime) $bPrime = $d[$v];
    $filtered = [];
    foreach ($u0 as $v) if ($d[$v] < $bPrime) $filtered[] = $v;
    return [$bPrime, $filtered];
}

function find_pivots(Graph $g, array &$d, array &$pred, float $b, array $s, int $k): array {
    $w = $s;
    $wi = $s;
    for ($round = 1; $round <= $k; $round++) {
        $wiNext = [];
        foreach ($wi as $u) {
            foreach ($g->outEdges($u) as $e) {
                [$v, $wE] = $e;
                $newD = $d[$u] + $wE;
                if ($newD > $d[$v]) continue;
                relax($d, $pred, $u, $v, $wE);
                if ($newD < $b) $wiNext[] = $v;
            }
        }
        $w = array_merge($w, $wiNext);
        $wi = $wiNext;
        if (count($w) > $k * count($s)) return [$s, $w];
    }

    $inW = array_flip($w);
    $parent = array_fill(0, $g->vertexCount(), null);
    foreach ($w as $u) {
        foreach ($g->outEdges($u) as $e) {
            [$v, $wE] = $e;
            if (isset($inW[$v]) && abs($d[$v] - ($d[$u] + $wE)) < EPS && $parent[$v] === null)
                $parent[$v] = $u;
        }
    }

    $children = array_fill(0, $g->vertexCount(), []);
    foreach ($w as $v) if ($parent[$v] !== null) $children[$parent[$v]][] = $v;

    $subtreeSize = array_fill(0, $g->vertexCount(), 0);
    $countSubtree = function(int $u) use (&$children, &$subtreeSize, &$countSubtree): int {
        if ($subtreeSize[$u] !== 0) return $subtreeSize[$u];
        $s = 1;
        foreach ($children[$u] as $v) $s += $countSubtree($v);
        $subtreeSize[$u] = $s;
        return $s;
    };

    $hasParent = [];
    foreach ($w as $v) if ($parent[$v] !== null) $hasParent[$v] = true;
    $rootsInS = [];
    foreach ($s as $r) {
        if (!isset($hasParent[$r]) && $countSubtree($r) >= $k) $rootsInS[] = $r;
    }
    return [$rootsInS, $w];
}

class FrontierDS {
    private int $m;
    private float $b;
    /** @var array<int, float> */
    private array $keyToValue = [];
    /** @var list<array{0: float, 1: int}> */
    private array $list = [];
    private bool $sorted = true;

    public function __construct(int $m, float $b) {
        $this->m = max($m, 1);
        $this->b = $b;
    }

    public function insert(int $key, float $value): void {
        if (isset($this->keyToValue[$key]) && $value >= $this->keyToValue[$key]) return;
        $this->list = array_values(array_filter($this->list, fn($e) => $e[1] !== $key));
        $this->keyToValue[$key] = $value;
        $this->list[] = [$value, $key];
        $this->sorted = false;
    }

    /** @param list<array{0: int, 1: float}> $pairs */
    public function batchPrepend(array $pairs): void {
        foreach ($pairs as [$key, $value]) {
            if (isset($this->keyToValue[$key]) && $value >= $this->keyToValue[$key]) continue;
            $this->list = array_values(array_filter($this->list, fn($e) => $e[1] !== $key));
            $this->keyToValue[$key] = $value;
            $this->list[] = [$value, $key];
        }
        $this->sorted = false;
    }

    /** @return array{0: float, 1: list<int>}|null */
    public function pull(): ?array {
        if ($this->list === []) return null;
        if (!$this->sorted) {
            usort($this->list, fn($a, $b) => $a[0] <=> $b[0] ?: $a[1] <=> $b[1]);
            $this->sorted = true;
        }
        $take = min($this->m, count($this->list));
        $keys = [];
        for ($i = 0; $i < $take; $i++) {
            $keys[] = $this->list[$i][1];
            unset($this->keyToValue[$this->list[$i][1]]);
        }
        array_splice($this->list, 0, $take);
        $bound = $this->list !== [] ? $this->list[0][0] : $this->b;
        return [$bound, $keys];
    }

    public function isEmpty(): bool {
        return $this->list === [];
    }
}

class MinHeap {
    /** @var list<array{0: int, 1: float}> */
    private array $heap = [];
    /** @var list<int> */
    private array $index = [];

    public function __construct(int $maxVertex) {
        $this->index = array_fill(0, $maxVertex, -1);
    }

    public function isEmpty(): bool {
        return $this->heap === [];
    }

    public function contains(int $v): bool {
        return $v < count($this->index) && $this->index[$v] >= 0;
    }

    public function insert(int $v, float $dist): void {
        $i = count($this->heap);
        $this->index[$v] = $i;
        $this->heap[] = [$v, $dist];
        $this->siftUp($i);
    }

    /** @return array{0: int, 1: float} */
    public function extractMin(): array {
        $top = $this->heap[0];
        $this->index[$top[0]] = -1;
        $this->heap[0] = $this->heap[count($this->heap) - 1];
        array_pop($this->heap);
        if ($this->heap !== []) $this->index[$this->heap[0][0]] = 0;
        if ($this->heap !== []) $this->siftDown(0);
        return $top;
    }

    public function decreaseKey(int $v, float $newD): void {
        $i = $this->index[$v];
        if ($i < 0 || $this->heap[$i][1] <= $newD) return;
        $this->heap[$i] = [$v, $newD];
        $this->siftUp($i);
    }

    private function siftUp(int $i): void {
        while ($i > 0) {
            $p = (int)(($i - 1) / 2);
            if ($this->heap[$p][1] <= $this->heap[$i][1]) break;
            $this->swap($i, $p);
            $i = $p;
        }
    }

    private function siftDown(int $i): void {
        while (true) {
            $l = 2 * $i + 1;
            $r = 2 * $i + 2;
            $small = $i;
            if ($l < count($this->heap) && $this->heap[$l][1] < $this->heap[$small][1]) $small = $l;
            if ($r < count($this->heap) && $this->heap[$r][1] < $this->heap[$small][1]) $small = $r;
            if ($small === $i) break;
            $this->swap($i, $small);
            $i = $small;
        }
    }

    private function swap(int $i, int $j): void {
        $a = $this->heap[$i];
        $b = $this->heap[$j];
        $this->heap[$i] = $b;
        $this->heap[$j] = $a;
        $this->index[$a[0]] = $j;
        $this->index[$b[0]] = $i;
    }
}
