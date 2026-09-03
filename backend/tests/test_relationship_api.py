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


class RelationshipApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_creates_lists_and_traverses_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "relationships.db")
            try:
                app = create_app(lambda: FakeProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        ids = []
                        for proposition in ["A paid pilot predicts demand.", "The pilot audience matches buyers.", "Interview intent maps to purchases."]:
                            created = await client.post("/api/beliefs", json={"proposition": proposition})
                            self.assertEqual(created.status_code, 201)
                            ids.append(created.json()["id"])
                        first = await client.post(
                            f"/api/beliefs/{ids[0]}/relationships",
                            json={"target_belief_id": ids[1], "relationship_type": "DEPENDS_ON", "note": "Audience fit is load-bearing."},
                        )
                        self.assertEqual(first.status_code, 201)
                        self.assertEqual(first.json()["relationship_type"], "DEPENDS_ON")
                        second = await client.post(
                            f"/api/beliefs/{ids[1]}/relationships",
                            json={"target_belief_id": ids[2], "relationship_type": "DEPENDS_ON"},
                        )
                        self.assertEqual(second.status_code, 201)
                        relationships = await client.get(f"/api/beliefs/{ids[0]}/relationships")
                        self.assertEqual(len(relationships.json()["outgoing"]), 1)
                        neighborhood = await client.get(
                            f"/api/beliefs/{ids[0]}/relationship-neighborhood", params={"depth": 2}
                        )
                        self.assertEqual(len(neighborhood.json()["nodes"]), 3)
                        self.assertEqual(len(neighborhood.json()["edges"]), 2)
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous

    async def test_rejects_self_and_duplicate_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "relationships.db")
            try:
                app = create_app(lambda: FakeProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        first = await client.post("/api/beliefs", json={"proposition": "First belief."})
                        second = await client.post("/api/beliefs", json={"proposition": "Second belief."})
                        first_id, second_id = first.json()["id"], second.json()["id"]
                        self_relation = await client.post(
                            f"/api/beliefs/{first_id}/relationships",
                            json={"target_belief_id": first_id, "relationship_type": "SUPPORTS"},
                        )
                        self.assertEqual(self_relation.status_code, 422)
                        payload = {"target_belief_id": second_id, "relationship_type": "SUPPORTS"}
                        self.assertEqual((await client.post(f"/api/beliefs/{first_id}/relationships", json=payload)).status_code, 201)
                        self.assertEqual((await client.post(f"/api/beliefs/{first_id}/relationships", json=payload)).status_code, 409)
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous
