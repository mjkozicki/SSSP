#ifndef SSSP_GRAPH_HPP
#define SSSP_GRAPH_HPP

#include <cstddef>
#include <vector>

namespace sssp {

class Graph {
 public:
  explicit Graph(size_t vertex_count);
  size_t vertex_count() const { return out_edges_.size(); }
  size_t edge_count() const { return edge_count_; }
  void add_edge(size_t from, size_t to, double weight);
  const std::vector<std::pair<size_t, double>>& out_edges(size_t u) const;

 private:
  std::vector<std::vector<std::pair<size_t, double>>> out_edges_;
  size_t edge_count_ = 0;
};

}  // namespace sssp

#endif
