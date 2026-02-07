"""
SQLite database for benchmark results in benchmark/data/benchmark.db.
Schema: sessions (each full benchmark run), runs (per-language), utilization (time series per run).
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "benchmark.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    languages TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    wall_sec REAL,
    peak_mem_mb REAL,
    total_cpu_sec REAL,
    error TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS utilization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    elapsed_sec REAL NOT NULL,
    cpu_pct REAL NOT NULL,
    mem_mb REAL NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE INDEX IF NOT EXISTS idx_runs_session ON runs(session_id);
CREATE INDEX IF NOT EXISTS idx_utilization_run ON utilization(run_id);
"""

__all__ = ["init_db", "insert_session", "insert_run", "DB_PATH"]


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create tables if they do not exist."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def insert_session(languages: list[str]) -> int:
    """Insert a new session; returns session_id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO sessions (created_at, languages) VALUES (?, ?)",
            (datetime.now(timezone.utc).isoformat(), ",".join(languages)),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def insert_run(
    session_id: int,
    language: str,
    wall_sec: Optional[float],
    peak_mem_mb: Optional[float],
    total_cpu_sec: Optional[float],
    error: Optional[str],
    utilization: list[dict],
) -> int:
    """Insert a run and its utilization samples; returns run_id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO runs (session_id, language, wall_sec, peak_mem_mb, total_cpu_sec, error, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                language,
                wall_sec,
                peak_mem_mb,
                total_cpu_sec,
                error,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        run_id = cur.lastrowid
        for s in utilization or []:
            conn.execute(
                "INSERT INTO utilization (run_id, elapsed_sec, cpu_pct, mem_mb) VALUES (?, ?, ?, ?)",
                (run_id, s.get("elapsed_sec", 0), s.get("cpu_pct", 0), s.get("mem_mb", 0)),
            )
        conn.commit()
        return run_id
    finally:
        conn.close()
