package sssp

// Graph is a directed graph with non-negative edge weights.
// Vertices are 0..VertexCount-1.
type Graph struct {
	outEdges  [][]edge
	edgeCount int
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
func (g *Graph) AddEdge(from, to int, weight float64) {
	if weight < 0 {
		panic("edge weights must be non-negative")
	}
	g.outEdges[from] = append(g.outEdges[from], edge{to, weight})
	g.edgeCount++
}

// OutEdges returns the outgoing edges from vertex u.
func (g *Graph) OutEdges(u int) []edge {
	return g.outEdges[u]
}
