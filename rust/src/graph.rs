//! Directed graph with non-negative edge weights for SSSP.
//! Vertices are 0..vertex_count()-1.

/// Directed graph: for each vertex, list of (target, weight) for outgoing edges.
#[derive(Clone, Debug)]
pub struct Graph {
    out_edges: Vec<Vec<(usize, f64)>>,
    edge_count: usize,
}

impl Graph {
    /// Creates a graph with `vertex_count` vertices (no edges).
    pub fn new(vertex_count: usize) -> Self {
        Graph {
            out_edges: vec![Vec::new(); vertex_count],
            edge_count: 0,
        }
    }

    /// Number of vertices.
    pub fn vertex_count(&self) -> usize {
        self.out_edges.len()
    }

    /// Number of edges.
    pub fn edge_count(&self) -> usize {
        self.edge_count
    }

    /// Adds directed edge (from, to) with given weight. Panics if weight < 0.
    pub fn add_edge(&mut self, from: usize, to: usize, weight: f64) {
        assert!(weight >= 0.0, "edge weights must be non-negative");
        self.out_edges[from].push((to, weight));
        self.edge_count += 1;
    }

    /// Outgoing edges from vertex `u`: slice of (to, weight).
    pub fn out_edges(&self, u: usize) -> &[(usize, f64)] {
        &self.out_edges[u]
    }

    /// Out-degree of vertex `u`.
    pub fn out_degree(&self, u: usize) -> usize {
        self.out_edges[u].len()
    }
}
