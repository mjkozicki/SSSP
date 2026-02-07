// Load graph from file, run SSSP(0), print DONE. Path = argv[1] or GRAPH_FILE env.
use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;

use sssp::{duan_mao_shu_yin, Graph};

fn load_graph(path: &Path) -> std::io::Result<Graph> {
    let f = File::open(path)?;
    let mut lines = BufReader::new(f).lines();
    let first = lines.next().ok_or_else(|| std::io::Error::from(std::io::ErrorKind::InvalidData))??;
    let mut parts = first.split_whitespace();
    let n: usize = parts.next().unwrap().parse().unwrap();
    let m: usize = parts.next().unwrap().parse().unwrap();
    let mut g = Graph::new(n);
    for _ in 0..m {
        let line = lines.next().ok_or_else(|| std::io::Error::from(std::io::ErrorKind::InvalidData))??;
        let mut p = line.split_whitespace();
        let u: usize = p.next().unwrap().parse().unwrap();
        let v: usize = p.next().unwrap().parse().unwrap();
        let w: f64 = p.next().unwrap().parse().unwrap();
        g.add_edge(u, v, w);
    }
    Ok(g)
}

fn main() {
    let path = env::args()
        .nth(1)
        .or_else(|| env::var("GRAPH_FILE").ok())
        .unwrap_or_else(|| {
            eprintln!("Usage: benchmark <graph.txt>");
            std::process::exit(1);
        });
    let path = Path::new(&path);
    let g = load_graph(path).unwrap_or_else(|e| {
        eprintln!("{}", e);
        std::process::exit(1);
    });
    let r = duan_mao_shu_yin(&g, 0);
    let reachable = r.distance.iter().filter(|d| d.is_finite()).count();
    println!("DONE {} {}", r.vertex_count(), reachable);
}
