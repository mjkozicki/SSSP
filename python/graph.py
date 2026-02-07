"""Directed graph with non-negative edge weights. Vertices are 0..vertex_count-1.
Call compact() after adding all edges for cache-friendly traversal."""


class Graph:
    def __init__(self, vertex_count: int):
        self._out_edges: list[list[tuple[int, float]]] = [[] for _ in range(vertex_count)]
        self._edge_count = 0
        self._compact = False
        self._edges: list[tuple[int, float]] = []
        self._offsets: list[int] = []

    def vertex_count(self) -> int:
        return len(self._out_edges)

    def edge_count(self) -> int:
        return self._edge_count

    def add_edge(self, from_: int, to: int, weight: float) -> None:
        if self._compact:
            return
        if weight < 0:
            raise ValueError("edge weights must be non-negative")
        self._out_edges[from_].append((to, weight))
        self._edge_count += 1

    def compact(self) -> None:
        """Build a single flat edge list for better cache locality. Call once after adding all edges."""
        if self._compact:
            return
        n = self.vertex_count()
        self._offsets = [0]
        for u in range(n):
            self._offsets.append(self._offsets[-1] + len(self._out_edges[u]))
        self._edges = []
        for u in range(n):
            self._edges.extend(self._out_edges[u])
        self._compact = True

    def out_edges(self, u: int) -> list[tuple[int, float]]:
        if self._compact:
            return self._edges[self._offsets[u] : self._offsets[u + 1]]
        return self._out_edges[u]
