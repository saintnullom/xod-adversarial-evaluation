"""Evidence, prediction, and falsification records independent of AI output."""

from __future__ import annotations

import sqlite3
import uuid

from app.repositories.beliefs import utc_now


class EpistemicRecordRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_evidence(
        self,
        belief_id: str,
        claim: str,
        source: str,
        source_type: str,
        direction: str,
        url: str | None = None,
        retrieved_at: str | None = None,
        reliability: float | None = None,
        relevance: float | None = None,
    ) -> dict[str, object]:
        record = {
            "id": str(uuid.uuid4()), "belief_id": belief_id, "claim": claim, "source": source,
            "source_type": source_type, "url": url, "retrieved_at": retrieved_at,
            "reliability": reliability, "relevance": relevance, "direction": direction, "created_at": utc_now(),
        }
        with self.connection:
            self.connection.execute(
                """INSERT INTO evidence
                   (id, belief_id, claim, source, source_type, url, retrieved_at, reliability, relevance, direction, created_at)
                   VALUES (:id, :belief_id, :claim, :source, :source_type, :url, :retrieved_at, :reliability, :relevance, :direction, :created_at)""",
                record,
            )
        return record

    def create_prediction(
        self, belief_id: str, statement: str, success_criteria: str, expected_resolution_at: str | None = None
    ) -> dict[str, object]:
        belief = self.connection.execute(
            "SELECT user_confidence FROM beliefs WHERE id = ?", (belief_id,)
        ).fetchone()
        if belief is None:
            raise KeyError(f"Unknown belief: {belief_id}")
        record = {
            "id": str(uuid.uuid4()), "belief_id": belief_id, "statement": statement,
            "success_criteria": success_criteria, "created_at": utc_now(),
            "belief_confidence_at_commit": belief["user_confidence"],
            "expected_resolution_at": expected_resolution_at, "result": None, "status": "OPEN",
            "impact": None, "resolved_at": None,
        }
        with self.connection:
            self.connection.execute(
                """INSERT INTO predictions
                   (id, belief_id, statement, success_criteria, created_at, belief_confidence_at_commit, expected_resolution_at, result, status, impact, resolved_at)
                   VALUES (:id, :belief_id, :statement, :success_criteria, :created_at, :belief_confidence_at_commit, :expected_resolution_at, :result, :status, :impact, :resolved_at)""",
                record,
            )
        return record

    def resolve_prediction(self, prediction_id: str, result: str, impact: str) -> dict[str, object]:
        prediction = self.connection.execute(
            "SELECT status FROM predictions WHERE id = ?", (prediction_id,)
        ).fetchone()
        if prediction is None:
            raise KeyError(f"Unknown prediction: {prediction_id}")
        if prediction["status"] != "OPEN":
            raise ValueError("Only open predictions can be resolved.")
        resolved_at = utc_now()
        with self.connection:
            self.connection.execute(
                """UPDATE predictions SET result = ?, impact = ?, status = 'RESOLVED', resolved_at = ?
                   WHERE id = ?""",
                (result, impact, resolved_at, prediction_id),
            )
        row = self.connection.execute(
            """SELECT id, belief_id, statement, success_criteria, created_at, belief_confidence_at_commit, expected_resolution_at, result,
                      status, impact, resolved_at FROM predictions WHERE id = ?""",
            (prediction_id,),
        ).fetchone()
        assert row is not None
        return dict(row)

    def create_falsification_condition(self, belief_id: str, condition: str) -> dict[str, object]:
        record = {"id": str(uuid.uuid4()), "belief_id": belief_id, "condition": condition, "created_at": utc_now()}
        with self.connection:
            self.connection.execute(
                """INSERT INTO belief_falsification_conditions (id, belief_id, condition, created_at)
                   VALUES (:id, :belief_id, :condition, :created_at)""",
                record,
            )
        return record
