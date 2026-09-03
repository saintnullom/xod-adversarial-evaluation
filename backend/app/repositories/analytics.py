"""Read-only SQLite queries for XOD's retrospective metrics."""

from __future__ import annotations

import sqlite3


class AnalyticsRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def belief_history(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """SELECT b.id AS belief_id, b.proposition, b.current_version, b.status, b.user_confidence AS current_confidence,
                      b.updated_at AS revised_at, initial.user_confidence AS initial_confidence
               FROM beliefs b
               JOIN belief_versions initial ON initial.belief_id = b.id AND initial.version = 1
               ORDER BY b.updated_at DESC"""
        ).fetchall()
        return [dict(row) for row in rows]

    def predictions(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """SELECT id, belief_id, belief_confidence_at_commit, status, impact
               FROM predictions ORDER BY created_at DESC"""
        ).fetchall()
        return [dict(row) for row in rows]
