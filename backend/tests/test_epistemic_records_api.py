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


class EpistemicRecordsApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_records_evidence_prediction_resolution_and_falsification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "records.db")
            try:
                app = create_app(lambda: FakeProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        belief = await client.post(
                            "/api/beliefs",
                            json={
                                "proposition": "A paid pilot will predict demand.",
                                "falsification_conditions": ["Fewer than five qualified signups arrive in 30 days."],
                            },
                        )
                        self.assertEqual(belief.status_code, 201)
                        belief_id = belief.json()["id"]
                        self.assertEqual(len(belief.json()["falsification_conditions"]), 1)

                        evidence = await client.post(
                            f"/api/beliefs/{belief_id}/evidence",
                            json={
                                "claim": "Seven qualified prospects accepted an interview.",
                                "source": "Pilot contact log",
                                "source_type": "FIRST_PARTY_OBSERVATION",
                                "direction": "SUPPORTS",
                                "reliability": 0.8,
                                "relevance": 0.9,
                            },
                        )
                        self.assertEqual(evidence.status_code, 201)
                        self.assertEqual(evidence.json()["direction"], "SUPPORTS")

                        prediction = await client.post(
                            f"/api/beliefs/{belief_id}/predictions",
                            json={
                                "statement": "Ten qualified users will join the pilot in 30 days.",
                                "success_criteria": "At least ten verified signup records exist by the deadline.",
                            },
                        )
                        self.assertEqual(prediction.status_code, 201)
                        resolved = await client.patch(
                            f"/api/predictions/{prediction.json()['id']}/resolve",
                            json={"result": "Only three qualified users joined.", "impact": "WEAKENS"},
                        )
                        self.assertEqual(resolved.status_code, 200)
                        self.assertEqual(resolved.json()["status"], "RESOLVED")
                        self.assertEqual(resolved.json()["impact"], "WEAKENS")

                        detail = await client.get(f"/api/beliefs/{belief_id}")
                        self.assertEqual(len(detail.json()["evidence"]), 1)
                        self.assertEqual(detail.json()["predictions"][0]["result"], "Only three qualified users joined.")
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous

    async def test_rejects_invalid_evidence_and_double_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "records.db")
            try:
                app = create_app(lambda: FakeProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        belief = await client.post("/api/beliefs", json={"proposition": "A claim."})
                        belief_id = belief.json()["id"]
                        invalid = await client.post(
                            f"/api/beliefs/{belief_id}/evidence",
                            json={"claim": "A note.", "source": "Notebook", "direction": "SUPPORTS", "reliability": 1.1},
                        )
                        self.assertEqual(invalid.status_code, 422)
                        prediction = await client.post(
                            f"/api/beliefs/{belief_id}/predictions",
                            json={"statement": "A result happens.", "success_criteria": "Measure it."},
                        )
                        first = await client.patch(
                            f"/api/predictions/{prediction.json()['id']}/resolve",
                            json={"result": "Measured.", "impact": "INCONCLUSIVE"},
                        )
                        self.assertEqual(first.status_code, 200)
                        repeated = await client.patch(
                            f"/api/predictions/{prediction.json()['id']}/resolve",
                            json={"result": "Changed later.", "impact": "SUPPORTS"},
                        )
                        self.assertEqual(repeated.status_code, 409)
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous
