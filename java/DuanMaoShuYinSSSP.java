package sssp;

import java.util.*;

public final class DuanMaoShuYinSSSP {
    private static final int MAX_ITER = 100_000_000;
    private static final double EPS = 1e-12;

    public static SsspResult solve(Graph g, int source) {
        int n = g.vertexCount();
        if (n == 0) {
            return new SsspResult(new double[0], new Integer[0]);
        }
        double[] d = new double[n];
        Integer[] pred = new Integer[n];
        Arrays.fill(d, Double.POSITIVE_INFINITY);
        d[source] = 0;

        double tLog = Math.log(Math.max(n, 2)) / Math.log(2.0);
        int t = Math.max(1, (int) Math.floor(Math.pow(tLog, 2.0 / 3.0)));
        int k = Math.max(1, (int) Math.floor(Math.pow(tLog, 1.0 / 3.0)));
        int l = (int) Math.ceil(tLog / t);

        List<Integer> s = Collections.singletonList(source);
        bmssp(g, d, pred, l, Double.POSITIVE_INFINITY, s, n, k, t);

        return new SsspResult(d, pred);
    }

    private static void relax(double[] d, Integer[] pred, int u, int v, double w) {
        double newD = d[u] + w;
        if (newD >= d[v]) return;
        d[v] = newD;
        pred[v] = u;
    }

    private static int pow2(int exp) {
        if (exp <= 0) return 1;
        return 1 << Math.min(exp, 30);
    }

    private static class MinHeap {
        private final List<double[]> heap;
        private final int[] index;

        MinHeap(int maxVertex) {
            index = new int[maxVertex];
            Arrays.fill(index, -1);
            heap = new ArrayList<>(Math.min(maxVertex, 4096));
        }

        boolean isEmpty() { return heap.isEmpty(); }
        boolean contains(int v) { return v < index.length && index[v] >= 0; }

        void insert(int v, double dist) {
            int i = heap.size();
            heap.add(new double[]{v, dist});
            index[v] = i;
            siftUp(i);
        }

        double[] extractMin() {
            double[] top = heap.get(0);
            index[(int) top[0]] = -1;
            heap.set(0, heap.get(heap.size() - 1));
            heap.remove(heap.size() - 1);
            if (!heap.isEmpty()) index[(int) heap.get(0)[0]] = 0;
            if (!heap.isEmpty()) siftDown(0);
            return top;
        }

        double dist(int i) { return heap.get(i)[1]; }

        void decreaseKey(int v, double newD) {
            int i = index[v];
            if (i < 0 || dist(i) <= newD) return;
            heap.set(i, new double[]{v, newD});
            siftUp(i);
        }

        void siftUp(int i) {
            while (i > 0) {
                int p = (i - 1) / 2;
                if (dist(p) <= dist(i)) break;
                swap(i, p);
                i = p;
            }
        }

        void siftDown(int i) {
            while (true) {
                int l = 2 * i + 1, r = 2 * i + 2, small = i;
                if (l < heap.size() && dist(l) < dist(small)) small = l;
                if (r < heap.size() && dist(r) < dist(small)) small = r;
                if (small == i) break;
                swap(i, small);
                i = small;
            }
        }

        void swap(int i, int j) {
            double[] a = heap.get(i), b = heap.get(j);
            heap.set(i, b);
            heap.set(j, a);
            index[(int) a[0]] = j;
            index[(int) b[0]] = i;
        }
    }

    private static class FrontierDS {
        final int m;
        final double b;
        final Map<Integer, Double> keyToValue;
        final List<double[]> list;
        boolean sorted = true;

        FrontierDS(int m, double b) {
            this.m = Math.max(m, 1);
            this.b = b;
            int cap = Math.min(this.m * 2, 64000);
            keyToValue = new HashMap<>(cap);
            list = new ArrayList<>(cap);
        }

        void insert(int key, double value) {
            Double old = keyToValue.get(key);
            if (old != null && value >= old) return;
            list.removeIf(p -> (int) p[1] == key);
            keyToValue.put(key, value);
            list.add(new double[]{value, key});
            sorted = false;
        }

        void batchPrepend(List<double[]> pairs) {
            for (double[] p : pairs) {
                int key = (int) p[0];
                double value = p[1];
                Double old = keyToValue.get(key);
                if (old != null && value >= old) continue;
                list.removeIf(e -> (int) e[1] == key);
                keyToValue.put(key, value);
                list.add(new double[]{value, key});
            }
            sorted = false;
        }

        double[] pull(List<Integer> outKeys) {
            if (list.isEmpty()) return null;
            if (!sorted) {
                list.sort((a, b) -> {
                    int c = Double.compare(a[0], b[0]);
                    return c != 0 ? c : Double.compare(a[1], b[1]);
                });
                sorted = true;
            }
            int take = Math.min(m, list.size());
            outKeys.clear();
            for (int i = 0; i < take; i++) {
                outKeys.add((int) list.get(i)[1]);
                keyToValue.remove((int) list.get(i)[1]);
            }
            for (int i = 0; i < take; i++) list.remove(0);
            double bound = list.isEmpty() ? b : list.get(0)[0];
            return new double[]{bound};
        }

        boolean isEmpty() { return list.isEmpty(); }
    }

    private static int countSubtree(int u, List<List<Integer>> children, int[] size) {
        if (size[u] != 0) return size[u];
        int s = 1;
        for (int v : children.get(u)) s += countSubtree(v, children, size);
        size[u] = s;
        return s;
    }

    private static class PW {
        List<Integer> p, w;
        PW(List<Integer> p, List<Integer> w) { this.p = p; this.w = w; }
    }

    private static PW findPivots(Graph g, double[] d, Integer[] pred, double b, List<Integer> s, int k) {
        List<Integer> w = new ArrayList<>(s);
        List<Integer> wi = new ArrayList<>(s);
        for (int round = 1; round <= k; round++) {
            List<Integer> wiNext = new ArrayList<>();
            for (int u : wi) {
                for (double[] e : g.outEdges(u)) {
                    int v = (int) e[0];
                    double wE = e[1];
                    double newD = d[u] + wE;
                    if (newD > d[v]) continue;
                    relax(d, pred, u, v, wE);
                    if (newD < b) wiNext.add(v);
                }
            }
            w.addAll(wiNext);
            wi = wiNext;
            if (w.size() > k * s.size())
                return new PW(new ArrayList<>(s), w);
        }
        Set<Integer> inW = new HashSet<>(w.size());
        inW.addAll(w);
        Integer[] parent = new Integer[g.vertexCount()];
        for (int u : w) {
            for (double[] e : g.outEdges(u)) {
                int v = (int) e[0];
                double wE = e[1];
                if (inW.contains(v) && Math.abs(d[v] - (d[u] + wE)) < EPS && parent[v] == null)
                    parent[v] = u;
            }
        }
        List<List<Integer>> children = new ArrayList<>();
        for (int i = 0; i < g.vertexCount(); i++) children.add(new ArrayList<>());
        for (int v : w)
            if (parent[v] != null) children.get(parent[v]).add(v);
        int[] subtreeSize = new int[g.vertexCount()];
        Set<Integer> hasParent = new HashSet<>(w.size());
        for (int v : w) if (parent[v] != null) hasParent.add(v);
        List<Integer> rootsInS = new ArrayList<>();
        for (int r : s) {
            if (!hasParent.contains(r) && countSubtree(r, children, subtreeSize) >= k)
                rootsInS.add(r);
        }
        return new PW(rootsInS, w);
    }

    private static Object[] baseCaseFull(Graph g, double[] d, Integer[] pred, double b, List<Integer> s, int n, int k) {
        int x = s.get(0);
        List<Integer> u0 = new ArrayList<>();
        MinHeap heap = new MinHeap(n);
        heap.insert(x, d[x]);
        while (!heap.isEmpty() && u0.size() < k + 1) {
            double[] top = heap.extractMin();
            int u = (int) top[0];
            double du = top[1];
            u0.add(u);
            for (double[] e : g.outEdges(u)) {
                int v = (int) e[0];
                double wE = e[1];
                double newD = du + wE;
                if (newD >= b || newD > d[v]) continue;
                relax(d, pred, u, v, wE);
                if (heap.contains(v)) heap.decreaseKey(v, d[v]);
                else heap.insert(v, d[v]);
            }
        }
        if (u0.size() <= k)
            return new Object[]{b, u0};
        double bPrime = b;
        for (int v : u0) if (d[v] > bPrime) bPrime = d[v];
        List<Integer> filtered = new ArrayList<>();
        for (int v : u0) if (d[v] < bPrime) filtered.add(v);
        return new Object[]{bPrime, filtered};
    }

    @SuppressWarnings("unchecked")
    private static Object[] bmssp(Graph g, double[] d, Integer[] pred, int l, double b, List<Integer> s, int n, int k, int t) {
        int twoLt = pow2(l * t);
        if (l == 0) {
            Object[] bc = baseCaseFull(g, d, pred, b, s, n, k);
            return bc;
        }
        PW pw = findPivots(g, d, pred, b, s, k);
        List<Integer> p = pw.p, w = pw.w;
        int m = Math.max(pow2((l - 1) * t), 1);
        FrontierDS ds = new FrontierDS(m, b);
        for (int x : p) ds.insert(x, d[x]);
        double b0Prime = b;
        for (int x : p) if (d[x] < b0Prime) b0Prime = d[x];
        int uSetCap = Math.min(k * twoLt, 1_000_000);
        Set<Integer> uSet = new HashSet<>(uSetCap);
        double lastBiPrime = b0Prime;
        int iter = 0;
        List<Integer> si = new ArrayList<>();
        while (uSet.size() < k * twoLt && iter < MAX_ITER) {
            si.clear();
            double[] pullResult = ds.pull(si);
            if (pullResult == null) break;
            iter++;
            double bi = pullResult[0];
            Object[] rec = bmssp(g, d, pred, l - 1, bi, new ArrayList<>(si), n, k, t);
            double biPrime = (Double) rec[0];
            List<Integer> ui = (List<Integer>) rec[1];
            lastBiPrime = biPrime;
            uSet.addAll(ui);
            int kCap = Math.max(64, ui.size() * 4);
            List<double[]> kList = new ArrayList<>(kCap);
            for (int u : ui) {
                List<double[]> adj = g.outEdges(u);
                for (int i = 0; i < adj.size(); i++) {
                    double[] e = adj.get(i);
                    int v = (int) e[0];
                    double wE = e[1];
                    double newD = d[u] + wE;
                    if (newD > d[v]) continue;
                    relax(d, pred, u, v, wE);
                    if (d[v] >= bi && d[v] < b) ds.insert(v, d[v]);
                    else if (d[v] >= biPrime && d[v] < bi)
                        kList.add(new double[]{v, d[v]});
                }
            }
            for (int x : si)
                if (d[x] >= biPrime && d[x] < bi)
                    kList.add(new double[]{x, d[x]});
            ds.batchPrepend(kList);
            if (ds.isEmpty())
                return new Object[]{b, new ArrayList<>(uSet)};
            if (uSet.size() > k * twoLt)
                return new Object[]{biPrime, new ArrayList<>(uSet)};
        }
        double bPrime = iter > 0 ? lastBiPrime : b0Prime;
        for (int x : w) if (d[x] < bPrime) uSet.add(x);
        return new Object[]{bPrime, new ArrayList<>(uSet)};
    }
}
