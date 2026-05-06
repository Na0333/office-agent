import sqlite3
from pathlib import Path

from app.config import get_settings


def get_connection() -> sqlite3.Connection:
    db_path = get_settings().resolved_database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    db_path: Path = get_settings().resolved_database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                assignee TEXT,
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                source_platform TEXT,
                source_user_id TEXT,
                source_group_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                tool_name TEXT,
                input_json TEXT,
                output_json TEXT,
                success INTEGER,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS file_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                source TEXT DEFAULT 'generated',
                created_at TEXT NOT NULL
            )
            """
        )
        _ensure_column(conn, "file_records", "summary", "TEXT")
        _ensure_column(conn, "file_records", "content_preview", "TEXT")
        _ensure_column(conn, "file_records", "metadata_json", "TEXT")
        _ensure_column(conn, "file_records", "indexed_at", "TEXT")

        # Agent memory tables
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_memory (
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                memory_data TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (session_id, user_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memory (
                user_id TEXT PRIMARY KEY,
                memory_data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        conn.commit()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
