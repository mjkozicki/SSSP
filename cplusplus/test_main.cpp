#include "graph.hpp"
#include "sssp.hpp"

#include <cassert>
#include <cmath>
#include <limits>
#include <vector>

static std::vector<double> dijkstra(const sssp::Graph& g, size_t source) {
  size_t n = g.vertex_count();
  std::vector<double> dist(n, std::numeric_limits<double>::infinity());
  dist[source] = 0;
  std::vector<bool> done(n, false);
  for (size_t round = 0; round < n; ++round) {
    size_t u = n;
    double best = std::numeric_limits<double>::infinity();
    for (size_t i = 0; i < n; ++i)
      if (!done[i] && dist[i] < best) {
        best = dist[i];
        u = i;
      }
    if (u >= n || best == std::numeric_limits<double>::infinity()) break;
    done[u] = true;
    for (const auto& [to, w] : g.out_edges(u)) {
      double d = dist[u] + w;
      if (d < dist[to]) dist[to] = d;
    }
  }
  return dist;
}

int main() {
  {
    sssp::Graph g(1);
    auto r = sssp::duan_mao_shu_yin(g, 0);
    assert(r.distance.size() == 1);
    assert(r.distance[0] == 0.0);
  }
  {
    sssp::Graph g(2);
    g.add_edge(0, 1, 3.0);
    auto r = sssp::duan_mao_shu_yin(g, 0);
    assert(r.distance[0] == 0.0);
    assert(r.distance[1] == 3.0);
    assert(r.predecessor[1] && *r.predecessor[1] == 0);
  }
  {
    sssp::Graph g(6);
    g.add_edge(0, 1, 2.0);
    g.add_edge(0, 2, 5.0);
    g.add_edge(1, 2, 2.0);
    g.add_edge(1, 3, 7.0);
    g.add_edge(2, 3, 1.0);
    g.add_edge(2, 4, 6.0);
    g.add_edge(3, 4, 3.0);
    g.add_edge(3, 5, 9.0);
    g.add_edge(4, 5, 1.0);
    auto dijkstra_dist = dijkstra(g, 0);
    auto r = sssp::duan_mao_shu_yin(g, 0);
    for (size_t i = 0; i < g.vertex_count(); ++i)
      assert(std::fabs(dijkstra_dist[i] - r.distance[i]) < 1e-10);
  }
  return 0;
}
