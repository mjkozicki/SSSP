(function () {
  const runBtn = document.getElementById("runBtn");
  const algorithmSelect = document.getElementById("algorithmSelect");
  const runStatus = document.getElementById("runStatus");
  const runProgress = document.getElementById("runProgress");
  const runProgressHeading = document.getElementById("runProgressHeading");
  const runProgressList = document.getElementById("runProgressList");
  const sessionsBody = document.getElementById("sessionsBody");
  const sessionSelect = document.getElementById("sessionSelect");
  const runsBody = document.getElementById("runsBody");
  const chartWall = document.getElementById("chartWall");
  const chartMem = document.getElementById("chartMem");
  const chartCpu = document.getElementById("chartCpu");

  const LANG_COLORS = [
    "#22d3d4", "#a78bfa", "#f472b6", "#fbbf24", "#34d399",
    "#f87171", "#60a5fa", "#c084fc"
  ];

  function setStatus(text, className) {
    runStatus.textContent = text;
    runStatus.className = "status" + (className ? " " + className : "");
  }

  function getWsUrl() {
    const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
    return scheme + "//" + window.location.host + "/ws";
  }

  var progressState = {}; // language -> { status, wall_sec, peak_mem_mb, total_cpu_sec, error }

  function renderProgressList() {
    const langs = Object.keys(progressState).sort();
    if (langs.length === 0) {
      runProgressList.innerHTML = "";
      return;
    }
    runProgressList.innerHTML = langs.map((lang) => {
      const s = progressState[lang];
      const status = s.status || "pending";
      let metrics = "";
      if (status === "done" || status === "error") {
        const parts = [];
        if (s.wall_sec != null) parts.push(s.wall_sec.toFixed(2) + "s");
        if (s.peak_mem_mb != null) parts.push(s.peak_mem_mb.toFixed(0) + " MiB");
        if (s.error) parts.push("Error");
        if (parts.length) metrics = " <span class=\"metrics\">(" + parts.join(", ") + ")</span>";
      }
      if (status === "built") metrics = " <span class=\"metrics\">(built)</span>";
      return "<li class=\"" + status + "\" data-lang=\"" + escapeHtml(lang) + "\"><span class=\"dot\"></span>" + escapeHtml(lang) + metrics + "</li>";
    }).join("");
  }

  function handleProgressMessage(data) {
    if (data.event === "build_started") {
      progressState = {};
      (data.languages || []).forEach((lang) => {
        progressState[lang] = { status: "pending" };
      });
      runProgressHeading.textContent = "Building images";
      runProgress.classList.remove("hidden");
      renderProgressList();
      return;
    }
    if (data.event === "building" && data.language) {
      if (!progressState[data.language]) progressState[data.language] = {};
      progressState[data.language].status = "building";
      renderProgressList();
      return;
    }
    if (data.event === "built" && data.language) {
      if (!progressState[data.language]) progressState[data.language] = {};
      progressState[data.language].status = "built";
      renderProgressList();
      return;
    }
    if (data.event === "build_finished") {
      runProgressHeading.textContent = "Build complete, starting tests…";
      return;
    }
    if (data.event === "suite_started") {
      progressState = {};
      (data.languages || []).forEach((lang) => {
        progressState[lang] = { status: "pending" };
      });
      runProgressHeading.textContent = "Running tests";
      runProgress.classList.remove("hidden");
      renderProgressList();
      return;
    }
    if (data.event === "started" && data.language) {
      if (!progressState[data.language]) progressState[data.language] = {};
      progressState[data.language].status = "running";
      renderProgressList();
      return;
    }
    if (data.event === "completed" && data.language) {
      if (!progressState[data.language]) progressState[data.language] = {};
      progressState[data.language].status = data.error ? "error" : "done";
      progressState[data.language].wall_sec = data.wall_sec;
      progressState[data.language].peak_mem_mb = data.peak_mem_mb;
      progressState[data.language].total_cpu_sec = data.total_cpu_sec;
      progressState[data.language].error = data.error;
      renderProgressList();
      return;
    }
    if (data.event === "suite_finished") {
      setTimeout(function () {
        runProgress.classList.add("hidden");
        runProgressHeading.textContent = "Current run";
        progressState = {};
        runProgressList.innerHTML = "";
        refresh();
      }, 1500);
    }
  }

  function connectWs() {
    const ws = new WebSocket(getWsUrl());
    ws.onmessage = function (ev) {
      try {
        const data = JSON.parse(ev.data);
        handleProgressMessage(data);
      } catch (e) {}
    };
    ws.onclose = function () {
      setTimeout(connectWs, 3000);
    };
    ws.onerror = function () {
      ws.close();
    };
  }
  connectWs();

  async function api(path, options = {}) {
    const res = await fetch(path, options);
    const data = res.ok ? await res.json().catch(() => ({})) : null;
    if (!res.ok) throw new Error(data?.message || res.statusText || "Request failed");
    return data;
  }

  async function loadSessions(limit = 50) {
    const sessions = await api("/api/sessions?limit=" + limit);
    return sessions;
  }

  function formatDate(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleString("en-US", { dateStyle: "short", timeStyle: "short", hour12: false });
  }

  function algorithmLabel(algo) {
    return algo === "dijkstra" ? "Dijkstra" : "Duan–Mao–Shu–Yin";
  }

  function renderSessions(sessions) {
    if (!sessions.length) {
      sessionsBody.innerHTML = '<tr><td colspan="6" class="empty">No runs yet. Start a test suite above.</td></tr>';
      return;
    }
    sessionsBody.innerHTML = sessions.map((s) => `
      <tr>
        <td class="num">#${s.id}</td>
        <td>${formatDate(s.created_at)}</td>
        <td>${escapeHtml(algorithmLabel(s.algorithm || "duan_mao_shu_yin"))}</td>
        <td>${escapeHtml(s.languages || "")}</td>
        <td class="num">${s.run_count ?? 0}</td>
        <td><a href="#" data-session-id="${s.id}">View results</a></td>
      </tr>
    `).join("");

    sessionsBody.querySelectorAll("a[data-session-id]").forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        const id = a.getAttribute("data-session-id");
        sessionSelect.value = id;
        loadSessionRuns(id);
      });
    });
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function fillSessionSelect(sessions) {
    const cur = sessionSelect.value;
    sessionSelect.innerHTML = sessions.length
      ? '<option value="">Select session…</option>' + sessions.map((s) =>
          `<option value="${s.id}">#${s.id} — ${formatDate(s.created_at)} — ${algorithmLabel(s.algorithm || "duan_mao_shu_yin")} (${s.run_count} runs)</option>`
        ).join("")
      : '<option value="">No sessions</option>';
    if (cur) sessionSelect.value = cur;
  }

  async function loadSessionRuns(sessionId) {
    if (!sessionId) {
      runsBody.innerHTML = '<tr><td colspan="5" class="empty">Select a session</td></tr>';
      return;
    }
    let session;
    try {
      session = await api("/api/sessions/" + sessionId);
    } catch {
      runsBody.innerHTML = '<tr><td colspan="5" class="empty">Failed to load session</td></tr>';
      return;
    }
    const runs = session.runs || [];
    if (!runs.length) {
      runsBody.innerHTML = '<tr><td colspan="5" class="empty">No runs in this session</td></tr>';
      return;
    }
    runsBody.innerHTML = runs.map((r) => `
      <tr>
        <td>${escapeHtml(r.language)}</td>
        <td class="num">${r.wall_sec != null ? Number(r.wall_sec).toFixed(3) : "—"}</td>
        <td class="num">${r.peak_mem_mb != null ? Number(r.peak_mem_mb).toFixed(2) : "—"}</td>
        <td class="num">${r.total_cpu_sec != null ? Number(r.total_cpu_sec).toFixed(3) : "—"}</td>
        <td class="err" title="${escapeHtml(r.error || "")}">${r.error ? escapeHtml(r.error) : "—"}</td>
      </tr>
    `).join("");
  }

  sessionSelect.addEventListener("change", () => loadSessionRuns(sessionSelect.value));

  async function loadMetrics() {
    const data = await api("/api/metrics");
    return data;
  }

  function buildChartData(metrics, valueKey, labelKey) {
    const languages = new Set();
    metrics.forEach((s) => s.runs.forEach((r) => languages.add(r.language)));
    const langList = [...languages].sort();
    const sessionLabels = metrics.map((s) => "Session " + s.session_id);
    const datasets = langList.map((lang, i) => {
      const values = metrics.map((s) => {
        const run = s.runs.find((r) => r.language === lang);
        const v = run ? run[valueKey] : null;
        return v != null ? Number(v) : null;
      });
      return {
        label: lang,
        data: values,
        borderColor: LANG_COLORS[i % LANG_COLORS.length],
        backgroundColor: LANG_COLORS[i % LANG_COLORS.length] + "20",
        fill: false,
        tension: 0.2,
        spanGaps: true
      };
    });
    return { labels: sessionLabels, datasets };
  }

  let chartWallInst, chartMemInst, chartCpuInst;

  function destroyCharts() {
    [chartWallInst, chartMemInst, chartCpuInst].forEach((c) => c && c.destroy());
  }

  function renderCharts(metrics) {
    destroyCharts();
    if (!metrics || !metrics.length) return;

    const opts = {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: "bottom" }
      },
      scales: {
        x: { grid: { color: "rgba(255,255,255,0.06)" }, ticks: { color: "#a1a1aa", maxRotation: 45 } },
        y: { grid: { color: "rgba(255,255,255,0.06)" }, ticks: { color: "#a1a1aa" }, beginAtZero: true }
      }
    };

    const wallData = buildChartData(metrics, "wall_sec", "Wall (s)");
    chartWallInst = new Chart(chartWall.getContext("2d"), {
      type: "line",
      data: wallData,
      options: opts
    });

    const memData = buildChartData(metrics, "peak_mem_mb", "Peak mem (MiB)");
    chartMemInst = new Chart(chartMem.getContext("2d"), {
      type: "line",
      data: memData,
      options: opts
    });

    const cpuData = buildChartData(metrics, "total_cpu_sec", "CPU (s)");
    chartCpuInst = new Chart(chartCpu.getContext("2d"), {
      type: "line",
      data: cpuData,
      options: opts
    });
  }

  async function refresh() {
    const sessions = await loadSessions();
    renderSessions(sessions);
    fillSessionSelect(sessions);
    const metrics = await loadMetrics();
    renderCharts(metrics);
    const status = await api("/api/status");
    if (status.running) {
      runBtn.disabled = true;
      setStatus("Test suite running…", "running");
    } else {
      runBtn.disabled = false;
      if (runStatus.classList.contains("running")) setStatus("Run finished.", "success");
      else if (!runStatus.textContent) setStatus("Idle", "");
    }
  }

  runBtn.addEventListener("click", async () => {
    try {
      const progressUrl = window.location.origin;
      const algorithm = algorithmSelect ? algorithmSelect.value : "duan_mao_shu_yin";
      const minSecondsCheck = document.getElementById("minSecondsCheck");
      const minSeconds = minSecondsCheck && minSecondsCheck.checked
        ? parseFloat(minSecondsCheck.value) || 10
        : 0;
      const result = await api("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          progressUrl: progressUrl,
          algorithm: algorithm,
          minSeconds: minSeconds
        })
      });
      if (!result.started) {
        setStatus(result.message || "Could not start.", "error");
        return;
      }
      runBtn.disabled = true;
      setStatus("Test suite running…", "running");
      const poll = setInterval(async () => {
        const status = await api("/api/status");
        if (!status.running) {
          clearInterval(poll);
          setStatus("Run finished.", "success");
          runBtn.disabled = false;
          refresh();
        }
      }, 2000);
    } catch (e) {
      setStatus(e.message || "Failed to start run", "error");
      runBtn.disabled = false;
    }
  });

  refresh();
  setInterval(refresh, 10000);
})();
