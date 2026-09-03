import os
import tempfile
import unittest
from pathlib import Path

import httpx

from app.main import create_app
from app.schemas import TribunalAnalysis
from app.services.ai_provider import AIProvider


class FakeProvider(AIProvider):
    async def reply(self, messages: list[dict[str, str]]) -> str:
        return "PROPOSITION: A limited proposition.\nSTRONGEST ASSUMPTION: The signal generalizes.\nSTRONGEST OBJECTION: The evidence is anecdotal.\nALTERNATIVE: Politeness explains the response.\nCHEAPEST TEST: Ask for a precommitted purchase."

    async def analyze_tribunal(self, messages: list[dict[str, str]], user_confidence: float | None) -> TribunalAnalysis:
        return TribunalAnalysis.model_validate(
            {
                "proposition": messages[-1]["content"],
                "user_confidence": user_confidence,
                "assumptions": ["The sample represents the market."],
                "evidence_for": [],
                "evidence_against": [],
                "strongest_objection": "The claim is not yet tested.",
                "alternative_explanations": ["Novelty could explain interest."],
                "bias_risks": ["Confirmation bias."],
                "falsification_conditions": ["A paid test fails."],
                "cheapest_experiment": "Run a paid test.",
                "steelman": "The problem is plausibly real.",
                "verdict": "UNDERTESTED",
                "recommended_confidence": {"minimum": 0.3, "maximum": 0.6},
                "xod_self_critique": "The target segment is incomplete.",
            }
        )


class ConversationApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_creates_and_retrieves_persisted_conversation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "api.db")
            try:
                app = create_app(lambda: FakeProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        created = await client.post("/api/conversations", json={"title": "Purchase claim"})
                        self.assertEqual(created.status_code, 201)
                        conversation_id = created.json()["id"]
                        turn = await client.post(
                            f"/api/conversations/{conversation_id}/messages",
                            json={"content": "Three people promised to purchase."},
                        )
                        self.assertEqual(turn.status_code, 200)
                        self.assertEqual([message["role"] for message in turn.json()["messages"]], ["USER", "XOD"])
                        loaded = await client.get(f"/api/conversations/{conversation_id}")
                        self.assertEqual(loaded.status_code, 200)
                        self.assertEqual(len(loaded.json()["messages"]), 2)
                        tribunal = await client.post(
                            f"/api/conversations/{conversation_id}/tribunal",
                            json={"content": "A paid pilot will predict demand.", "user_confidence": 0.75},
                        )
                        self.assertEqual(tribunal.status_code, 200)
                        self.assertEqual(tribunal.json()["messages"][-1]["analysis"]["verdict"], "UNDERTESTED")
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous
