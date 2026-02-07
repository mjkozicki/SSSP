#ifndef SSSP_GRAPH_HPP
#define SSSP_GRAPH_HPP

#include <cstddef>
#include <utility>
#include <vector>

namespace sssp {

using Edge = std::pair<size_t, double>;

/** Lightweight view over a contiguous range of edges. Supports range-for. */
class OutEdgesView {
 public:
  OutEdgesView() : begin_(nullptr), end_(nullptr) {}
  OutEdgesView(const Edge* b, const Edge* e) : begin_(b), end_(e) {}

  const Edge* begin() const { return begin_; }
  const Edge* end() const { return end_; }
  size_t size() const { return static_cast<size_t>(end_ - begin_); }

 private:
  const Edge* begin_;
  const Edge* end_;
};

class Graph {
 public:
  explicit Graph(size_t vertex_count);
  size_t vertex_count() const { return out_edges_.size(); }
  size_t edge_count() const { return edge_count_; }
  void add_edge(size_t from, size_t to, double weight);
  /** Call after adding all edges for cache-friendly traversal. */
  void compact();
  OutEdgesView out_edges(size_t u) const;

 private:
  std::vector<std::vector<Edge>> out_edges_;
  size_t edge_count_ = 0;
  bool compact_ = false;
  std::vector<Edge> edges_;
  std::vector<size_t> offsets_;
};

}  // namespace sssp

#endif
