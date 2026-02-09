package sssp;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.exporter.otlp.trace.OtlpGrpcSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.semconv.ResourceAttributes;

import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Reads graph from file (n m then u v w lines), runs SSSP(0), prints DONE.
 * When OTEL_EXPORTER_OTLP_ENDPOINT is set, emits a trace span (e.g. for SigNoz). */
public final class Benchmark {
    public static void main(String[] args) throws IOException {
        String path = args.length > 0 ? args[0] : System.getenv("GRAPH_FILE");
        if (path == null || path.isEmpty()) {
            System.err.println("Usage: java sssp.Benchmark <graph.txt>");
            System.exit(1);
        }
        Graph g = loadGraph(path);
        String algo = System.getenv("SSSP_ALGORITHM");
        if (algo == null) algo = "duan_mao_shu_yin";
        algo = algo.trim().toLowerCase();
        int fixedIters = 0;
        String itersEnv = System.getenv("SSSP_ITERATIONS");
        if (itersEnv != null && !itersEnv.isBlank()) {
            try {
                fixedIters = Integer.parseInt(itersEnv.trim());
            } catch (NumberFormatException ignored) {}
        }
        double minSec = 0.0;
        String minSecEnv = System.getenv("SSSP_MIN_SECONDS");
        if (minSecEnv != null && !minSecEnv.isBlank()) {
            try {
                minSec = Double.parseDouble(minSecEnv.trim());
            } catch (NumberFormatException ignored) {}
        }
        double maxSec = 30.0;
        String maxSecEnv = System.getenv("SSSP_MAX_SECONDS");
        if (maxSecEnv != null && !maxSecEnv.isBlank()) {
            try {
                maxSec = Double.parseDouble(maxSecEnv.trim());
            } catch (NumberFormatException ignored) {}
        }

        OpenTelemetry otel = initOpenTelemetry();
        Tracer tracer = otel != null ? otel.getTracer("sssp-bench-java", "1.0.0") : null;
        int[] iterationsHolder = { 1 };

        if (tracer != null) {
            Span span = tracer.spanBuilder("sssp.benchmark").setAttribute("sssp.algorithm", algo).startSpan();
            try {
                runBenchmark(g, algo, fixedIters, minSec, maxSec, iterationsHolder);
            } finally {
                span.setAttribute(AttributeKey.longKey("sssp.iterations"), iterationsHolder[0]);
                span.end();
            }
        } else {
            runBenchmark(g, algo, fixedIters, minSec, maxSec, iterationsHolder);
        }

        int iterations = iterationsHolder[0];
        String resultFile = System.getenv("RESULT_FILE");
        if (resultFile != null && !resultFile.isEmpty()) {
            try {
                Files.writeString(Path.of(resultFile), "{\"iterations\":" + iterations + "}");
            } catch (IOException ignored) {}
        }
    }

    private static OpenTelemetry initOpenTelemetry() {
        String endpoint = System.getenv("OTEL_EXPORTER_OTLP_ENDPOINT");
        if (endpoint == null || endpoint.isBlank()) return null;
        try {
            OtlpGrpcSpanExporter exporter = OtlpGrpcSpanExporter.builder().build();
            String svcName = System.getenv("OTEL_SERVICE_NAME");
            if (svcName == null || svcName.isBlank()) svcName = "sssp-bench-java";
            Resource resource = Resource.getDefault().toBuilder().put(ResourceAttributes.SERVICE_NAME, svcName).build();
            SdkTracerProvider provider = SdkTracerProvider.builder()
                .addSpanProcessor(BatchSpanProcessor.builder(exporter).build())
                .setResource(resource)
                .build();
            return OpenTelemetrySdk.builder().setTracerProvider(provider).buildAndRegisterGlobal();
        } catch (Throwable t) {
            return null;
        }
    }

    private static void runBenchmark(Graph g, String algo, int fixedIters, double minSec, double maxSec, int[] iterationsHolder) {
        SsspResult r;
        if (fixedIters > 0) {
            r = "dijkstra".equals(algo) ? Dijkstra.solve(g, 0) : DuanMaoShuYinSSSP.solve(g, 0);
            for (int i = 1; i < fixedIters; i++)
                r = "dijkstra".equals(algo) ? Dijkstra.solve(g, 0) : DuanMaoShuYinSSSP.solve(g, 0);
            iterationsHolder[0] = fixedIters;
        } else if (minSec > 0) {
            long startNanos = System.nanoTime();
            long minNanos = (long) (minSec * 1_000_000_000);
            long maxNanos = (long) (maxSec * 1_000_000_000);
            int iters = 0;
            do {
                r = "dijkstra".equals(algo) ? Dijkstra.solve(g, 0) : DuanMaoShuYinSSSP.solve(g, 0);
                iters++;
            } while (System.nanoTime() - startNanos < minNanos && System.nanoTime() - startNanos < maxNanos);
            iterationsHolder[0] = iters;
        } else {
            r = "dijkstra".equals(algo) ? Dijkstra.solve(g, 0) : DuanMaoShuYinSSSP.solve(g, 0);
        }
    }

    static Graph loadGraph(String path) throws IOException {
        try (Scanner sc = new Scanner(new File(path))) {
            int n = sc.nextInt(), m = sc.nextInt();
            Graph g = new Graph(n);
            for (int i = 0; i < m; i++)
                g.addEdge(sc.nextInt(), sc.nextInt(), sc.nextDouble());
            g.compact();
            return g;
        }
    }
}
