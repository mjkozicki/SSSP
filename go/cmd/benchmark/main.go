// Benchmark runner: read graph from GRAPH_FILE or argv[1], run SSSP(0), print DONE.
// When OTEL_EXPORTER_OTLP_ENDPOINT is set, emits a trace span for the run (e.g. SigNoz).
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"sssp"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
)

func initTracer(ctx context.Context) (func(context.Context), error) {
	if os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT") == "" {
		return nil, nil
	}
	exporter, err := otlptracehttp.New(ctx)
	if err != nil {
		return nil, err
	}
	svcName := os.Getenv("OTEL_SERVICE_NAME")
	if svcName == "" {
		svcName = "sssp-bench-go"
	}
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(resource.NewWithAttributes(semconv.SchemaURL, semconv.ServiceNameKey.String(svcName))),
	)
	otel.SetTracerProvider(tp)
	return func(c context.Context) { _ = tp.Shutdown(c) }, nil
}

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
	g.Compact()
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
	fixedIters := 0
	if s := os.Getenv("SSSP_ITERATIONS"); s != "" {
		if n, err := strconv.Atoi(strings.TrimSpace(s)); err == nil && n > 0 {
			fixedIters = n
		}
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
	ctx := context.Background()
	shutdown, err := initTracer(ctx)
	if err != nil {
		fmt.Fprintln(os.Stderr, "otel init:", err)
	}
	if shutdown != nil {
		defer shutdown(ctx)
	}

	runBench := func() {
		if fixedIters > 0 {
			if algo == "dijkstra" {
				r = sssp.Dijkstra(g, 0)
			} else {
				r = sssp.DuanMaoShuYin(g, 0)
			}
			for i := 1; i < fixedIters; i++ {
				if algo == "dijkstra" {
					r = sssp.Dijkstra(g, 0)
				} else {
					r = sssp.DuanMaoShuYin(g, 0)
				}
			}
			iterations = fixedIters
		} else if minSec > 0 {
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
		} else {
			if algo == "dijkstra" {
				r = sssp.Dijkstra(g, 0)
			} else {
				r = sssp.DuanMaoShuYin(g, 0)
			}
		}
	}

	var r *sssp.SsspResult
	iterations := 1
	tracer := otel.Tracer("sssp-bench-go")
	if shutdown != nil {
		ctx, span := tracer.Start(ctx, "sssp.benchmark")
		defer span.End()
		span.SetAttributes(attribute.String("sssp.algorithm", algo))
		runBench()
		span.SetAttributes(attribute.Int("sssp.iterations", iterations))
	} else {
		runBench()
	}
	_ = r
	if resultFile := os.Getenv("RESULT_FILE"); resultFile != "" {
		out, _ := json.Marshal(map[string]int{"iterations": iterations})
		os.WriteFile(resultFile, out, 0644)
	}
}
