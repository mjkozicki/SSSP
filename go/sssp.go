package sssp

import (
	"container/heap"
	"math"
	"sort"
)

const maxIter = 100_000_000
const eps = 1e-12

// SsspResult holds distances and predecessors from a single-source shortest path run.
type SsspResult struct {
	Distance    []float64
	Predecessor []int // -1 for source or unreachable
}

// VertexCount returns the number of vertices.
func (r *SsspResult) VertexCount() int {
	return len(r.Distance)
}

// dijkstraHeap is a min-heap of (distance, vertex) for Dijkstra.
type dijkstraHeap []struct {
	dist float64
	v    int
}

func (h dijkstraHeap) Len() int           { return len(h) }
func (h dijkstraHeap) Less(i, j int) bool { return h[i].dist < h[j].dist }
func (h dijkstraHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *dijkstraHeap) Push(x any)        { *h = append(*h, x.(struct{ dist float64; v int })) }
func (h *dijkstraHeap) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[:n-1]
	return x
}

// Dijkstra runs SSSP from source using Dijkstra's algorithm (O((V+E) log V)).
// Returns the same result type as DuanMaoShuYin. Predecessor is -1 for source or unreachable.
func Dijkstra(g *Graph, source int) *SsspResult {
	n := g.VertexCount()
	if n == 0 {
		return &SsspResult{}
	}
	d := make([]float64, n)
	pred := make([]int, n)
	for i := range d {
		d[i] = math.Inf(1)
		pred[i] = -1
	}
	d[source] = 0
	cap := n
	if cap > 4096 {
		cap = 4096
	}
	pq := make(dijkstraHeap, 0, cap)
	heap.Init(&pq)
	heap.Push(&pq, struct{ dist float64; v int }{0, source})
	for pq.Len() > 0 {
		entry := heap.Pop(&pq).(struct{ dist float64; v int })
		du, u := entry.dist, entry.v
		if du > d[u] {
			continue
		}
		edges := g.OutEdges(u)
		for i := 0; i < len(edges); i++ {
			e := &edges[i]
			v, w := e.to, e.weight
			newD := d[u] + w
			if newD < d[v] {
				d[v] = newD
				pred[v] = u
				heap.Push(&pq, struct{ dist float64; v int }{newD, v})
			}
		}
	}
	return &SsspResult{Distance: d, Predecessor: pred}
}

// DuanMaoShuYin runs SSSP from source using the Duan–Mao–Shu–Yin algorithm.
func DuanMaoShuYin(g *Graph, source int) *SsspResult {
	n := g.VertexCount()
	if n == 0 {
		return &SsspResult{}
	}
	d := make([]float64, n)
	pred := make([]int, n)
	for i := range d {
		d[i] = math.Inf(1)
		pred[i] = -1
	}
	d[source] = 0

	tLog := math.Log(float64(max(n, 2))) / math.Ln2
	t := max(1, int(math.Floor(math.Pow(tLog, 2.0/3.0))))
	k := max(1, int(math.Floor(math.Pow(tLog, 1.0/3.0))))
	l := int(math.Ceil(tLog / float64(t)))

	s := []int{source}
	bmssp(g, d, pred, l, math.Inf(1), s, n, k, t)

	return &SsspResult{Distance: d, Predecessor: pred}
}

func bmssp(g *Graph, d []float64, pred []int, l int, b float64, s []int, n, k, t int) (float64, []int) {
	twoLt := pow2(l * t)
	if l == 0 {
		return baseCase(g, d, pred, b, s, n, k)
	}

	p, w := findPivots(g, d, pred, b, s, k)
	m := max(pow2((l-1)*t), 1)
	ds := newFrontierDS(m, b)
	for _, x := range p {
		ds.insert(x, d[x])
	}

	b0Prime := b
	for _, x := range p {
		if d[x] < b0Prime {
			b0Prime = d[x]
		}
	}

	uSetCap := k * twoLt
	if uSetCap > 1_000_000 {
		uSetCap = 1_000_000
	}
	uSet := make(map[int]struct{}, uSetCap)
	lastBiPrime := b0Prime
	iter := 0

	for len(uSet) < k*twoLt && iter < maxIter {
		bi, si, ok := ds.pull()
		if !ok {
			break
		}
		iter++
		biPrime, ui := bmssp(g, d, pred, l-1, bi, si, n, k, t)
		lastBiPrime = biPrime
		for _, u := range ui {
			uSet[u] = struct{}{}
		}

		kCap := 64
		if len(ui)*4 > kCap {
			kCap = len(ui) * 4
		}
		kListV := make([]int, 0, kCap)
		kListD := make([]float64, 0, kCap)
		for _, u := range ui {
			edges := g.OutEdges(u)
			for i := 0; i < len(edges); i++ {
				e := &edges[i]
				newD := d[u] + e.weight
				if newD > d[e.to] {
					continue
				}
				relax(d, pred, u, e.to, e.weight)
				if d[e.to] >= bi && d[e.to] < b {
					ds.insert(e.to, d[e.to])
				} else if d[e.to] >= biPrime && d[e.to] < bi {
					kListV = append(kListV, e.to)
					kListD = append(kListD, d[e.to])
				}
			}
		}
		for _, x := range si {
			if d[x] >= biPrime && d[x] < bi {
				kListV = append(kListV, x)
				kListD = append(kListD, d[x])
			}
		}
		ds.batchPrepend(kListV, kListD)

		if ds.isEmpty() {
			return b, mapToSlice(uSet)
		}
		if len(uSet) > k*twoLt {
			return biPrime, mapToSlice(uSet)
		}
	}

	bPrime := b0Prime
	if iter > 0 {
		bPrime = lastBiPrime
	}
	for _, x := range w {
		if d[x] < bPrime {
			uSet[x] = struct{}{}
		}
	}
	return bPrime, mapToSlice(uSet)
}

func baseCase(g *Graph, d []float64, pred []int, b float64, s []int, n, k int) (float64, []int) {
	x := s[0]
	var u0 []int
	heap := newMinHeap(n)
	heap.insert(x, d[x])

	for !heap.isEmpty() && len(u0) < k+1 {
		u, du := heap.extractMin()
		u0 = append(u0, u)
		for _, e := range g.OutEdges(u) {
			newD := du + e.weight
			if newD >= b || newD > d[e.to] {
				continue
			}
			relax(d, pred, u, e.to, e.weight)
			if heap.contains(e.to) {
				heap.decreaseKey(e.to, d[e.to])
			} else {
				heap.insert(e.to, d[e.to])
			}
		}
	}

	if len(u0) <= k {
		return b, u0
	}
	bPrime := b
	for _, v := range u0 {
		if d[v] > bPrime {
			bPrime = d[v]
		}
	}
	var filtered []int
	for _, v := range u0 {
		if d[v] < bPrime {
			filtered = append(filtered, v)
		}
	}
	return bPrime, filtered
}

func findPivots(g *Graph, d []float64, pred []int, b float64, s []int, k int) (p, w []int) {
	w = append([]int{}, s...)
	wi := append([]int{}, s...)

	for round := 1; round <= k; round++ {
		var wiNext []int
		for _, u := range wi {
			for _, e := range g.OutEdges(u) {
				newD := d[u] + e.weight
				if newD > d[e.to] {
					continue
				}
				relax(d, pred, u, e.to, e.weight)
				if newD < b {
					wiNext = append(wiNext, e.to)
				}
			}
		}
		w = append(w, wiNext...)
		wi = wiNext
		if len(w) > k*len(s) {
			return s, w
		}
	}

	inW := make(map[int]struct{}, len(w))
	for _, v := range w {
		inW[v] = struct{}{}
	}
	parent := make([]int, g.VertexCount())
	for i := range parent {
		parent[i] = -1
	}
	for _, u := range w {
		for _, e := range g.OutEdges(u) {
			if _, ok := inW[e.to]; ok && math.Abs(d[e.to]-(d[u]+e.weight)) < eps {
				if parent[e.to] == -1 {
					parent[e.to] = u
				}
			}
		}
	}

	children := make([][]int, g.VertexCount())
	for _, v := range w {
		if parent[v] >= 0 {
			children[parent[v]] = append(children[parent[v]], v)
		}
	}

	subtreeSize := make([]int, g.VertexCount())
	var countSubtree func(int) int
	countSubtree = func(u int) int {
		if subtreeSize[u] != 0 {
			return subtreeSize[u]
		}
		s := 1
		for _, v := range children[u] {
			s += countSubtree(v)
		}
		subtreeSize[u] = s
		return s
	}

	hasParent := make(map[int]struct{}, len(w))
	for _, v := range w {
		if parent[v] >= 0 {
			hasParent[v] = struct{}{}
		}
	}
	var rootsInS []int
	for _, r := range s {
		if _, ok := hasParent[r]; !ok {
			if countSubtree(r) >= k {
				rootsInS = append(rootsInS, r)
			}
		}
	}
	return rootsInS, w
}

func relax(d []float64, pred []int, u, v int, w float64) {
	newD := d[u] + w
	if newD >= d[v] {
		return
	}
	d[v] = newD
	pred[v] = u
}

func pow2(exp int) int {
	if exp <= 0 {
		return 1
	}
	if exp > 30 {
		exp = 30
	}
	return 1 << exp
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func mapToSlice(m map[int]struct{}) []int {
	out := make([]int, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	return out
}

// --- frontierDS ---
type frontierDS struct {
	m            int
	b            float64
	keyToValue   map[int]float64
	list         []struct{ v float64; k int }
	sorted       bool
}

func newFrontierDS(m int, b float64) *frontierDS {
	if m < 1 {
		m = 1
	}
	cap := m * 2
	if cap > 64000 {
		cap = 64000
	}
	return &frontierDS{
		m:          m,
		b:          b,
		keyToValue: make(map[int]float64, cap),
		list:       make([]struct{ v float64; k int }, 0, cap),
	}
}

func (f *frontierDS) insert(key int, value float64) {
	if old, ok := f.keyToValue[key]; ok && value >= old {
		return
	}
	// remove old (value, key) from list
	for i := 0; i < len(f.list); i++ {
		if f.list[i].k == key {
			f.list = append(f.list[:i], f.list[i+1:]...)
			break
		}
	}
	f.keyToValue[key] = value
	f.list = append(f.list, struct{ v float64; k int }{value, key})
	f.sorted = false
}

func (f *frontierDS) batchPrepend(keys []int, values []float64) {
	for i, key := range keys {
		value := values[i]
		if old, ok := f.keyToValue[key]; ok && value >= old {
			continue
		}
		for j := 0; j < len(f.list); j++ {
			if f.list[j].k == key {
				f.list = append(f.list[:j], f.list[j+1:]...)
				break
			}
		}
		f.keyToValue[key] = value
		f.list = append(f.list, struct{ v float64; k int }{value, key})
	}
	f.sorted = false
}

func (f *frontierDS) pull() (bound float64, keys []int, ok bool) {
	if len(f.list) == 0 {
		return f.b, nil, false
	}
	if !f.sorted {
		sort.Slice(f.list, func(i, j int) bool {
			if f.list[i].v != f.list[j].v {
				return f.list[i].v < f.list[j].v
			}
			return f.list[i].k < f.list[j].k
		})
		f.sorted = true
	}
	take := f.m
	if take > len(f.list) {
		take = len(f.list)
	}
	keys = make([]int, take)
	for i := 0; i < take; i++ {
		keys[i] = f.list[i].k
		delete(f.keyToValue, f.list[i].k)
	}
	f.list = f.list[take:]
	if len(f.list) > 0 {
		bound = f.list[0].v
	} else {
		bound = f.b
	}
	return bound, keys, true
}

func (f *frontierDS) isEmpty() bool {
	return len(f.list) == 0
}

// --- minHeap ---
type minHeap struct {
	heap  []struct{ v int; d float64 }
	index []int
}

func newMinHeap(maxVertex int) *minHeap {
	idx := make([]int, maxVertex)
	for i := range idx {
		idx[i] = -1
	}
	heapCap := maxVertex
	if heapCap > 4096 {
		heapCap = 4096
	}
	return &minHeap{
		heap:  make([]struct{ v int; d float64 }, 0, heapCap),
		index: idx,
	}
}

func (h *minHeap) isEmpty() bool {
	return len(h.heap) == 0
}

func (h *minHeap) contains(v int) bool {
	return v < len(h.index) && h.index[v] >= 0
}

func (h *minHeap) insert(v int, d float64) {
	i := len(h.heap)
	h.heap = append(h.heap, struct{ v int; d float64 }{v, d})
	h.index[v] = i
	h.siftUp(i)
}

func (h *minHeap) extractMin() (int, float64) {
	top := h.heap[0]
	h.index[top.v] = -1
	h.heap[0] = h.heap[len(h.heap)-1]
	h.heap = h.heap[:len(h.heap)-1]
	if len(h.heap) > 0 {
		h.index[h.heap[0].v] = 0
		h.siftDown(0)
	}
	return top.v, top.d
}

func (h *minHeap) decreaseKey(v int, newD float64) {
	i := h.index[v]
	if i < 0 || h.heap[i].d <= newD {
		return
	}
	h.heap[i] = struct{ v int; d float64 }{v, newD}
	h.siftUp(i)
}

func (h *minHeap) siftUp(i int) {
	for i > 0 {
		p := (i - 1) / 2
		if h.heap[p].d <= h.heap[i].d {
			break
		}
		h.swap(i, p)
		i = p
	}
}

func (h *minHeap) siftDown(i int) {
	for {
		l, r, small := 2*i+1, 2*i+2, i
		if l < len(h.heap) && h.heap[l].d < h.heap[small].d {
			small = l
		}
		if r < len(h.heap) && h.heap[r].d < h.heap[small].d {
			small = r
		}
		if small == i {
			break
		}
		h.swap(i, small)
		i = small
	}
}

func (h *minHeap) swap(i, j int) {
	a, b := h.heap[i], h.heap[j]
	h.heap[i], h.heap[j] = b, a
	h.index[a.v], h.index[b.v] = j, i
}
