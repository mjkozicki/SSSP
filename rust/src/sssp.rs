//! O(m log^{2/3} n) deterministic SSSP (Duan–Mao–Shu–Yin).
//! Comparison-addition model; non-negative real weights.

use std::collections::HashSet;

use crate::graph::Graph;

/// Result of single-source shortest path: distances and predecessors.
/// Unreachable vertices have distance `f64::INFINITY` and predecessor `None`.
#[derive(Clone, Debug)]
pub struct SsspResult {
    pub distance: Vec<f64>,
    pub predecessor: Vec<Option<usize>>,
}

impl SsspResult {
    pub fn vertex_count(&self) -> usize {
        self.distance.len()
    }
}

const MAX_ITER: usize = 100_000_000;
const EPS: f64 = 1e-12;

/// Runs SSSP from `source` using the Duan–Mao–Shu–Yin algorithm.
/// Returns distances and predecessor pointers.
pub fn duan_mao_shu_yin(g: &Graph, source: usize) -> SsspResult {
    let n = g.vertex_count();
    if n == 0 {
        return SsspResult {
            distance: vec![],
            predecessor: vec![],
        };
    }

    let mut d = vec![f64::INFINITY; n];
    let mut pred = vec![None; n];
    d[source] = 0.0;

    let t_log = (n.max(2) as f64).ln() / 2_f64.ln();
    let t = (t_log.powf(2.0 / 3.0).floor() as i32).max(1) as usize;
    let k = (t_log.powf(1.0 / 3.0).floor() as i32).max(1) as usize;
    let l = (t_log / t as f64).ceil() as usize;

    let mut s = vec![source];
    bmssp(g, &mut d, &mut pred, l, f64::INFINITY, &mut s, n, k, t);

    SsspResult {
        distance: d,
        predecessor: pred,
    }
}

fn bmssp(
    g: &Graph,
    d: &mut [f64],
    pred: &mut [Option<usize>],
    l: usize,
    b: f64,
    s: &[usize],
    n: usize,
    k: usize,
    t: usize,
) -> (f64, Vec<usize>) {
    let two_lt = pow2(l * t);
    if l == 0 {
        return base_case(g, d, pred, b, s, n, k);
    }

    let (p, w) = find_pivots(g, d, pred, b, s, k);

    let m = pow2((l - 1) * t).max(1);
    let mut ds = FrontierDS::new(m, b);
    for &x in &p {
        ds.insert(x, d[x]);
    }

    let b0_prime = p.iter().map(|&x| d[x]).min_by(f64_cmp).unwrap_or(b);
    let mut u_set: HashSet<usize> = HashSet::new();
    let mut last_bi_prime = b0_prime;
    let mut iter = 0usize;

    while u_set.len() < k * two_lt && iter < MAX_ITER {
        let (bi, si) = match ds.pull() {
            Some(x) => x,
            None => break,
        };
        iter += 1;
        let (bi_prime, ui) = bmssp(g, d, pred, l - 1, bi, &si, n, k, t);
        last_bi_prime = bi_prime;
        for u in &ui {
            u_set.insert(*u);
        }

        let mut k_list = Vec::new();
        for &u in &ui {
            for &(v, w_e) in g.out_edges(u) {
                let new_d = d[u] + w_e;
                if new_d > d[v] {
                    continue;
                }
                relax(d, pred, u, v, w_e);
                if d[v] >= bi && d[v] < b {
                    ds.insert(v, d[v]);
                } else if d[v] >= bi_prime && d[v] < bi {
                    k_list.push((v, d[v]));
                }
            }
        }
        for &x in &si {
            if d[x] >= bi_prime && d[x] < bi {
                k_list.push((x, d[x]));
            }
        }
        ds.batch_prepend(&k_list);

        if ds.is_empty() {
            return (b, u_set.into_iter().collect());
        }
        if u_set.len() > k * two_lt {
            return (bi_prime, u_set.into_iter().collect());
        }
    }

    let b_prime = if iter > 0 { last_bi_prime } else { b0_prime };
    for &x in &w {
        if d[x] < b_prime {
            u_set.insert(x);
        }
    }
    (b_prime, u_set.into_iter().collect())
}

fn base_case(
    g: &Graph,
    d: &mut [f64],
    pred: &mut [Option<usize>],
    b: f64,
    s: &[usize],
    n: usize,
    k: usize,
) -> (f64, Vec<usize>) {
    let x = s[0];
    let mut u0 = Vec::new();
    let mut heap = MinHeap::new(n);
    heap.insert(x, d[x]);

    while !heap.is_empty() && u0.len() < k + 1 {
        let (u, du) = heap.extract_min().unwrap();
        u0.push(u);
        for &(v, w_e) in g.out_edges(u) {
            let new_d = du + w_e;
            if new_d >= b {
                continue;
            }
            if new_d > d[v] {
                continue;
            }
            relax(d, pred, u, v, w_e);
            if heap.contains(v) {
                heap.decrease_key(v, d[v]);
            } else {
                heap.insert(v, d[v]);
            }
        }
    }

    if u0.len() <= k {
        return (b, u0);
    }
    let b_prime = u0.iter().map(|&v| d[v]).max_by(f64_cmp).unwrap_or(b);
    let u0_filtered: Vec<usize> = u0.into_iter().filter(|&v| d[v] < b_prime).collect();
    (b_prime, u0_filtered)
}

fn find_pivots(
    g: &Graph,
    d: &mut [f64],
    pred: &mut [Option<usize>],
    b: f64,
    s: &[usize],
    k: usize,
) -> (Vec<usize>, Vec<usize>) {
    let mut w: Vec<usize> = s.to_vec();
    let mut wi = s.to_vec();

    for _ in 1..=k {
        let mut wi_next = Vec::new();
        for &u in &wi {
            for &(v, w_e) in g.out_edges(u) {
                let new_d = d[u] + w_e;
                if new_d > d[v] {
                    continue;
                }
                relax(d, pred, u, v, w_e);
                if new_d < b {
                    wi_next.push(v);
                }
            }
        }
        w.extend(wi_next.iter().copied());
        wi = wi_next;
        if w.len() > k * s.len() {
            return (s.to_vec(), w);
        }
    }

    let in_w: HashSet<usize> = w.iter().copied().collect();
    let mut parent = vec![None; g.vertex_count()];
    for &u in &w {
        for &(v, w_e) in g.out_edges(u) {
            if in_w.contains(&v) && (d[v] - (d[u] + w_e)).abs() < EPS {
                if parent[v].is_none() {
                    parent[v] = Some(u);
                }
            }
        }
    }

    let mut children: Vec<Vec<usize>> = vec![Vec::new(); g.vertex_count()];
    for &v in &w {
        if let Some(u) = parent[v] {
            children[u].push(v);
        }
    }

    let mut subtree_size = vec![0usize; g.vertex_count()];
    fn count_subtree(u: usize, children: &[Vec<usize>], size: &mut [usize]) -> usize {
        if size[u] != 0 {
            return size[u];
        }
        let mut s = 1;
        for &v in &children[u] {
            s += count_subtree(v, children, size);
        }
        size[u] = s;
        s
    }

    let has_parent: HashSet<usize> = w.iter().filter(|&&v| parent[v].is_some()).copied().collect();
    let mut roots_in_s = Vec::new();
    for &r in s {
        if !has_parent.contains(&r) {
            let size = count_subtree(r, &children, &mut subtree_size);
            if size >= k {
                roots_in_s.push(r);
            }
        }
    }
    (roots_in_s, w)
}

fn relax(
    d: &mut [f64],
    pred: &mut [Option<usize>],
    u: usize,
    v: usize,
    w: f64,
) {
    let new_d = d[u] + w;
    if new_d > d[v] {
        return;
    }
    d[v] = new_d;
    pred[v] = Some(u);
}

fn pow2(exp: usize) -> usize {
    if exp == 0 {
        1
    } else {
        1 << exp.min(30)
    }
}

fn f64_cmp(a: &f64, b: &f64) -> std::cmp::Ordering {
    a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal)
}

// --- FrontierDS (Lemma 3.3 style) ---

struct FrontierDS {
    m: usize,
    b: f64,
    key_to_value: std::collections::HashMap<usize, f64>,
    list: Vec<(f64, usize)>,
    sorted: bool,
}

impl FrontierDS {
    fn new(m: usize, b: f64) -> Self {
        FrontierDS {
            m: m.max(1),
            b,
            key_to_value: std::collections::HashMap::new(),
            list: Vec::new(),
            sorted: true,
        }
    }

    fn insert(&mut self, key: usize, value: f64) {
        if let Some(&old) = self.key_to_value.get(&key) {
            if value >= old {
                return;
            }
            self.list.retain(|(_, k)| *k != key);
        }
        self.key_to_value.insert(key, value);
        self.list.push((value, key));
        self.sorted = false;
    }

    fn batch_prepend(&mut self, pairs: &[(usize, f64)]) {
        for &(key, value) in pairs {
            if let Some(&old) = self.key_to_value.get(&key) {
                if value >= old {
                    continue;
                }
            }
            self.list.retain(|(_, k)| *k != key);
            self.key_to_value.insert(key, value);
            self.list.push((value, key));
        }
        self.sorted = false;
    }

    fn pull(&mut self) -> Option<(f64, Vec<usize>)> {
        if self.list.is_empty() {
            return None;
        }
        if !self.sorted {
            self.list.sort_by(|a, b| {
                f64_cmp(&a.0, &b.0).then_with(|| a.1.cmp(&b.1))
            });
            self.sorted = true;
        }
        let take = self.m.min(self.list.len());
        let mut keys = Vec::with_capacity(take);
        for i in 0..take {
            let (_v, k) = self.list[i];
            keys.push(k);
            self.key_to_value.remove(&k);
        }
        self.list.drain(0..take);
        let bound = self.list.first().map(|(v, _)| *v).unwrap_or(self.b);
        Some((bound, keys))
    }

    fn is_empty(&self) -> bool {
        self.list.is_empty()
    }
}

// --- MinHeap for base case ---

struct MinHeap {
    heap: Vec<(usize, f64)>,
    index: Vec<Option<usize>>,
}

impl MinHeap {
    fn new(max_vertex: usize) -> Self {
        MinHeap {
            heap: Vec::new(),
            index: vec![None; max_vertex],
        }
    }

    fn is_empty(&self) -> bool {
        self.heap.is_empty()
    }

    fn contains(&self, v: usize) -> bool {
        v < self.index.len() && self.index[v].is_some()
    }

    fn insert(&mut self, v: usize, dist: f64) {
        let i = self.heap.len();
        self.index[v] = Some(i);
        self.heap.push((v, dist));
        self.sift_up(i);
    }

    fn extract_min(&mut self) -> Option<(usize, f64)> {
        if self.heap.is_empty() {
            return None;
        }
        let top = self.heap[0];
        self.index[top.0] = None;
        let last = self.heap.pop().unwrap();
        if !self.heap.is_empty() {
            self.heap[0] = last;
            self.index[last.0] = Some(0);
            self.sift_down(0);
        }
        Some(top)
    }

    fn decrease_key(&mut self, v: usize, new_d: f64) {
        let i = match self.index[v] {
            Some(i) => i,
            None => return,
        };
        if self.heap[i].1 <= new_d {
            return;
        }
        self.heap[i] = (v, new_d);
        self.sift_up(i);
    }

    fn sift_up(&mut self, mut i: usize) {
        while i > 0 {
            let p = (i - 1) / 2;
            if self.heap[p].1 <= self.heap[i].1 {
                break;
            }
            self.swap(i, p);
            i = p;
        }
    }

    fn sift_down(&mut self, mut i: usize) {
        loop {
            let l = 2 * i + 1;
            let r = 2 * i + 2;
            let mut small = i;
            if l < self.heap.len() && self.heap[l].1 < self.heap[small].1 {
                small = l;
            }
            if r < self.heap.len() && self.heap[r].1 < self.heap[small].1 {
                small = r;
            }
            if small == i {
                break;
            }
            self.swap(i, small);
            i = small;
        }
    }

    fn swap(&mut self, i: usize, j: usize) {
        let a = self.heap[i].0;
        let b = self.heap[j].0;
        self.heap.swap(i, j);
        self.index[a] = Some(j);
        self.index[b] = Some(i);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn dijkstra(g: &Graph, source: usize) -> Vec<f64> {
        let n = g.vertex_count();
        let mut dist = vec![f64::INFINITY; n];
        dist[source] = 0.0;
        let mut done = vec![false; n];
        for _ in 0..n {
            let u = (0..n)
                .filter(|&i| !done[i])
                .min_by(|&a, &b| dist[a].partial_cmp(&dist[b]).unwrap());
            let u = match u {
                Some(u) => u,
                None => break,
            };
            if dist[u] == f64::INFINITY {
                break;
            }
            done[u] = true;
            for &(to, w) in g.out_edges(u) {
                let d = dist[u] + w;
                if d < dist[to] {
                    dist[to] = d;
                }
            }
        }
        dist
    }

    #[test]
    fn single_vertex() {
        let g = Graph::new(1);
        let r = duan_mao_shu_yin(&g, 0);
        assert_eq!(r.distance[0], 0.0);
    }

    #[test]
    fn two_vertices_one_edge() {
        let mut g = Graph::new(2);
        g.add_edge(0, 1, 3.0);
        let r = duan_mao_shu_yin(&g, 0);
        assert_eq!(r.distance[0], 0.0);
        assert_eq!(r.distance[1], 3.0);
        assert_eq!(r.predecessor[1], Some(0));
    }

    #[test]
    fn matches_dijkstra_small() {
        let mut g = Graph::new(6);
        g.add_edge(0, 1, 2.0);
        g.add_edge(0, 2, 5.0);
        g.add_edge(1, 2, 2.0);
        g.add_edge(1, 3, 7.0);
        g.add_edge(2, 3, 1.0);
        g.add_edge(2, 4, 6.0);
        g.add_edge(3, 4, 3.0);
        g.add_edge(3, 5, 9.0);
        g.add_edge(4, 5, 1.0);
        let dijkstra_dist = dijkstra(&g, 0);
        let r = duan_mao_shu_yin(&g, 0);
        for i in 0..g.vertex_count() {
            assert!(
                (dijkstra_dist[i] - r.distance[i]).abs() < 1e-10,
                "vertex {}: dijkstra {} vs dmsy {}",
                i,
                dijkstra_dist[i],
                r.distance[i]
            );
        }
    }

    #[test]
    fn matches_dijkstra_parallel_paths() {
        let mut g = Graph::new(4);
        g.add_edge(0, 1, 1.0);
        g.add_edge(0, 2, 4.0);
        g.add_edge(1, 3, 2.0);
        g.add_edge(2, 3, 1.0);
        let dijkstra_dist = dijkstra(&g, 0);
        let r = duan_mao_shu_yin(&g, 0);
        for i in 0..g.vertex_count() {
            assert!(
                (dijkstra_dist[i] - r.distance[i]).abs() < 1e-10,
                "vertex {}: dijkstra {} vs dmsy {}",
                i,
                dijkstra_dist[i],
                r.distance[i]
            );
        }
    }
}
