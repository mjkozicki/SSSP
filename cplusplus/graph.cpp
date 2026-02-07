#include "graph.hpp"

#include <stdexcept>

namespace sssp {

Graph::Graph(size_t vertex_count) : out_edges_(vertex_count) {}

void Graph::add_edge(size_t from, size_t to, double weight) {
  if (compact_) return;
  if (weight < 0) throw std::invalid_argument("edge weights must be non-negative");
  out_edges_[from].emplace_back(to, weight);
  ++edge_count_;
}

void Graph::compact() {
  if (compact_) return;
  const size_t n = out_edges_.size();
  offsets_.resize(n + 1);
  offsets_[0] = 0;
  for (size_t u = 0; u < n; ++u)
    offsets_[u + 1] = offsets_[u] + out_edges_[u].size();
  edges_.resize(edge_count_);
  size_t pos = 0;
  for (size_t u = 0; u < n; ++u) {
    for (const Edge& e : out_edges_[u]) {
      edges_[pos++] = e;
    }
  }
  compact_ = true;
}

OutEdgesView Graph::out_edges(size_t u) const {
  if (compact_) {
    const Edge* b = edges_.data() + offsets_[u];
    const Edge* e = edges_.data() + offsets_[u + 1];
    return OutEdgesView(b, e);
  }
  const auto& adj = out_edges_[u];
  return OutEdgesView(adj.data(), adj.data() + adj.size());
}

}  // namespace sssp
