// Benchmark runner: read graph from GRAPH_FILE or argv[1], run SSSP(0), print DONE.
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"sssp"
)

func loadGraph(path string) (*sssp.Graph, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	sc.Scan()
	parts := strings.Fields(sc.Text())
	n, _ := strconv.Atoi(parts[0])
	m, _ := strconv.Atoi(parts[1])
	g := sssp.NewGraph(n)
	for i := 0; i < m && sc.Scan(); i++ {
		parts := strings.Fields(sc.Text())
		u, _ := strconv.Atoi(parts[0])
		v, _ := strconv.Atoi(parts[1])
		w, _ := strconv.ParseFloat(parts[2], 64)
		g.AddEdge(u, v, w)
	}
	return g, sc.Err()
}

func main() {
	path := os.Getenv("GRAPH_FILE")
	if len(os.Args) > 1 {
		path = os.Args[1]
	}
	if path == "" {
		fmt.Fprintln(os.Stderr, "Usage: benchmark <graph.txt>")
		os.Exit(1)
	}
	g, err := loadGraph(path)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	algo := strings.TrimSpace(strings.ToLower(os.Getenv("SSSP_ALGORITHM")))
	if algo == "" {
		algo = "duan_mao_shu_yin"
	}
	minSec := 0.0
	if s := os.Getenv("SSSP_MIN_SECONDS"); s != "" {
		if f, err := strconv.ParseFloat(strings.TrimSpace(s), 64); err == nil && f > 0 {
			minSec = f
		}
	}
	maxSec := 30.0
	if s := os.Getenv("SSSP_MAX_SECONDS"); s != "" {
		if f, err := strconv.ParseFloat(strings.TrimSpace(s), 64); err == nil && f > 0 {
			maxSec = f
		}
	}
	var r *sssp.SsspResult
	iterations := 1
	if minSec > 0 {
		start := time.Now()
		iterations = 0
		for time.Since(start).Seconds() < minSec && time.Since(start).Seconds() < maxSec {
			if algo == "dijkstra" {
				r = sssp.Dijkstra(g, 0)
			} else {
				r = sssp.DuanMaoShuYin(g, 0)
			}
			iterations++
		}
		reachable := 0
		for _, d := range r.Distance {
			if d < 1e30 {
				reachable++
			}
		}
		fmt.Println("DONE", r.VertexCount(), reachable, iterations)
	} else {
		if algo == "dijkstra" {
			r = sssp.Dijkstra(g, 0)
		} else {
			r = sssp.DuanMaoShuYin(g, 0)
		}
		reachable := 0
		for _, d := range r.Distance {
			if d < 1e30 {
				reachable++
			}
		}
		fmt.Println("DONE", r.VertexCount(), reachable, iterations)
	}
	if resultFile := os.Getenv("RESULT_FILE"); resultFile != "" {
		out, _ := json.Marshal(map[string]int{"iterations": iterations})
		os.WriteFile(resultFile, out, 0644)
	}
}
