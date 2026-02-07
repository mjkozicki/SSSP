"""O(m log^{2/3} n) SSSP (Duan–Mao–Shu–Yin) for directed graphs with non-negative weights."""

from __future__ import annotations

import heapq
import math
from typing import Optional

from graph import Graph

MAX_ITER = 100_000_000
EPS = 1e-12


def dijkstra(g: Graph, source: int) -> SsspResult:
    """Dijkstra's algorithm: O((V+E) log V) SSSP with a min-heap. Returns same result type as duan_mao_shu_yin."""
    n = g.vertex_count()
    if n == 0:
        return SsspResult([], [])
    dist = [math.inf] * n
    pred: list[Optional[int]] = [None] * n
    dist[source] = 0.0
    # Min-heap: (distance, vertex). We push (d, v) when we relax; skip when stale.
    heap: list[tuple[float, int]] = [(0.0, source)]
    while heap:
        du, u = heapq.heappop(heap)
        if du > dist[u]:
            continue
        adj = g.out_edges(u)
        for i in range(len(adj)):
            v, w = adj[i]
            new_d = dist[u] + w
            if new_d < dist[v]:
                dist[v] = new_d
                pred[v] = u
                heapq.heappush(heap, (new_d, v))
    return SsspResult(dist, pred)


class SsspResult:
    def __init__(self, distance: list[float], predecessor: list[Optional[int]]):
        self.distance = distance
        self.predecessor = predecessor

    def vertex_count(self) -> int:
        return len(self.distance)


def duan_mao_shu_yin(g: Graph, source: int) -> SsspResult:
    n = g.vertex_count()
    if n == 0:
        return SsspResult([], [])

    d = [math.inf] * n
    pred: list[Optional[int]] = [None] * n
    d[source] = 0.0

    t_log = math.log(max(n, 2)) / math.log(2.0)
    t = max(1, int(math.floor(t_log ** (2 / 3))))
    k = max(1, int(math.floor(t_log ** (1 / 3))))
    l = int(math.ceil(t_log / t))

    s = [source]
    bmssp(g, d, pred, l, math.inf, s, n, k, t)

    return SsspResult(d, pred)


def _relax(d: list[float], pred: list[Optional[int]], u: int, v: int, w: float) -> None:
    new_d = d[u] + w
    if new_d >= d[v]:
        return
    d[v] = new_d
    pred[v] = u


def _pow2(exp: int) -> int:
    if exp <= 0:
        return 1
    return 1 << min(exp, 30)


class _MinHeap:
    def __init__(self, max_vertex: int):
        self._heap: list[tuple[int, float]] = []
        self._index = [-1] * max_vertex

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def contains(self, v: int) -> bool:
        return v < len(self._index) and self._index[v] >= 0

    def insert(self, v: int, dist: float) -> None:
        i = len(self._heap)
        self._index[v] = i
        self._heap.append((v, dist))
        self._sift_up(i)

    def extract_min(self) -> tuple[int, float]:
        top = self._heap[0]
        self._index[top[0]] = -1
        self._heap[0] = self._heap[-1]
        self._heap.pop()
        if self._heap:
            self._index[self._heap[0][0]] = 0
            self._sift_down(0)
        return top

    def decrease_key(self, v: int, new_d: float) -> None:
        i = self._index[v]
        if i < 0 or self._heap[i][1] <= new_d:
            return
        self._heap[i] = (v, new_d)
        self._sift_up(i)

    def _sift_up(self, i: int) -> None:
        while i > 0:
            p = (i - 1) // 2
            if self._heap[p][1] <= self._heap[i][1]:
                break
            self._swap(i, p)
            i = p

    def _sift_down(self, i: int) -> None:
        while True:
            l, r, small = 2 * i + 1, 2 * i + 2, i
            if l < len(self._heap) and self._heap[l][1] < self._heap[small][1]:
                small = l
            if r < len(self._heap) and self._heap[r][1] < self._heap[small][1]:
                small = r
            if small == i:
                break
            self._swap(i, small)
            i = small

    def _swap(self, i: int, j: int) -> None:
        a, b = self._heap[i], self._heap[j]
        self._heap[i], self._heap[j] = b, a
        self._index[a[0]], self._index[b[0]] = j, i


class _FrontierDS:
    def __init__(self, m: int, b: float):
        self._m = max(m, 1)
        self._b = b
        self._key_to_value: dict[int, float] = {}
        self._list: list[tuple[float, int]] = []
        self._sorted = True

    def insert(self, key: int, value: float) -> None:
        if key in self._key_to_value and value >= self._key_to_value[key]:
            return
        self._list = [(v, k) for v, k in self._list if k != key]
        self._key_to_value[key] = value
        self._list.append((value, key))
        self._sorted = False

    def batch_prepend(self, pairs: list[tuple[int, float]]) -> None:
        for key, value in pairs:
            if key in self._key_to_value and value >= self._key_to_value[key]:
                continue
            self._list = [(v, k) for v, k in self._list if k != key]
            self._key_to_value[key] = value
            self._list.append((value, key))
        self._sorted = False

    def pull(self) -> Optional[tuple[float, list[int]]]:
        if not self._list:
            return None
        if not self._sorted:
            self._list.sort(key=lambda x: (x[0], x[1]))
            self._sorted = True
        take = min(self._m, len(self._list))
        keys = [self._list[i][1] for i in range(take)]
        for k in keys:
            del self._key_to_value[k]
        self._list = self._list[take:]
        bound = self._list[0][0] if self._list else self._b
        return (bound, keys)

    def is_empty(self) -> bool:
        return len(self._list) == 0


def _base_case(
    g: Graph,
    d: list[float],
    pred: list[Optional[int]],
    b: float,
    s: list[int],
    n: int,
    k: int,
) -> tuple[float, list[int]]:
    x = s[0]
    u0: list[int] = []
    heap = _MinHeap(n)
    heap.insert(x, d[x])

    while not heap.is_empty() and len(u0) < k + 1:
        u, du = heap.extract_min()
        u0.append(u)
        for v, w_e in g.out_edges(u):
            new_d = du + w_e
            if new_d >= b or new_d > d[v]:
                continue
            _relax(d, pred, u, v, w_e)
            if heap.contains(v):
                heap.decrease_key(v, d[v])
            else:
                heap.insert(v, d[v])

    if len(u0) <= k:
        return (b, u0)
    b_prime = max(d[v] for v in u0)
    return (b_prime, [v for v in u0 if d[v] < b_prime])


def _count_subtree(u: int, children: list[list[int]], size: list[int]) -> int:
    if size[u] != 0:
        return size[u]
    s = 1
    for v in children[u]:
        s += _count_subtree(v, children, size)
    size[u] = s
    return s


def _find_pivots(
    g: Graph,
    d: list[float],
    pred: list[Optional[int]],
    b: float,
    s: list[int],
    k: int,
) -> tuple[list[int], list[int]]:
    w = list(s)
    wi = list(s)
    for _ in range(1, k + 1):
        wi_next: list[int] = []
        for u in wi:
            for v, w_e in g.out_edges(u):
                new_d = d[u] + w_e
                if new_d > d[v]:
                    continue
                _relax(d, pred, u, v, w_e)
                if new_d < b:
                    wi_next.append(v)
        w.extend(wi_next)
        wi = wi_next
        if len(w) > k * len(s):
            return (list(s), w)

    in_w = set(w)
    parent: list[Optional[int]] = [None] * g.vertex_count()
    for u in w:
        for v, w_e in g.out_edges(u):
            if v in in_w and abs(d[v] - (d[u] + w_e)) < EPS and parent[v] is None:
                parent[v] = u

    children: list[list[int]] = [[] for _ in range(g.vertex_count())]
    for v in w:
        if parent[v] is not None:
            children[parent[v]].append(v)

    subtree_size = [0] * g.vertex_count()
    has_parent = {v for v in w if parent[v] is not None}
    roots_in_s = [r for r in s if r not in has_parent and _count_subtree(r, children, subtree_size) >= k]
    return (roots_in_s, w)


def bmssp(
    g: Graph,
    d: list[float],
    pred: list[Optional[int]],
    l: int,
    b: float,
    s: list[int],
    n: int,
    k: int,
    t: int,
) -> tuple[float, list[int]]:
    two_lt = _pow2(l * t)
    if l == 0:
        return _base_case(g, d, pred, b, s, n, k)

    p, w = _find_pivots(g, d, pred, b, s, k)
    m = max(_pow2((l - 1) * t), 1)
    ds = _FrontierDS(m, b)
    for x in p:
        ds.insert(x, d[x])

    b0_prime = min((d[x] for x in p), default=b)
    u_set: set[int] = set()
    last_bi_prime = b0_prime
    iter_count = 0

    while len(u_set) < k * two_lt and iter_count < MAX_ITER:
        pull_result = ds.pull()
        if pull_result is None:
            break
        bi, si = pull_result
        iter_count += 1
        bi_prime, ui = bmssp(g, d, pred, l - 1, bi, si, n, k, t)
        last_bi_prime = bi_prime
        u_set.update(ui)

        k_list: list[tuple[int, float]] = []
        for u in ui:
            adj = g.out_edges(u)
            for i in range(len(adj)):
                v, w_e = adj[i]
                new_d = d[u] + w_e
                if new_d > d[v]:
                    continue
                _relax(d, pred, u, v, w_e)
                if d[v] >= bi and d[v] < b:
                    ds.insert(v, d[v])
                elif d[v] >= bi_prime and d[v] < bi:
                    k_list.append((v, d[v]))
        for x in si:
            if d[x] >= bi_prime and d[x] < bi:
                k_list.append((x, d[x]))
        ds.batch_prepend(k_list)

        if ds.is_empty():
            return (b, list(u_set))
        if len(u_set) > k * two_lt:
            return (bi_prime, list(u_set))

    b_prime = last_bi_prime if iter_count > 0 else b0_prime
    for x in w:
        if d[x] < b_prime:
            u_set.add(x)
    return (b_prime, list(u_set))
