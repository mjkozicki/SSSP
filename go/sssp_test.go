package sssp

import (
	"math"
	"testing"
)

func dijkstra(g *Graph, source int) []float64 {
	n := g.VertexCount()
	dist := make([]float64, n)
	for i := range dist {
		dist[i] = math.Inf(1)
	}
	dist[source] = 0
	done := make([]bool, n)
	for round := 0; round < n; round++ {
		u := -1
		best := math.Inf(1)
		for i := 0; i < n; i++ {
			if !done[i] && dist[i] < best {
				best = dist[i]
				u = i
			}
		}
		if u < 0 || math.IsInf(best, 1) {
			break
		}
		done[u] = true
		for _, e := range g.OutEdges(u) {
			d := dist[u] + e.weight
			if d < dist[e.to] {
				dist[e.to] = d
			}
		}
	}
	return dist
}

func TestSingleVertex(t *testing.T) {
	g := NewGraph(1)
	r := DuanMaoShuYin(g, 0)
	if r.Distance[0] != 0 {
		t.Errorf("distance[0] = %v, want 0", r.Distance[0])
	}
}

func TestTwoVerticesOneEdge(t *testing.T) {
	g := NewGraph(2)
	g.AddEdge(0, 1, 3)
	r := DuanMaoShuYin(g, 0)
	if r.Distance[0] != 0 || r.Distance[1] != 3 {
		t.Errorf("distances = %v", r.Distance)
	}
	if r.Predecessor[1] != 0 {
		t.Errorf("predecessor[1] = %v, want 0", r.Predecessor[1])
	}
}

func TestMatchesDijkstraSmall(t *testing.T) {
	g := NewGraph(6)
	g.AddEdge(0, 1, 2)
	g.AddEdge(0, 2, 5)
	g.AddEdge(1, 2, 2)
	g.AddEdge(1, 3, 7)
	g.AddEdge(2, 3, 1)
	g.AddEdge(2, 4, 6)
	g.AddEdge(3, 4, 3)
	g.AddEdge(3, 5, 9)
	g.AddEdge(4, 5, 1)
	dijkstraDist := dijkstra(g, 0)
	r := DuanMaoShuYin(g, 0)
	for i := 0; i < g.VertexCount(); i++ {
		if math.Abs(dijkstraDist[i]-r.Distance[i]) >= 1e-10 {
			t.Errorf("vertex %d: dijkstra %v vs dmsy %v", i, dijkstraDist[i], r.Distance[i])
		}
	}
}
