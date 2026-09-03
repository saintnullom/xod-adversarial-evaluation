import os
import tempfile
import unittest
from pathlib import Path

import httpx

from app.main import create_app
from app.schemas import TribunalAnalysis
from app.services.ai_provider import AIProvider
from app.services.self_critique_evaluator import evaluate_self_critique


def analysis_with(critique: str) -> TribunalAnalysis:
    return TribunalAnalysis.model_validate(
        {
            "proposition": "A paid pilot predicts demand for one segment.",
            "user_confidence": 0.7,
            "assumptions": [],
            "evidence_for": [],
            "evidence_against": [],
            "strongest_objection": "The pilot could be unrepresentative.",
            "alternative_explanations": [],
            "bias_risks": [],
            "falsification_conditions": ["The paid test misses the threshold."],
            "cheapest_experiment": "Run the paid test.",
            "steelman": "The target problem may be urgent.",
            "verdict": "UNDERTESTED",
            "recommended_confidence": {"minimum": 0.3, "maximum": 0.6},
            "xod_self_critique": critique,
        }
    )


class FakeTribunalProvider(AIProvider):
    async def reply(self, messages: list[dict[str, str]]) -> str:
        return "SPAR"

    async def analyze_tribunal(
        self, messages: list[dict[str, str]], user_confidence: float | None
    ) -> TribunalAnalysis:
        return analysis_with(
            "XOD lacks context about the target segment and measurement design; domain data could weaken this "
            "criticism if it shows the pilot sample matches the intended buyers."
        ).model_copy(update={"user_confidence": user_confidence})


class SelfCritiqueEvaluatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_api_persists_a_useful_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "evaluation.db")
            try:
                app = create_app(lambda: FakeTribunalProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        conversation = await client.post("/api/conversations", json={})
                        tribunal = await client.post(
                            f"/api/conversations/{conversation.json()['id']}/tribunal",
                            json={"content": "A paid pilot predicts demand.", "user_confidence": 0.7},
                        )
                        message_id = next(
                            message["id"] for message in tribunal.json()["messages"] if message["role"] == "XOD"
                        )
                        evaluation = await client.post(
                            f"/api/analyses/{message_id}/self-critique-evaluation"
                        )
                        self.assertEqual(evaluation.status_code, 200)
                        self.assertEqual(evaluation.json()["verdict"], "USEFUL")
                        self.assertEqual(evaluation.json()["score"], 4)
                        self.assertEqual(len(evaluation.json()["checks"]), 4)
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous

    async def test_rubric_flags_generic_self_critique(self) -> None:
        score, verdict, checks = evaluate_self_critique(analysis_with("I could be wrong."))
        self.assertLess(score, 3)
        self.assertEqual(verdict, "NEEDS_WORK")
        self.assertFalse(checks[0].passed)
