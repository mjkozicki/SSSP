#include "sssp.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>

namespace sssp {

namespace {

constexpr size_t kMaxIter = 100000000;
constexpr double kEps = 1e-12;
constexpr double kInf = std::numeric_limits<double>::infinity();

size_t Pow2(size_t exp) {
  if (exp == 0) return 1;
  return size_t(1) << std::min(exp, size_t(30));
}

void Relax(std::vector<double>& d, std::vector<std::optional<size_t>>& pred,
           size_t u, size_t v, double w) {
  double new_d = d[u] + w;
  if (new_d > d[v]) return;
  d[v] = new_d;
  pred[v] = u;
}

int F64Cmp(double a, double b) {
  if (a < b) return -1;
  if (a > b) return 1;
  return 0;
}

// --- MinHeap ---
class MinHeap {
 public:
  explicit MinHeap(size_t max_vertex)
      : index_(max_vertex, static_cast<size_t>(-1)) {}

  bool is_empty() const { return heap_.empty(); }
  bool contains(size_t v) const {
    return v < index_.size() && index_[v] != static_cast<size_t>(-1);
  }

  void insert(size_t v, double dist) {
    size_t i = heap_.size();
    index_[v] = i;
    heap_.emplace_back(v, dist);
    sift_up(i);
  }

  std::pair<size_t, double> extract_min() {
    auto top = heap_.front();
    index_[top.first] = static_cast<size_t>(-1);
    heap_.front() = heap_.back();
    heap_.pop_back();
    if (!heap_.empty()) {
      index_[heap_.front().first] = 0;
      sift_down(0);
    }
    return top;
  }

  void decrease_key(size_t v, double new_d) {
    size_t i = index_[v];
    if (i == static_cast<size_t>(-1) || heap_[i].second <= new_d) return;
    heap_[i] = {v, new_d};
    sift_up(i);
  }

 private:
  std::vector<std::pair<size_t, double>> heap_;
  std::vector<size_t> index_;

  void sift_up(size_t i) {
    while (i > 0) {
      size_t p = (i - 1) / 2;
      if (heap_[p].second <= heap_[i].second) break;
      swap(i, p);
      i = p;
    }
  }

  void sift_down(size_t i) {
    while (true) {
      size_t l = 2 * i + 1, r = 2 * i + 2, small = i;
      if (l < heap_.size() && heap_[l].second < heap_[small].second) small = l;
      if (r < heap_.size() && heap_[r].second < heap_[small].second) small = r;
      if (small == i) break;
      swap(i, small);
      i = small;
    }
  }

  void swap(size_t i, size_t j) {
    std::pair<size_t, double> a = heap_[i], b = heap_[j];
    heap_[i] = b;
    heap_[j] = a;
    index_[a.first] = j;
    index_[b.first] = i;
  }
};

// --- FrontierDS ---
class FrontierDS {
 public:
  FrontierDS(size_t m, double b) : m_(std::max(m, size_t(1))), b_(b) {}

  void insert(size_t key, double value) {
    auto it = key_to_value_.find(key);
    if (it != key_to_value_.end()) {
      if (value >= it->second) return;
      list_.erase(std::remove_if(list_.begin(), list_.end(),
                                 [key](const auto& p) { return p.second == key; }),
                  list_.end());
    }
    key_to_value_[key] = value;
    list_.emplace_back(value, key);
    sorted_ = false;
  }

  void batch_prepend(const std::vector<std::pair<size_t, double>>& pairs) {
    for (const auto& [key, value] : pairs) {
      auto it = key_to_value_.find(key);
      if (it != key_to_value_.end() && value >= it->second) continue;
      list_.erase(std::remove_if(list_.begin(), list_.end(),
                                 [key](const auto& p) { return p.second == key; }),
                  list_.end());
      key_to_value_[key] = value;
      list_.emplace_back(value, key);
    }
    sorted_ = false;
  }

  bool pull(double& bound, std::vector<size_t>& keys) {
    if (list_.empty()) {
      bound = b_;
      return false;
    }
    if (!sorted_) {
      std::sort(list_.begin(), list_.end(), [](const auto& a, const auto& b) {
        int c = F64Cmp(a.first, b.first);
        return c != 0 ? c < 0 : a.second < b.second;
      });
      sorted_ = true;
    }
    size_t take = std::min(m_, list_.size());
    keys.clear();
    keys.reserve(take);
    for (size_t i = 0; i < take; ++i) {
      keys.push_back(list_[i].second);
      key_to_value_.erase(list_[i].second);
    }
    list_.erase(list_.begin(), list_.begin() + static_cast<std::ptrdiff_t>(take));
    bound = list_.empty() ? b_ : list_.front().first;
    return true;
  }

  bool is_empty() const { return list_.empty(); }

 private:
  size_t m_;
  double b_;
  std::unordered_map<size_t, double> key_to_value_;
  std::vector<std::pair<double, size_t>> list_;
  bool sorted_ = true;
};

static size_t count_subtree(size_t u, const std::vector<std::vector<size_t>>& children,
                            std::vector<size_t>& size) {
  if (size[u] != 0) return size[u];
  size_t s = 1;
  for (size_t v : children[u]) s += count_subtree(v, children, size);
  size[u] = s;
  return s;
}

std::pair<std::vector<size_t>, std::vector<size_t>> find_pivots(
    const Graph& g, std::vector<double>& d,
    std::vector<std::optional<size_t>>& pred, double b,
    const std::vector<size_t>& s, size_t k) {
  std::vector<size_t> w = s, wi = s;

  for (size_t round = 1; round <= k; ++round) {
    std::vector<size_t> wi_next;
    for (size_t u : wi) {
      for (const auto& [v, w_e] : g.out_edges(u)) {
        double new_d = d[u] + w_e;
        if (new_d > d[v]) continue;
        Relax(d, pred, u, v, w_e);
        if (new_d < b) wi_next.push_back(v);
      }
    }
    for (size_t v : wi_next) w.push_back(v);
    wi = std::move(wi_next);
    if (w.size() > k * s.size()) return {s, w};
  }

  std::unordered_set<size_t> in_w(w.begin(), w.end());
  std::vector<std::optional<size_t>> parent(g.vertex_count());
  for (size_t u : w) {
    for (const auto& [v, w_e] : g.out_edges(u)) {
      if (in_w.count(v) && std::fabs(d[v] - (d[u] + w_e)) < kEps) {
        if (!parent[v]) parent[v] = u;
      }
    }
  }

  std::vector<std::vector<size_t>> children(g.vertex_count());
  for (size_t v : w) {
    if (parent[v]) children[*parent[v]].push_back(v);
  }

  std::vector<size_t> subtree_size(g.vertex_count(), 0);
  std::unordered_set<size_t> has_parent;
  for (size_t v : w)
    if (parent[v]) has_parent.insert(v);

  std::vector<size_t> roots_in_s;
  for (size_t r : s) {
    if (!has_parent.count(r)) {
      if (count_subtree(r, children, subtree_size) >= k) roots_in_s.push_back(r);
    }
  }
  return {roots_in_s, w};
}

std::pair<double, std::vector<size_t>> base_case(
    const Graph& g, std::vector<double>& d,
    std::vector<std::optional<size_t>>& pred, double b,
    const std::vector<size_t>& s, size_t n, size_t k) {
  size_t x = s[0];
  std::vector<size_t> u0;
  MinHeap heap(n);
  heap.insert(x, d[x]);

  while (!heap.is_empty() && u0.size() < k + 1) {
    auto [u, du] = heap.extract_min();
    u0.push_back(u);
    for (const auto& [v, w_e] : g.out_edges(u)) {
      double new_d = du + w_e;
      if (new_d >= b || new_d > d[v]) continue;
      Relax(d, pred, u, v, w_e);
      if (heap.contains(v))
        heap.decrease_key(v, d[v]);
      else
        heap.insert(v, d[v]);
    }
  }

  if (u0.size() <= k) return {b, u0};
  double b_prime = b;
  for (size_t v : u0)
    if (d[v] > b_prime) b_prime = d[v];
  std::vector<size_t> filtered;
  for (size_t v : u0)
    if (d[v] < b_prime) filtered.push_back(v);
  return {b_prime, filtered};
}

std::pair<double, std::vector<size_t>> bmssp(
    const Graph& g, std::vector<double>& d,
    std::vector<std::optional<size_t>>& pred, size_t l, double b,
    const std::vector<size_t>& s, size_t n, size_t k, size_t t) {
  size_t two_lt = Pow2(l * t);
  if (l == 0) return base_case(g, d, pred, b, s, n, k);

  auto [p, w] = find_pivots(g, d, pred, b, s, k);

  size_t m = std::max(Pow2((l - 1) * t), size_t(1));
  FrontierDS ds(m, b);
  for (size_t x : p) ds.insert(x, d[x]);

  double b0_prime = b;
  for (size_t x : p)
    if (d[x] < b0_prime) b0_prime = d[x];

  std::unordered_set<size_t> u_set;
  double last_bi_prime = b0_prime;
  size_t iter = 0;

  while (u_set.size() < k * two_lt && iter < kMaxIter) {
    double bi;
    std::vector<size_t> si;
    if (!ds.pull(bi, si)) break;
    ++iter;
    auto [bi_prime, ui] = bmssp(g, d, pred, l - 1, bi, si, n, k, t);
    last_bi_prime = bi_prime;
    for (size_t u : ui) u_set.insert(u);

    std::vector<std::pair<size_t, double>> k_list;
    for (size_t u : ui) {
      for (const auto& [v, w_e] : g.out_edges(u)) {
        double new_d = d[u] + w_e;
        if (new_d > d[v]) continue;
        Relax(d, pred, u, v, w_e);
        if (d[v] >= bi && d[v] < b)
          ds.insert(v, d[v]);
        else if (d[v] >= bi_prime && d[v] < bi)
          k_list.emplace_back(v, d[v]);
      }
    }
    for (size_t x : si)
      if (d[x] >= bi_prime && d[x] < bi) k_list.emplace_back(x, d[x]);
    ds.batch_prepend(k_list);

    if (ds.is_empty()) {
      return {b, std::vector<size_t>(u_set.begin(), u_set.end())};
    }
    if (u_set.size() > k * two_lt) {
      return {bi_prime, std::vector<size_t>(u_set.begin(), u_set.end())};
    }
  }

  double b_prime = (iter > 0) ? last_bi_prime : b0_prime;
  for (size_t x : w)
    if (d[x] < b_prime) u_set.insert(x);
  return {b_prime, std::vector<size_t>(u_set.begin(), u_set.end())};
}

}  // namespace

SsspResult duan_mao_shu_yin(const Graph& g, size_t source) {
  size_t n = g.vertex_count();
  if (n == 0) return {{}, {}};

  std::vector<double> d(n, kInf);
  std::vector<std::optional<size_t>> pred(n);
  d[source] = 0;

  double t_log = std::log(static_cast<double>(std::max(n, size_t(2)))) / std::log(2.0);
  size_t t = std::max(static_cast<size_t>(1),
                      static_cast<size_t>(std::floor(std::pow(t_log, 2.0 / 3.0))));
  size_t k = std::max(static_cast<size_t>(1),
                      static_cast<size_t>(std::floor(std::pow(t_log, 1.0 / 3.0))));
  size_t l = static_cast<size_t>(std::ceil(t_log / static_cast<double>(t)));

  std::vector<size_t> s = {source};
  bmssp(g, d, pred, l, kInf, s, n, k, t);

  return {std::move(d), std::move(pred)};
}

}  // namespace sssp
