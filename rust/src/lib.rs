//! Single-source shortest paths: O(m log^{2/3} n) deterministic algorithm
//! for directed graphs with non-negative real weights (comparison-addition model).
//! From "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths"
//! (Duan, Mao, Shu, Yin).

mod graph;
mod sssp;

pub use graph::Graph;
pub use sssp::{duan_mao_shu_yin, SsspResult};
