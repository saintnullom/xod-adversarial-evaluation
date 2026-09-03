"""Persistence for user-recorded paired specialist evaluation measurements."""

from __future__ import annotations

import sqlite3
import uuid

from app.repositories.beliefs import utc_now


class SpecialistMeasurementRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """SELECT id, case_id, baseline_quality, specialist_quality, baseline_cost_usd, specialist_cost_usd,
                      baseline_latency_ms, specialist_latency_ms, created_at, updated_at
               FROM specialist_evaluation_measurements ORDER BY case_id"""
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert(self, payload: dict[str, object]) -> dict[str, object]:
        timestamp = utc_now()
        record = {"id": str(uuid.uuid4()), **payload, "created_at": timestamp, "updated_at": timestamp}
        with self.connection:
            self.connection.execute(
                """INSERT INTO specialist_evaluation_measurements
                   (id, case_id, baseline_quality, specialist_quality, baseline_cost_usd, specialist_cost_usd,
                    baseline_latency_ms, specialist_latency_ms, created_at, updated_at)
                   VALUES (:id, :case_id, :baseline_quality, :specialist_quality, :baseline_cost_usd, :specialist_cost_usd,
                           :baseline_latency_ms, :specialist_latency_ms, :created_at, :updated_at)
                   ON CONFLICT(case_id) DO UPDATE SET baseline_quality = excluded.baseline_quality,
                   specialist_quality = excluded.specialist_quality, baseline_cost_usd = excluded.baseline_cost_usd,
                   specialist_cost_usd = excluded.specialist_cost_usd, baseline_latency_ms = excluded.baseline_latency_ms,
                   specialist_latency_ms = excluded.specialist_latency_ms, updated_at = excluded.updated_at""",
                record,
            )
        row = self.connection.execute(
            """SELECT id, case_id, baseline_quality, specialist_quality, baseline_cost_usd, specialist_cost_usd,
                      baseline_latency_ms, specialist_latency_ms, created_at, updated_at
               FROM specialist_evaluation_measurements WHERE case_id = ?""",
            (str(payload["case_id"]),),
        ).fetchone()
        assert row is not None
        return dict(row)
