# SSSP — Single-Source Shortest Paths

Deterministic **O(m log²⁄³ n)** algorithm for single-source shortest paths on **directed graphs with non-negative real edge weights**, implemented in multiple languages.

Based on the paper:

> **Breaking the Sorting Barrier for Directed Single-Source Shortest Paths**  
> Ran Duan, Jiayi Mao, Xiao Mao, Xinkai Shu, Longhui Yin  
> [arXiv:2504.17033v2](https://arxiv.org/html/2504.17033v2)

---

## Algorithm overview

- **Problem:** Given a directed graph *G* with *n* vertices, *m* edges, non-negative real weights *w(e)*, and a source *s*, compute the shortest path distances (and optionally predecessors) from *s* to every vertex.
- **Complexity:** **O(m log²⁄³ n)** in the **comparison-addition model** (only comparisons and additions on edge weights; no integer/word-RAM tricks).
- **Result:** First deterministic SSSP for directed graphs that breaks the *O(m + n log n)* “sorting barrier” of Dijkstra on sparse graphs.

### Main ideas

- **Parameters:** *k* = ⌊log¹⁄³ n⌋, *t* = ⌊log²⁄³ n⌋, *l* = ⌈(log n)/t⌉.
- **FindPivots:** Run *k* relaxation steps from the current frontier *S*; build a forest of “tight” edges and take as pivots the roots of trees of size ≥ *k* (at most |*Ũ*|/*k* pivots).
- **Base case (*l* = 0):** Mini-Dijkstra from a single vertex until *k*+1 vertices or no more.
- **BMSSP:** Recursive bounded multi-source shortest path using a frontier data structure (Lemma 3.3 style) with **Insert**, **BatchPrepend**, and **Pull**; merge results and relax edges.
- **Relaxation:** Update when *d[u] + w(u,v) ≤ d[v]* (equality allowed per Remark 3.4).

---

## Project structure

```
SSSP/
├── README.md
├── csharp/          # C# library (.NET 8)
├── rust/            # Rust library
├── cplusplus/       # C++17 library + test
├── go/              # Go module
├── java/            # Java (no build tool)
├── php/             # PHP (single file)
├── python/          # Python 3
└── typescript/      # TypeScript (Node)
```

Each language folder contains:

- A **directed graph** type (vertices 0..*n*−1, non-negative weights).
- An **SSSP result** type (distances and predecessors).
- The **Duan–Mao–Shu–Yin** implementation (Solve entry point, BMSSP, BaseCase, FindPivots, FrontierDS, MinHeap).
- Tests or a small runner that compare distances to a reference Dijkstra where applicable.

---

## Language-specific details

### C# (`csharp/`)

- **Target:** .NET 8.0  
- **Files:** `Graph.cs`, `SSSPResult.cs`, `DuanMaoShuYinSSSP.cs`, `SSSP.Tests/DuanMaoShuYinSSSPTests.cs`  
- **API:** `SSSP.DuanMaoShuYinSSSP.Solve(Graph g, int source)` → `SSSPResult` (Distance, Predecessor arrays).  
- **Build & test:**
  ```bash
  cd csharp
  dotnet build
  dotnet test
  ```

---

### Rust (`rust/`)

- **Files:** `src/graph.rs`, `src/sssp.rs`, `src/lib.rs`  
- **API:** `sssp::duan_mao_shu_yin(g, source)` → `SsspResult { distance, predecessor }`; `predecessor[v]` is `Option<usize>`.  
- **Build & test:**
  ```bash
  cd rust
  cargo build
  cargo test
  ```

---

### C++ (`cplusplus/`)

- **Standard:** C++17  
- **Files:** `graph.hpp`/`graph.cpp`, `sssp.hpp`/`sssp.cpp`, `test_main.cpp`, `CMakeLists.txt`  
- **API:** `sssp::duan_mao_shu_yin(g, source)` → `SsspResult { distance, predecessor }`; `predecessor[v]` is `std::optional<size_t>`.  
- **Build & test:**
  ```bash
  cd cplusplus
  mkdir build && cd build
  cmake .. -DCMAKE_BUILD_TYPE=Release
  cmake --build .
  ctest  # or ./sssp_test
  ```

---

### Go (`go/`)

- **Files:** `graph.go`, `sssp.go`, `sssp_test.go`  
- **API:** `sssp.DuanMaoShuYin(g, source)` → `*SsspResult` with `Distance []float64`, `Predecessor []int` (−1 for source/unreachable).  
- **Test:**
  ```bash
  cd go
  go test -v ./...
  ```

---

### Java (`java/`)

- **Files:** `Graph.java`, `SsspResult.java`, `DuanMaoShuYinSSSP.java`, `Main.java`  
- **API:** `DuanMaoShuYinSSSP.solve(Graph g, int source)` → `SsspResult` with `getDistance()`, `getPredecessor()` (Integer; null for source/unreachable).  
- **Build & run:**
  ```bash
  cd java
  javac -d out sssp/*.java
  java -cp out sssp.Main
  ```

---

### PHP (`php/`)

- **File:** `sssp.php` (Graph, SsspResult, algorithm, FrontierDS, MinHeap in one file).  
- **API:** `duan_mao_shu_yin(Graph $g, int $source)` → `SsspResult` with `$result->distance`, `$result->predecessor` (null for source/unreachable).  
- **Run:** Include the file and call the function; no separate test runner in repo.

---

### Python (`python/`)

- **Files:** `graph.py`, `sssp.py`, `test_sssp.py`  
- **API:** `duan_mao_shu_yin(g, source)` → `SsspResult(distance, predecessor)`; `predecessor[v]` is `int | None`.  
- **Test:**
  ```bash
  cd python
  python test_sssp.py
  ```

---

### TypeScript (`typescript/`)

- **Files:** `src/graph.ts`, `src/sssp.ts`, `src/index.ts`, `test/sssp.test.js`  
- **API:** `duanMaoShuYin(g, source)` → `SsspResult { distance, predecessor }`; `predecessor[v]` is `number | null`.  
- **Build & test:**
  ```bash
  cd typescript
  npm install
  npm run build
  node test/sssp.test.js
  ```

---

## Graph representation

In every implementation:

- **Vertices:** integers `0` .. `n-1`.  
- **Edges:** directed; each edge has a **non-negative** weight (double/float).  
- **Storage:** adjacency list: for each vertex `u`, a list of `(v, weight)` for edges *u* → *v*.

Typical usage:

1. Construct a graph with *n* vertices.  
2. Add edges with `add_edge(from, to, weight)`.  
3. Call the algorithm with the graph and source index.  
4. Read distances and predecessors from the result.

---

## References

- **Paper:** Duan, Mao, Mao, Shu, Yin — *Breaking the Sorting Barrier for Directed Single-Source Shortest Paths*, [arXiv:2504.17033v2](https://arxiv.org/html/2504.17033v2).  
- **Model:** Comparison-addition model; constant-degree assumption in the paper (general graphs can be reduced).  
- **Note:** Implementations use a simplified frontier data structure that preserves correctness; the paper’s full block-based structure (Lemma 3.3) can be used for tighter complexity constants.
