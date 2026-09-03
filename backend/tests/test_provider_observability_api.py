import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

import httpx

from app.main import create_app
from app.schemas import TribunalAnalysis
from app.services.ai_provider import AIProvider
from app.services.provider_failures import ProviderFailure, ProviderFailureCategory


class FailingProvider(AIProvider):
    async def reply(self, messages: list[dict[str, str]]) -> str:
        raise ProviderFailure(
            ProviderFailureCategory.RATE_LIMIT,
            "SPAR",
            provider="test-provider",
            model="test-model",
            latency_ms=12,
        )

    async def analyze_tribunal(
        self, messages: list[dict[str, str]], user_confidence: float | None
    ) -> TribunalAnalysis:
        raise ProviderFailure(
            ProviderFailureCategory.MALFORMED_RESPONSE,
            "TRIBUNAL",
            provider="test-provider",
            model="test-model",
            latency_ms=18,
        )


class ProviderObservabilityApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_translates_failures_and_persists_content_free_reliability_events(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "observability.db"
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(database)
            try:
                app = create_app(lambda: FailingProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        conversation = await client.post("/api/conversations", json={})
                        conversation_id = conversation.json()["id"]
                        with self.assertLogs("xod.provider", level="ERROR") as logs:
                            spar = await client.post(
                                f"/api/conversations/{conversation_id}/messages",
                                json={"content": "Private proposition text must not be logged."},
                            )
                        tribunal = await client.post(
                            f"/api/conversations/{conversation_id}/tribunal",
                            json={"content": "Another private proposition.", "user_confidence": 0.5},
                        )

                self.assertEqual(spar.status_code, 429)
                detail = spar.json()["detail"]
                self.assertEqual(detail["category"], "RATE_LIMIT")
                self.assertTrue(detail["retryable"])
                self.assertTrue(detail["error_id"].startswith("XOD-"))
                self.assertNotIn("Private proposition", "\n".join(logs.output))
                self.assertEqual(tribunal.status_code, 502)
                self.assertFalse(tribunal.json()["detail"]["retryable"])

                connection = sqlite3.connect(database)
                try:
                    events = connection.execute(
                        "SELECT category, operation, provider, model, retryable, latency_ms FROM provider_failure_events ORDER BY occurred_at"
                    ).fetchall()
                    columns = {row[1] for row in connection.execute("PRAGMA table_info(provider_failure_events)")}
                finally:
                    connection.close()
                self.assertEqual(
                    events,
                    [
                        ("RATE_LIMIT", "SPAR", "test-provider", "test-model", 1, 12),
                        ("MALFORMED_RESPONSE", "TRIBUNAL", "test-provider", "test-model", 0, 18),
                    ],
                )
                self.assertNotIn("conversation_id", columns)
                self.assertNotIn("content", columns)
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous
