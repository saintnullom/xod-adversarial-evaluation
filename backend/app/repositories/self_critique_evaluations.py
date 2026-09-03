"""Persistence for repeatable self-critique quality evaluations."""

from __future__ import annotations

import json
import sqlite3

from app.repositories.beliefs import utc_now
from app.schemas import SelfCritiqueCheck


class SelfCritiqueEvaluationRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def analysis_payload(self, message_id: str) -> str | None:
        row = self.connection.execute(
            "SELECT payload_json FROM analyses WHERE message_id = ?", (message_id,)
        ).fetchone()
        return str(row["payload_json"]) if row else None

    def get(self, message_id: str) -> dict[str, object] | None:
        row = self.connection.execute(
            """SELECT message_id, rubric_version, score, verdict, checks_json, created_at
               FROM self_critique_evaluations WHERE message_id = ?""",
            (message_id,),
        ).fetchone()
        if row is None:
            return None
        record = dict(row)
        checks = json.loads(str(record.pop("checks_json")))
        return {**record, "checks": checks}

    def upsert(
        self, message_id: str, rubric_version: str, score: int, verdict: str, checks: list[SelfCritiqueCheck]
    ) -> dict[str, object]:
        record = {
            "message_id": message_id,
            "rubric_version": rubric_version,
            "score": score,
            "verdict": verdict,
            "checks_json": json.dumps([check.model_dump() for check in checks]),
            "created_at": utc_now(),
        }
        with self.connection:
            self.connection.execute(
                """INSERT INTO self_critique_evaluations
                   (message_id, rubric_version, score, verdict, checks_json, created_at)
                   VALUES (:message_id, :rubric_version, :score, :verdict, :checks_json, :created_at)
                   ON CONFLICT(message_id) DO UPDATE SET rubric_version = excluded.rubric_version,
                   score = excluded.score, verdict = excluded.verdict, checks_json = excluded.checks_json,
                   created_at = excluded.created_at""",
                record,
            )
        return {
            "message_id": message_id,
            "rubric_version": rubric_version,
            "score": score,
            "verdict": verdict,
            "checks": json.loads(str(record["checks_json"])),
            "created_at": str(record["created_at"]),
        }
