#include "graph.hpp"
#include "sssp.hpp"

#include <chrono>
#include <cmath>
#include <cstdlib>
#include <cctype>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

static bool str_eq_ignore_case(const std::string& a, const char* b) {
  size_t i = 0;
  while (i < a.size() && *b) {
    if (std::tolower(static_cast<unsigned char>(a[i])) != std::tolower(static_cast<unsigned char>(*b)))
      return false;
    i++;
    b++;
  }
  return i == a.size() && *b == '\0';
}

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
  const char* algo_env = std::getenv("SSSP_ALGORITHM");
  std::string algo(algo_env ? algo_env : "duan_mao_shu_yin");
  while (!algo.empty() && (algo.back() == ' ' || algo.back() == '\t')) algo.pop_back();
  size_t start = 0;
  while (start < algo.size() && (algo[start] == ' ' || algo[start] == '\t')) start++;
  algo = algo.substr(start);
  double min_sec = 0.0;
  if (const char* min_env = std::getenv("SSSP_MIN_SECONDS")) {
    char* end = nullptr;
    min_sec = std::strtod(min_env, &end);
    if (end == min_env || min_sec < 0) min_sec = 0.0;
  }
  double max_sec = 30.0;
  if (const char* max_env = std::getenv("SSSP_MAX_SECONDS")) {
    char* end = nullptr;
    max_sec = std::strtod(max_env, &end);
    if (end == max_env || max_sec < 0) max_sec = 30.0;
  }
  size_t iterations = 1;
  if (min_sec > 0.0) {
    auto t0 = std::chrono::steady_clock::now();
    std::chrono::duration<double> min_dur(min_sec);
    std::chrono::duration<double> max_dur(max_sec);
    iterations = 0;
    sssp::SsspResult r = str_eq_ignore_case(algo, "dijkstra")
        ? sssp::dijkstra(g, 0)
        : sssp::duan_mao_shu_yin(g, 0);
    while (std::chrono::steady_clock::now() - t0 < min_dur && std::chrono::steady_clock::now() - t0 < max_dur) {
      r = str_eq_ignore_case(algo, "dijkstra")
          ? sssp::dijkstra(g, 0)
          : sssp::duan_mao_shu_yin(g, 0);
      iterations++;
    }
  } else {
    sssp::SsspResult r = str_eq_ignore_case(algo, "dijkstra")
        ? sssp::dijkstra(g, 0)
        : sssp::duan_mao_shu_yin(g, 0);
  }
  if (const char* result_path = std::getenv("RESULT_FILE"); result_path && result_path[0]) {
    std::ostringstream out;
    out << "{\"iterations\":" << iterations << "}";
    std::ofstream f(result_path);
    if (f) f << out.str();
  }
  return 0;
}
