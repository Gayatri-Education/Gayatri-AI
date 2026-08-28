"""
db.py — Gayatri AI v5.0
SQLite persistence layer (Section 7). Replaces the legacy in-memory
conversation_history list and manual autosave thread. Three tables:
sessions, messages, stats (computed on the fly from messages/sources).
"""

import sqlite3
import json
import threading
from datetime import datetime, timezone

import config

_local = threading.local()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    """One connection per thread (Flet event handlers may run on different threads)."""
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA foreign_keys = ON")
    return _local.conn


def init_db() -> None:
    """Creates tables if they don't exist. Call once at app startup."""
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT 'New Chat',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            sources_json TEXT DEFAULT '[]',
            md_chunks_used_json TEXT DEFAULT '[]',
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS stats (
            session_id INTEGER PRIMARY KEY,
            keywords_generated INTEGER NOT NULL DEFAULT 0,
            searches_performed INTEGER NOT NULL DEFAULT 0,
            sources_found INTEGER NOT NULL DEFAULT 0,
            pages_crawled INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS session_context_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            content TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL DEFAULT 'fact',
            key TEXT NOT NULL,
            content TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 1.0,
            source_session_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (source_session_id) REFERENCES sessions(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS agent_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            goal TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS agent_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            step_index INTEGER NOT NULL,
            title TEXT NOT NULL,
            tool TEXT NOT NULL,
            tool_input TEXT NOT NULL DEFAULT '{}',
            tool_output TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            updated_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES agent_tasks(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_session_context_files_session_id ON session_context_files(session_id);
        CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
        CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
        CREATE INDEX IF NOT EXISTS idx_agent_tasks_session_id ON agent_tasks(session_id);
        CREATE INDEX IF NOT EXISTS idx_agent_steps_task_id ON agent_steps(task_id);
        """
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
def create_session(title: str = None) -> int:
    conn = get_connection()
    now = _now()
    cur = conn.execute(
        "INSERT INTO sessions (title, created_at, updated_at) VALUES (?, ?, ?)",
        (title or config.DEFAULT_SESSION_TITLE, now, now),
    )
    session_id = cur.lastrowid
    conn.execute(
        "INSERT INTO stats (session_id, keywords_generated, searches_performed, "
        "sources_found, pages_crawled) VALUES (?, 0, 0, 0, 0)",
        (session_id,),
    )
    conn.commit()
    return session_id


def get_session(session_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return dict(row) if row else None


def list_sessions() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
    return [dict(r) for r in rows]


def rename_session(session_id: int, new_title: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
        (new_title, _now(), session_id),
    )
    conn.commit()


def touch_session(session_id: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?", (_now(), session_id)
    )
    conn.commit()


def delete_session(session_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------
def add_message(session_id: int, role: str, content: str,
                 sources: list[dict] = None, md_chunks_used: list[str] = None) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO messages (session_id, role, content, timestamp, sources_json, "
        "md_chunks_used_json) VALUES (?, ?, ?, ?, ?, ?)",
        (
            session_id,
            role,
            content,
            _now(),
            json.dumps(sources or []),
            json.dumps(md_chunks_used or []),
        ),
    )
    conn.commit()
    touch_session(session_id)
    return cur.lastrowid


def get_messages(session_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,)
    ).fetchall()
    messages = []
    for r in rows:
        m = dict(r)
        m["sources"] = json.loads(m.pop("sources_json") or "[]")
        m["md_chunks_used"] = json.loads(m.pop("md_chunks_used_json") or "[]")
        messages.append(m)
    return messages


def delete_message(message_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()


def update_message_content(message_id: int, new_content: str) -> None:
    """Used for edit-and-resend of a previous user message (Section 6.3)."""
    conn = get_connection()
    conn.execute(
        "UPDATE messages SET content = ? WHERE id = ?", (new_content, message_id)
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
def get_stats(session_id: int) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM stats WHERE session_id = ?", (session_id,)
    ).fetchone()
    if row:
        return dict(row)
    return {
        "session_id": session_id,
        "keywords_generated": 0,
        "searches_performed": 0,
        "sources_found": 0,
        "pages_crawled": 0,
    }


def increment_stats(session_id: int, keywords_generated: int = 0, searches_performed: int = 0,
                     sources_found: int = 0, pages_crawled: int = 0) -> None:
    conn = get_connection()
    conn.execute(
        """
        UPDATE stats SET
            keywords_generated = keywords_generated + ?,
            searches_performed = searches_performed + ?,
            sources_found = sources_found + ?,
            pages_crawled = pages_crawled + ?
        WHERE session_id = ?
        """,
        (keywords_generated, searches_performed, sources_found, pages_crawled, session_id),
    )
    conn.commit()


def reset_stats(session_id: int) -> None:
    conn = get_connection()
    conn.execute(
        """
        UPDATE stats SET keywords_generated = 0, searches_performed = 0,
            sources_found = 0, pages_crawled = 0
        WHERE session_id = ?
        """,
        (session_id,),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Section 5A: Per-session context files (scoped to a single thread only,
# distinct from the global /workspace Context Center files)
# ---------------------------------------------------------------------------
MAX_SESSION_FILE_BYTES = 200_000  # ~200KB, per Section 5A.2 upload guard
SOFT_FILE_COUNT_WARNING = 10       # per Section 5A.2, non-blocking nudge


class SessionFileTooLargeError(Exception):
    """Raised when an uploaded per-session .md file exceeds MAX_SESSION_FILE_BYTES."""
    pass


def add_session_context_file(session_id: int, filename: str, content: str) -> int:
    """Adds a .md file scoped to a single session. Content is stored directly
    in the DB (not on disk) so it's automatically cleaned up via ON DELETE
    CASCADE when the session is deleted. Raises SessionFileTooLargeError if
    content exceeds MAX_SESSION_FILE_BYTES."""
    size = len(content.encode("utf-8"))
    if size > MAX_SESSION_FILE_BYTES:
        raise SessionFileTooLargeError(
            f"'{filename}' is {size // 1000}KB, over the {MAX_SESSION_FILE_BYTES // 1000}KB limit "
            f"for per-thread context files."
        )

    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO session_context_files (session_id, filename, content, enabled, created_at) "
        "VALUES (?, ?, ?, 1, ?)",
        (session_id, filename, content, _now()),
    )
    conn.commit()
    return cur.lastrowid


def get_session_context_files(session_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM session_context_files WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def set_session_context_file_enabled(file_id: int, enabled: bool) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE session_context_files SET enabled = ? WHERE id = ?",
        (1 if enabled else 0, file_id),
    )
    conn.commit()


def delete_session_context_file(file_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM session_context_files WHERE id = ?", (file_id,))
    conn.commit()


def count_session_context_files(session_id: int) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM session_context_files WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return row["cnt"] if row else 0


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def export_session_markdown(session_id: int) -> str:
    """Generates a clean Markdown transcript: question/answer pairs, sources,
    timestamps. Used by the 'Export Chat' UI action (Section 7)."""
    session = get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    messages = get_messages(session_id)
    lines = [f"# {session['title']}", f"_Exported: {_now()}_", ""]

    for m in messages:
        role_label = "User" if m["role"] == "user" else "Gayatri AI"
        lines.append(f"### {role_label} — {m['timestamp']}")
        lines.append(m["content"])

        if m["sources"]:
            lines.append("")
            lines.append("**Sources:**")
            for i, src in enumerate(m["sources"], 1):
                title = src.get("title", "Untitled")
                href = src.get("href", "")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Persistent Long-Term Memory (Second Brain)
# ---------------------------------------------------------------------------
def add_or_update_memory(
    key: str,
    content: str,
    category: str = "fact",
    confidence: float = 1.0,
    session_id: int = None,
) -> int:
    """Inserts a new memory or updates existing memory matching the key."""
    conn = get_connection()
    now = _now()
    clean_key = (key or "").strip().lower()
    clean_content = (content or "").strip()

    existing = conn.execute("SELECT id FROM memories WHERE LOWER(key) = ?", (clean_key,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE memories SET content = ?, category = ?, confidence = ?, "
            "source_session_id = COALESCE(?, source_session_id), updated_at = ? WHERE id = ?",
            (clean_content, category, confidence, session_id, now, existing["id"]),
        )
        conn.commit()
        return existing["id"]

    cur = conn.execute(
        "INSERT INTO memories (category, key, content, confidence, source_session_id, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (category, key.strip(), clean_content, confidence, session_id, now, now),
    )
    conn.commit()
    return cur.lastrowid


def list_memories(category: str = None) -> list[dict]:
    """Returns all stored memories ordered by updated_at descending."""
    conn = get_connection()
    if category:
        rows = conn.execute(
            "SELECT * FROM memories WHERE category = ? ORDER BY updated_at DESC", (category,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM memories ORDER BY updated_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_memory(memory_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    return dict(row) if row else None


def update_memory(memory_id: int, content: str, category: str = None) -> None:
    conn = get_connection()
    now = _now()
    if category:
        conn.execute(
            "UPDATE memories SET content = ?, category = ?, updated_at = ? WHERE id = ?",
            (content.strip(), category, now, memory_id),
        )
    else:
        conn.execute(
            "UPDATE memories SET content = ?, updated_at = ? WHERE id = ?",
            (content.strip(), now, memory_id),
        )
    conn.commit()


def delete_memory(memory_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()


def clear_all_memories() -> None:
    conn = get_connection()
    conn.execute("DELETE FROM memories")
    conn.commit()


def count_memories() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()
    return row["cnt"] if row else 0


# ---------------------------------------------------------------------------
# Agent Tasks & Steps Persistence
# ---------------------------------------------------------------------------
def create_agent_task(session_id: int, goal: str) -> int:
    """Creates a new agent task record."""
    conn = get_connection()
    now = _now()
    cur = conn.execute(
        "INSERT INTO agent_tasks (session_id, goal, status, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?)",
        (session_id, goal.strip(), now, now),
    )
    conn.commit()
    return cur.lastrowid


def get_agent_task(task_id: int) -> dict | None:
    """Retrieves an agent task by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM agent_tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def get_latest_agent_task(session_id: int) -> dict | None:
    """Retrieves the most recent agent task for a session."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM agent_tasks WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    return dict(row) if row else None


def update_agent_task_status(task_id: int, status: str) -> None:
    """Updates the status of an agent task."""
    conn = get_connection()
    now = _now()
    conn.execute(
        "UPDATE agent_tasks SET status = ?, updated_at = ? WHERE id = ?",
        (status, now, task_id),
    )
    conn.commit()


def create_agent_steps(task_id: int, steps: list[dict]) -> list[int]:
    """Persists a list of plan steps for an agent task."""
    conn = get_connection()
    now = _now()
    step_ids = []
    for idx, s in enumerate(steps):
        tool_input_str = s.get("tool_input", "")
        if isinstance(tool_input_str, (dict, list)):
            tool_input_str = json.dumps(tool_input_str)
        elif not isinstance(tool_input_str, str):
            tool_input_str = str(tool_input_str)

        cur = conn.execute(
            """
            INSERT INTO agent_steps (task_id, step_index, title, tool, tool_input, tool_output, status, updated_at)
            VALUES (?, ?, ?, ?, ?, '', 'pending', ?)
            """,
            (task_id, idx, s.get("title", f"Step {idx + 1}"), s.get("tool", "reason"), tool_input_str, now),
        )
        step_ids.append(cur.lastrowid)
    conn.commit()
    return step_ids


def get_agent_steps(task_id: int) -> list[dict]:
    """Retrieves all steps for an agent task ordered by step_index."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM agent_steps WHERE task_id = ? ORDER BY step_index ASC",
        (task_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_agent_step(step_id: int, status: str, tool_output: str = None) -> None:
    """Updates status and optionally tool output for an agent step."""
    conn = get_connection()
    now = _now()
    if tool_output is not None:
        conn.execute(
            "UPDATE agent_steps SET status = ?, tool_output = ?, updated_at = ? WHERE id = ?",
            (status, tool_output, now, step_id),
        )
    else:
        conn.execute(
            "UPDATE agent_steps SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, step_id),
        )
    conn.commit()
