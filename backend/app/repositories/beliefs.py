"""Versioned belief persistence independent of conversations."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class BeliefRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(
        self,
        proposition: str,
        user_confidence: float | None = None,
        status: str = "ACTIVE_TEST",
        source_analysis_message_id: str | None = None,
        falsification_conditions: list[str] | None = None,
    ) -> dict[str, object]:
        belief_id = str(uuid.uuid4())
        timestamp = utc_now()
        with self.connection:
            self.connection.execute(
                """INSERT INTO beliefs (id, proposition, user_confidence, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (belief_id, proposition, user_confidence, status, timestamp, timestamp),
            )
            self._insert_version(
                belief_id, 1, proposition, user_confidence, status, None, source_analysis_message_id, timestamp
            )
            for condition in falsification_conditions or []:
                self._insert_falsification_condition(belief_id, condition, timestamp)
        belief = self.get(belief_id)
        assert belief is not None
        return belief

    def list(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """SELECT id, proposition, current_version, user_confidence, xod_confidence, status, created_at, updated_at
               FROM beliefs ORDER BY updated_at DESC"""
        ).fetchall()
        return [dict(row) for row in rows]

    def get(self, belief_id: str) -> dict[str, object] | None:
        belief = self.connection.execute(
            """SELECT id, proposition, current_version, user_confidence, xod_confidence, status, created_at, updated_at
               FROM beliefs WHERE id = ?""",
            (belief_id,),
        ).fetchone()
        if belief is None:
            return None
        versions = self.connection.execute(
            """SELECT id, belief_id, version, proposition, user_confidence, status, change_reason,
                      source_analysis_message_id, created_at
               FROM belief_versions WHERE belief_id = ? ORDER BY version DESC""",
            (belief_id,),
        ).fetchall()
        evidence = self.connection.execute(
            """SELECT id, belief_id, claim, source, source_type, url, retrieved_at, reliability, relevance,
                      direction, created_at
               FROM evidence WHERE belief_id = ? ORDER BY created_at DESC""",
            (belief_id,),
        ).fetchall()
        predictions = self.connection.execute(
            """SELECT id, belief_id, statement, success_criteria, created_at, belief_confidence_at_commit, expected_resolution_at, result,
                      status, impact, resolved_at
               FROM predictions WHERE belief_id = ? ORDER BY created_at DESC""",
            (belief_id,),
        ).fetchall()
        falsification_conditions = self.connection.execute(
            """SELECT id, belief_id, condition, created_at
               FROM belief_falsification_conditions WHERE belief_id = ? ORDER BY created_at DESC""",
            (belief_id,),
        ).fetchall()
        return {
            **dict(belief),
            "versions": [dict(version) for version in versions],
            "evidence": [dict(item) for item in evidence],
            "predictions": [dict(item) for item in predictions],
            "falsification_conditions": [dict(item) for item in falsification_conditions],
        }

    def revise(
        self,
        belief_id: str,
        proposition: str,
        user_confidence: float | None,
        status: str,
        reason: str | None = None,
        source_analysis_message_id: str | None = None,
    ) -> dict[str, object]:
        row = self.connection.execute(
            "SELECT current_version FROM beliefs WHERE id = ?", (belief_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown belief: {belief_id}")
        next_version = int(row["current_version"]) + 1
        timestamp = utc_now()
        with self.connection:
            self.connection.execute(
                """UPDATE beliefs SET proposition = ?, current_version = ?, user_confidence = ?, status = ?,
                   updated_at = ? WHERE id = ?""",
                (proposition, next_version, user_confidence, status, timestamp, belief_id),
            )
            self._insert_version(
                belief_id,
                next_version,
                proposition,
                user_confidence,
                status,
                reason,
                source_analysis_message_id,
                timestamp,
            )
        belief = self.get(belief_id)
        assert belief is not None
        return belief

    def _insert_version(
        self,
        belief_id: str,
        version: int,
        proposition: str,
        user_confidence: float | None,
        status: str,
        reason: str | None,
        source_analysis_message_id: str | None,
        timestamp: str,
    ) -> None:
        self.connection.execute(
            """INSERT INTO belief_versions
               (id, belief_id, version, proposition, user_confidence, status, change_reason,
                source_analysis_message_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()), belief_id, version, proposition, user_confidence, status, reason,
                source_analysis_message_id, timestamp,
            ),
        )

    def _insert_falsification_condition(self, belief_id: str, condition: str, timestamp: str) -> None:
        self.connection.execute(
            """INSERT INTO belief_falsification_conditions (id, belief_id, condition, created_at)
               VALUES (?, ?, ?, ?)""",
            (str(uuid.uuid4()), belief_id, condition, timestamp),
        )
