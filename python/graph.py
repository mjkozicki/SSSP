"""Directed graph with non-negative edge weights. Vertices are 0..vertex_count-1."""

class Graph:
    def __init__(self, vertex_count: int):
        self._out_edges: list[list[tuple[int, float]]] = [[] for _ in range(vertex_count)]
        self._edge_count = 0

    def vertex_count(self) -> int:
        return len(self._out_edges)

    def edge_count(self) -> int:
        return self._edge_count

    def add_edge(self, from_: int, to: int, weight: float) -> None:
        if weight < 0:
            raise ValueError("edge weights must be non-negative")
        self._out_edges[from_].append((to, weight))
        self._edge_count += 1

    def out_edges(self, u: int) -> list[tuple[int, float]]:
        return self._out_edges[u]
