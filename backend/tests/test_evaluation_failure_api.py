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


class EvaluationFailureApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_exposes_complete_evaluation_suite_and_persists_voluntary_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "evaluation.db")
            try:
                app = create_app(lambda: FakeProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        cases = await client.get("/api/evaluation-suite/cases")
                        self.assertEqual(cases.status_code, 200)
                        self.assertEqual(len(cases.json()), 9)
                        self.assertIn("Creative strategy", {case["domain"] for case in cases.json()})
                        report = await client.post(
                            "/api/failure-reports",
                            json={
                                "category": "IGNORED_CONTEXT",
                                "summary": "The analysis ignored the stated budget constraint.",
                                "expected_behavior": "Treat the budget as a binding constraint.",
                                "evaluation_case_id": "planning-repeatability",
                            },
                        )
                        self.assertEqual(report.status_code, 201)
                        listed = await client.get("/api/failure-reports")
                        self.assertEqual(len(listed.json()), 1)
                        self.assertEqual(listed.json()[0]["category"], "IGNORED_CONTEXT")
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous

    async def test_rejects_unknown_evaluation_case(self) -> None:
        app = create_app(lambda: FakeProvider())
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
            response = await client.post(
                "/api/failure-reports",
                json={"category": "OTHER", "summary": "A problem.", "evaluation_case_id": "not-a-case"},
            )
        self.assertEqual(response.status_code, 422)
