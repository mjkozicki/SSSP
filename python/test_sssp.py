import math
from graph import Graph
from sssp import duan_mao_shu_yin


def dijkstra(g: Graph, source: int) -> list[float]:
    n = g.vertex_count()
    dist = [math.inf] * n
    dist[source] = 0
    done = [False] * n
    for _ in range(n):
        u = -1
        best = math.inf
        for i in range(n):
            if not done[i] and dist[i] < best:
                best = dist[i]
                u = i
        if u < 0 or math.isinf(best):
            break
        done[u] = True
        for v, w in g.out_edges(u):
            d = dist[u] + w
            if d < dist[v]:
                dist[v] = d
    return dist


def test_single_vertex():
    g = Graph(1)
    r = duan_mao_shu_yin(g, 0)
    assert r.distance[0] == 0


def test_two_vertices():
    g = Graph(2)
    g.add_edge(0, 1, 3)
    r = duan_mao_shu_yin(g, 0)
    assert r.distance[0] == 0 and r.distance[1] == 3
    assert r.predecessor[1] == 0


def test_matches_dijkstra():
    g = Graph(6)
    g.add_edge(0, 1, 2)
    g.add_edge(0, 2, 5)
    g.add_edge(1, 2, 2)
    g.add_edge(1, 3, 7)
    g.add_edge(2, 3, 1)
    g.add_edge(2, 4, 6)
    g.add_edge(3, 4, 3)
    g.add_edge(3, 5, 9)
    g.add_edge(4, 5, 1)
    ref = dijkstra(g, 0)
    r = duan_mao_shu_yin(g, 0)
    for i in range(g.vertex_count()):
        assert abs(ref[i] - r.distance[i]) < 1e-10, f"vertex {i}"


if __name__ == "__main__":
    test_single_vertex()
    test_two_vertices()
    test_matches_dijkstra()
    print("All tests passed.")
