#ifndef SSSP_SSSP_HPP
#define SSSP_SSSP_HPP

#include <cstddef>
#include <optional>
#include <vector>

#include "graph.hpp"

namespace sssp {

struct SsspResult {
  std::vector<double> distance;
  std::vector<std::optional<size_t>> predecessor;
  size_t vertex_count() const { return distance.size(); }
};

SsspResult duan_mao_shu_yin(const Graph& g, size_t source);

}  // namespace sssp

#endif
