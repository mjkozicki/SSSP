#include "graph.hpp"
#include "sssp.hpp"

#include <cassert>
#include <cmath>
#include <limits>
#include <vector>

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
    auto dijkstra_result = sssp::dijkstra(g, 0);
    auto r = sssp::duan_mao_shu_yin(g, 0);
    for (size_t i = 0; i < g.vertex_count(); ++i) {
      assert(std::fabs(dijkstra_result.distance[i] - r.distance[i]) < 1e-10);
    }
  }
  return 0;
}
