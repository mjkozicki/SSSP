package sssp

// Graph is a directed graph with non-negative edge weights.
// Vertices are 0..VertexCount-1.
// Call Compact() after adding all edges for cache-friendly traversal.
type Graph struct {
	outEdges  [][]edge
	edgeCount int
	compact   bool
	edges     []edge   // flat CSR after Compact
	offsets   []int    // length VertexCount+1
}

type edge struct {
	to     int
	weight float64
}

// NewGraph creates a graph with n vertices.
func NewGraph(n int) *Graph {
	return &Graph{
		outEdges: make([][]edge, n),
	}
}

// VertexCount returns the number of vertices.
func (g *Graph) VertexCount() int {
	return len(g.outEdges)
}

// EdgeCount returns the number of edges.
func (g *Graph) EdgeCount() int {
	return g.edgeCount
}

// AddEdge adds a directed edge (from, to) with the given weight.
// No-op after Compact().
func (g *Graph) AddEdge(from, to int, weight float64) {
	if g.compact {
		return
	}
	if weight < 0 {
		panic("edge weights must be non-negative")
	}
	g.outEdges[from] = append(g.outEdges[from], edge{to, weight})
	g.edgeCount++
}

// Compact builds a single flat edge array for better cache locality.
// Call once after adding all edges.
func (g *Graph) Compact() {
	if g.compact {
		return
	}
	n := len(g.outEdges)
	g.offsets = make([]int, n+1)
	for u := 0; u < n; u++ {
		g.offsets[u+1] = g.offsets[u] + len(g.outEdges[u])
	}
	g.edges = make([]edge, g.edgeCount)
	pos := 0
	for u := 0; u < n; u++ {
		copy(g.edges[pos:], g.outEdges[u])
		pos += len(g.outEdges[u])
	}
	g.compact = true
}

// OutEdges returns the outgoing edges from vertex u.
func (g *Graph) OutEdges(u int) []edge {
	if g.compact {
		return g.edges[g.offsets[u]:g.offsets[u+1]]
	}
	return g.outEdges[u]
}
