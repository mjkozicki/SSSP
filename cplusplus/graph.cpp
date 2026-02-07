#include "graph.hpp"

#include <stdexcept>

namespace sssp {

Graph::Graph(size_t vertex_count) : out_edges_(vertex_count) {}

void Graph::add_edge(size_t from, size_t to, double weight) {
  if (weight < 0) throw std::invalid_argument("edge weights must be non-negative");
  out_edges_[from].emplace_back(to, weight);
  ++edge_count_;
}

const std::vector<std::pair<size_t, double>>& Graph::out_edges(size_t u) const {
  return out_edges_[u];
}

}  // namespace sssp
