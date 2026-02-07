//! Directed graph with non-negative edge weights for SSSP.
//! Vertices are 0..vertex_count()-1.
//! Supports compaction to CSR (compressed sparse row) for cache-friendly iteration.

/// Directed graph: adjacency list during build, optional CSR after compact().
#[derive(Clone, Debug)]
pub struct Graph {
    /// During build: per-vertex edge lists. After compact: unused.
    adj: Vec<Vec<(usize, f64)>>,
    /// After compact: single contiguous edge list and offsets[0..=n].
    edges: Option<Box<[(usize, f64)]>>,
    offsets: Option<Box<[usize]>>,
    edge_count: usize,
}

impl Graph {
    /// Creates a graph with `vertex_count` vertices (no edges).
    pub fn new(vertex_count: usize) -> Self {
        Graph {
            adj: vec![Vec::new(); vertex_count],
            edges: None,
            offsets: None,
            edge_count: 0,
        }
    }

    /// Number of vertices.
    pub fn vertex_count(&self) -> usize {
        self.adj.len()
    }

    /// Number of edges.
    pub fn edge_count(&self) -> usize {
        self.edge_count
    }

    /// Adds directed edge (from, to) with given weight. Panics if weight < 0.
    /// No-op if compact() was already called.
    pub fn add_edge(&mut self, from: usize, to: usize, weight: f64) {
        assert!(weight >= 0.0, "edge weights must be non-negative");
        if self.edges.is_some() {
            return;
        }
        self.adj[from].push((to, weight));
        self.edge_count += 1;
    }

    /// Compacts adjacency list into a single contiguous edge array (CSR) for
    /// better cache locality. Call once after all edges are added.
    pub fn compact(&mut self) {
        if self.edges.is_some() {
            return;
        }
        let n = self.adj.len();
        let mut offsets = Vec::with_capacity(n + 1);
        let mut pos = 0usize;
        for list in &self.adj {
            offsets.push(pos);
            pos += list.len();
        }
        offsets.push(pos);
        let mut edges = Vec::with_capacity(pos);
        for list in &self.adj {
            edges.extend(list.iter().copied());
        }
        self.edges = Some(edges.into_boxed_slice());
        self.offsets = Some(offsets.into_boxed_slice());
        self.adj.clear();
        self.adj.shrink_to_fit();
    }

    /// Outgoing edges from vertex `u`: slice of (to, weight).
    #[inline(always)]
    pub fn out_edges(&self, u: usize) -> &[(usize, f64)] {
        if let (Some(ref edges), Some(ref offsets)) = (&self.edges, &self.offsets) {
            let start = offsets[u];
            let end = offsets[u + 1];
            &edges[start..end]
        } else {
            &self.adj[u]
        }
    }

    /// Out-degree of vertex `u`.
    pub fn out_degree(&self, u: usize) -> usize {
        if let Some(ref offsets) = self.offsets {
            offsets[u + 1] - offsets[u]
        } else {
            self.adj[u].len()
        }
    }
}
