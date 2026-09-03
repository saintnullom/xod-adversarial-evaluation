"""Local reliability events without conversation content."""

from __future__ import annotations

import sqlite3


class ProviderFailureEventRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, event: dict[str, object]) -> None:
        with self.connection:
            self.connection.execute(
                """INSERT INTO provider_failure_events
                   (error_id, category, operation, provider, model, retryable, latency_ms, occurred_at)
                   VALUES (:error_id, :category, :operation, :provider, :model, :retryable, :latency_ms, :occurred_at)""",
                {**event, "retryable": int(bool(event["retryable"]))},
            )
