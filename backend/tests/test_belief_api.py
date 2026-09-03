import os
import tempfile
import unittest
from pathlib import Path

import httpx

from app.main import create_app
from app.services.ai_provider import AIProvider


class FakeProvider(AIProvider):
    async def reply(self, messages: list[dict[str, str]]) -> str:
        return "SPAR"


class BeliefApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_creates_revises_and_reopens_a_belief(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "beliefs.db")
            try:
                app = create_app(lambda: FakeProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        created = await client.post(
                            "/api/beliefs",
                            json={
                                "proposition": "A paid pilot will predict demand.",
                                "user_confidence": 0.7,
                                "source_analysis_message_id": "analysis-message-1",
                            },
                        )
                        self.assertEqual(created.status_code, 201)
                        belief_id = created.json()["id"]
                        self.assertEqual(created.json()["versions"][0]["source_analysis_message_id"], "analysis-message-1")
                        revised = await client.patch(
                            f"/api/beliefs/{belief_id}",
                            json={
                                "proposition": "A paid pilot will predict demand for one segment.",
                                "user_confidence": 0.55,
                                "status": "REVISED",
                                "change_reason": "The segment was narrowed.",
                            },
                        )
                        self.assertEqual(revised.status_code, 200)
                        self.assertEqual(revised.json()["current_version"], 2)
                        self.assertEqual(len(revised.json()["versions"]), 2)
                        listed = await client.get("/api/beliefs")
                        self.assertEqual(listed.status_code, 200)
                        self.assertEqual(listed.json()[0]["status"], "REVISED")
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous

    async def test_rejects_out_of_range_confidence(self) -> None:
        app = create_app(lambda: FakeProvider())
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
            response = await client.post("/api/beliefs", json={"proposition": "A claim.", "user_confidence": 1.2})
        self.assertEqual(response.status_code, 422)
