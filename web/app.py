"""
SSSP Benchmark web UI: trigger test suite, view history, charts, and results table.
Run from repo root: python web/app.py
"""

import sys
import subprocess
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from flask import Flask, jsonify, render_template, request

from benchmark.db import get_connection, init_db

app = Flask(__name__, static_folder="static", template_folder="templates")

# In-memory: is a test suite currently running?
_run_process = None
_run_lock = threading.Lock()


def _get_sessions(limit=None):
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cur = conn.execute(
        """SELECT s.id, s.created_at, s.languages,
                  (SELECT COUNT(*) FROM runs r WHERE r.session_id = s.id) AS run_count
           FROM sessions s
           ORDER BY s.id DESC""" + (" LIMIT ?" if limit else ""),
        (limit,) if limit else (),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def _get_session_runs(session_id):
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cur = conn.execute(
        """SELECT id, session_id, language, wall_sec, peak_mem_mb, total_cpu_sec, error, created_at
           FROM runs WHERE session_id = ? ORDER BY id""",
        (session_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def _get_metrics_for_charts():
    """Sessions ordered by id; for each session, list of runs with language and metrics."""
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    sessions = conn.execute(
        "SELECT id, created_at, languages FROM sessions ORDER BY id"
    ).fetchall()
    out = []
    for s in sessions:
        runs = conn.execute(
            """SELECT language, wall_sec, peak_mem_mb, total_cpu_sec, error
               FROM runs WHERE session_id = ? ORDER BY id""",
            (s["id"],),
        ).fetchall()
        out.append({
            "session_id": s["id"],
            "created_at": s["created_at"],
            "languages": s["languages"],
            "runs": [dict(r) for r in runs],
        })
    conn.close()
    return out


def _start_harness():
    global _run_process
    with _run_lock:
        if _run_process is not None and _run_process.poll() is None:
            return False
        _run_process = subprocess.Popen(
            [sys.executable, str(REPO_ROOT / "benchmark" / "run_benchmarks.py")],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True


def _harness_running():
    with _run_lock:
        return _run_process is not None and _run_process.poll() is None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify({"running": _harness_running()})


@app.route("/api/sessions")
def api_sessions():
    limit = request.args.get("limit", type=int)
    sessions = _get_sessions(limit=limit)
    return jsonify(sessions)


@app.route("/api/sessions/<int:session_id>")
def api_session(session_id):
    runs = _get_session_runs(session_id)
    if not runs:
        return jsonify({"error": "not found"}), 404
    conn = get_connection()
    row = conn.execute(
        "SELECT id, created_at, languages FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "id": row[0],
        "created_at": row[1],
        "languages": row[2],
        "runs": runs,
    })


@app.route("/api/metrics")
def api_metrics():
    return jsonify(_get_metrics_for_charts())


@app.route("/api/run", methods=["POST"])
def api_run():
    init_db()
    if not _start_harness():
        return jsonify({"started": False, "message": "A test suite is already running."}), 409
    return jsonify({"started": True})


if __name__ == "__main__":
    import socket

    init_db()
    # Find an unused port by binding to port 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        port = s.getsockname()[1]

    print(f"Web UI available at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
