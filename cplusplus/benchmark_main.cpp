#include "graph.hpp"
#include "sssp.hpp"

#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
  std::string path;
  if (const char* e = std::getenv("GRAPH_FILE")) path = e;
  if (argc > 1) path = argv[1];
  if (path.empty()) {
    std::cerr << "Usage: benchmark <graph.txt>\n";
    return 1;
  }
  std::ifstream f(path);
  if (!f) {
    std::cerr << "Cannot open " << path << "\n";
    return 1;
  }
  size_t n, m;
  f >> n >> m;
  sssp::Graph g(n);
  for (size_t i = 0; i < m; i++) {
    size_t u, v;
    double w;
    f >> u >> v >> w;
    g.add_edge(u, v, w);
  }
  auto r = sssp::duan_mao_shu_yin(g, 0);
  size_t reachable = 0;
  for (double d : r.distance)
    if (std::isfinite(d)) reachable++;
  std::cout << "DONE " << r.vertex_count() << " " << reachable << "\n";
  return 0;
}
