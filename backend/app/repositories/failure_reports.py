"""Voluntary failure capture for improving future XOD evaluation cases."""

from __future__ import annotations

import sqlite3
import uuid

from app.repositories.beliefs import utc_now


class FailureReportRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, payload: dict[str, object]) -> dict[str, object]:
        record = {"id": str(uuid.uuid4()), **payload, "created_at": utc_now()}
        with self.connection:
            self.connection.execute(
                """INSERT INTO failure_reports
                   (id, category, summary, expected_behavior, evaluation_case_id, source_analysis_message_id, created_at)
                   VALUES (:id, :category, :summary, :expected_behavior, :evaluation_case_id, :source_analysis_message_id, :created_at)""",
                record,
            )
        return record

    def list(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """SELECT id, category, summary, expected_behavior, evaluation_case_id, source_analysis_message_id, created_at
               FROM failure_reports ORDER BY created_at DESC"""
        ).fetchall()
        return [dict(row) for row in rows]
