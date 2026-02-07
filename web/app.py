"""
SSSP Benchmark web UI: trigger test suite, view history, charts, and results table.
Run from repo root: python web/app.py
"""

import json
import os
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from flask import Flask, jsonify, request, send_from_directory
from simple_websocket import Server, ConnectionClosed

from benchmark.db import get_connection, init_db

app = Flask(__name__)

# Prefer Astro build when present (npm run build in web/)
DIST_DIR = Path(__file__).resolve().parent / "dist"
HAS_DIST = (DIST_DIR / "index.html").is_file()

# In-memory: is a test suite currently running?
_run_process = None
_run_lock = threading.Lock()

# WebSocket clients for progress broadcast
_ws_clients = set()
_ws_clients_lock = threading.Lock()


def _broadcast(obj):
    """Send a JSON-serializable object to all connected WebSocket clients."""
    msg = json.dumps(obj)
    with _ws_clients_lock:
        dead = []
        for ws in _ws_clients:
            try:
                ws.send(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            _ws_clients.discard(ws)


def _get_sessions(limit=None):
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    try:
        cur = conn.execute(
            """SELECT s.id, s.created_at, s.languages, s.algorithm,
                      (SELECT COUNT(*) FROM runs r WHERE r.session_id = s.id) AS run_count
               FROM sessions s
               ORDER BY s.id DESC""" + (" LIMIT ?" if limit else ""),
            (limit,) if limit else (),
        )
        rows = cur.fetchall()
    except Exception:
        cur = conn.execute(
            """SELECT s.id, s.created_at, s.languages,
                      (SELECT COUNT(*) FROM runs r WHERE r.session_id = s.id) AS run_count
               FROM sessions s
               ORDER BY s.id DESC""" + (" LIMIT ?" if limit else ""),
            (limit,) if limit else (),
        )
        rows = [dict(r, algorithm="duan_mao_shu_yin") for r in cur.fetchall()]
    conn.close()
    return rows


def _get_session_runs(session_id):
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    try:
        cur = conn.execute(
            """SELECT id, session_id, language, wall_sec, peak_mem_mb, total_cpu_sec, error, iterations, created_at
               FROM runs WHERE session_id = ? ORDER BY id""",
            (session_id,),
        )
        rows = cur.fetchall()
    except sqlite3.OperationalError as e:
        if "iterations" not in str(e).lower() and "no such column" not in str(e).lower():
            conn.close()
            raise
        cur = conn.execute(
            """SELECT id, session_id, language, wall_sec, peak_mem_mb, total_cpu_sec, error, created_at
               FROM runs WHERE session_id = ? ORDER BY id""",
            (session_id,),
        )
        rows = [dict(r, iterations=None) for r in cur.fetchall()]
    conn.close()
    return rows


def _get_metrics_for_charts():
    """Sessions ordered by id; for each session, list of runs with language and metrics."""
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    try:
        sessions = conn.execute(
            "SELECT id, created_at, languages, algorithm FROM sessions ORDER BY id"
        ).fetchall()
    except Exception:
        sessions = conn.execute(
            "SELECT id, created_at, languages FROM sessions ORDER BY id"
        ).fetchall()
        sessions = [dict(s, algorithm="duan_mao_shu_yin") for s in sessions]
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
            "algorithm": s.get("algorithm", "duan_mao_shu_yin"),
            "runs": [dict(r) for r in runs],
        })
    conn.close()
    return out


def _start_harness(progress_url, algorithm="duan_mao_shu_yin", min_seconds=0, iterations=None):
    global _run_process
    if algorithm not in ("dijkstra", "duan_mao_shu_yin"):
        algorithm = "duan_mao_shu_yin"
    try:
        min_seconds = max(0.0, float(min_seconds))
    except (TypeError, ValueError):
        min_seconds = 0
    if iterations is not None and (not isinstance(iterations, int) or iterations < 1):
        iterations = None
    with _run_lock:
        if _run_process is not None and _run_process.poll() is None:
            return False
        env = os.environ.copy()
        if progress_url:
            env["PROGRESS_URL"] = progress_url.rstrip("/")
        cmd = [sys.executable, str(REPO_ROOT / "benchmark" / "run_benchmarks.py"), "--build", "--algorithm", algorithm]
        if iterations is not None and iterations > 0:
            cmd.extend(["--iterations", str(iterations)])
        elif min_seconds > 0:
            cmd.extend(["--min-seconds", str(min_seconds)])
        _run_process = subprocess.Popen(
            cmd,
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        return True


def _harness_running():
    with _run_lock:
        return _run_process is not None and _run_process.poll() is None


@app.route("/")
def index():
    if HAS_DIST:
        return send_from_directory(DIST_DIR, "index.html")
    return (
        "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>SSSP Benchmark</title></head>"
        "<body><p>Frontend not built. From repo root run: <code>cd web &amp;&amp; npm install &amp;&amp; npm run build</code></p></body></html>",
        503,
        {"Content-Type": "text/html; charset=utf-8"},
    )


@app.route("/assets/<path:filename>")
def assets(filename):
    if not HAS_DIST:
        return "", 404
    return send_from_directory(DIST_DIR / "assets", filename)


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
    try:
        row = conn.execute(
            "SELECT id, created_at, languages, algorithm FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    except Exception:
        row = conn.execute(
            "SELECT id, created_at, languages FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        row = (row[0], row[1], row[2], "duan_mao_shu_yin") if row else None
    conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    # Ensure each run has iterations (int or None) for the UI
    runs_out = []
    for r in runs:
        r = dict(r)
        if "iterations" not in r:
            r["iterations"] = None
        elif r["iterations"] is not None:
            try:
                r["iterations"] = int(r["iterations"])
            except (TypeError, ValueError):
                r["iterations"] = None
        runs_out.append(r)
    return jsonify({
        "id": row[0],
        "created_at": row[1],
        "languages": row[2],
        "algorithm": row[3] if len(row) > 3 else "duan_mao_shu_yin",
        "runs": runs_out,
    })


@app.route("/api/metrics")
def api_metrics():
    return jsonify(_get_metrics_for_charts())


@app.route("/ws", websocket=True)
def ws_route():
    ws = Server.accept(request.environ)
    with _ws_clients_lock:
        _ws_clients.add(ws)
    try:
        while True:
            ws.receive()
    except ConnectionClosed:
        pass
    finally:
        with _ws_clients_lock:
            _ws_clients.discard(ws)
    return ""


@app.route("/api/progress", methods=["POST"])
def api_progress():
    """Receive progress from the harness and broadcast to WebSocket clients."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        _broadcast(data)
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"ok": False}), 400


@app.route("/api/run", methods=["POST"])
def api_run():
    init_db()
    progress_url = None
    algorithm = "duan_mao_shu_yin"
    min_seconds = 0
    iterations = None
    if request.is_json:
        body = request.get_json(silent=True) or {}
        progress_url = body.get("progressUrl")
        algorithm = body.get("algorithm", algorithm)
        min_seconds = body.get("minSeconds", min_seconds)
        try:
            iterations = body.get("iterations")
            if iterations is None:
                pass
            elif isinstance(iterations, (int, float)) and 1 <= int(iterations) <= 10**9:
                iterations = int(iterations)
            elif isinstance(iterations, str) and iterations.strip().isdigit():
                iterations = int(iterations.strip())
                if iterations < 1:
                    iterations = None
            else:
                iterations = None
        except (TypeError, ValueError):
            iterations = None
    if not progress_url and request.referrer:
        from urllib.parse import urlparse
        p = urlparse(request.referrer)
        progress_url = p.scheme + "://" + p.netloc
    if not progress_url:
        progress_url = "http://127.0.0.1:5000"
    if not _start_harness(progress_url, algorithm, min_seconds, iterations):
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
