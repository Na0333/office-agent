from datetime import datetime
import json
from pathlib import Path
from typing import Any

from app.database.db import get_connection, init_db


class FileRecordService:
    def __init__(self) -> None:
        init_db()

    def add_record(
        self,
        *,
        file_id: str,
        session_id: str,
        user_id: str,
        file_name: str,
        file_path: str,
        source: str = "generated",
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO file_records (
                    file_id, session_id, user_id, file_name, file_path, source, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (file_id, session_id, user_id, file_name, file_path, source, now),
            )
            conn.commit()

    def upsert_record(
        self,
        *,
        file_id: str,
        session_id: str,
        user_id: str,
        file_name: str,
        file_path: str,
        source: str = "upload",
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as conn:
            existing = conn.execute(
                """
                SELECT id FROM file_records
                WHERE session_id = ? AND user_id = ? AND file_path = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id, user_id, file_path),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE file_records
                    SET file_id = ?, file_name = ?, source = ?, created_at = ?
                    WHERE id = ?
                    """,
                    (file_id, file_name, source, now, existing["id"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO file_records (
                        file_id, session_id, user_id, file_name, file_path, source, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (file_id, session_id, user_id, file_name, file_path, source, now),
                )
            conn.commit()

    def list_records(self, session_id: str, user_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT file_id, file_name, file_path, source, summary, content_preview, metadata_json, indexed_at, created_at
                FROM file_records
                WHERE session_id = ? AND user_id = ?
                ORDER BY id DESC
                LIMIT 50
                """,
                (session_id, user_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_record(self, session_id: str, user_id: str, file_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT file_id, file_name, file_path, source, summary, content_preview, metadata_json, indexed_at, created_at
                FROM file_records
                WHERE session_id = ? AND user_id = ? AND file_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id, user_id, file_id),
            ).fetchone()
        return dict(row) if row else None

    def latest_record(self, session_id: str, user_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT file_id, file_name, file_path, source, summary, content_preview, metadata_json, indexed_at, created_at
                FROM file_records
                WHERE session_id = ? AND user_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id, user_id),
            ).fetchone()
        return dict(row) if row else None

    def search_records(self, session_id: str, user_id: str, query: str = "", limit: int = 10) -> list[dict[str, Any]]:
        pattern = f"%{query.strip()}%"
        with get_connection() as conn:
            if query.strip():
                rows = conn.execute(
                    """
                    SELECT file_id, file_name, file_path, source, summary, content_preview, metadata_json, indexed_at, created_at
                    FROM file_records
                    WHERE session_id = ? AND user_id = ?
                      AND (
                        file_id LIKE ?
                        OR file_name LIKE ?
                        OR file_path LIKE ?
                        OR COALESCE(summary, '') LIKE ?
                        OR COALESCE(content_preview, '') LIKE ?
                      )
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (session_id, user_id, pattern, pattern, pattern, pattern, pattern, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT file_id, file_name, file_path, source, summary, content_preview, metadata_json, indexed_at, created_at
                    FROM file_records
                    WHERE session_id = ? AND user_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (session_id, user_id, limit),
                ).fetchall()
        return [dict(row) for row in rows]

    def update_index(
        self,
        *,
        session_id: str,
        user_id: str,
        file_path: str,
        summary: str = "",
        content_preview: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE file_records
                SET summary = ?, content_preview = ?, metadata_json = ?, indexed_at = ?
                WHERE session_id = ? AND user_id = ? AND file_path = ?
                """,
                (
                    summary,
                    content_preview,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    now,
                    session_id,
                    user_id,
                    file_path,
                ),
            )
            conn.commit()

    def cleanup_missing_files(self) -> int:
        with get_connection() as conn:
            rows = conn.execute("SELECT id, file_path FROM file_records").fetchall()
            delete_ids = [row["id"] for row in rows if not Path(row["file_path"]).exists()]
            if delete_ids:
                conn.executemany("DELETE FROM file_records WHERE id = ?", [(row_id,) for row_id in delete_ids])
                conn.commit()
        return len(delete_ids)
