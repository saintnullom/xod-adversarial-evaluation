import os
import tempfile
import unittest
from pathlib import Path

import httpx

from app.main import create_app
from app.services.ai_provider import AIProvider
from app.services.specialist_evaluation import EVALUATION_CASES, readiness


def measurement(case_id: str, specialist_quality: float = 2.5) -> dict[str, object]:
    return {
        "case_id": case_id,
        "baseline_quality": 2.0,
        "specialist_quality": specialist_quality,
        "baseline_cost_usd": 0.02,
        "specialist_cost_usd": 0.03,
        "baseline_latency_ms": 500,
        "specialist_latency_ms": 900,
    }


class FakeProvider(AIProvider):
    async def reply(self, messages: list[dict[str, str]]) -> str:
        return "SPAR"


class SpecialistEvaluationTests(unittest.IsolatedAsyncioTestCase):
    async def test_requires_paired_coverage_before_a_pilot(self) -> None:
        report = readiness([measurement(EVALUATION_CASES[0]["id"])])
        self.assertEqual(report["decision"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(report["measured_case_count"], 1)
        self.assertEqual(len(report["missing_case_ids"]), 7)

    async def test_eligible_only_when_quality_improves_without_regression(self) -> None:
        report = readiness([measurement(case["id"]) for case in EVALUATION_CASES])
        self.assertEqual(report["decision"], "ELIGIBLE_FOR_PILOT")
        regressed = readiness([
            measurement(case["id"], 1.8 if case["id"] == "self-sealing" else 2.5)
            for case in EVALUATION_CASES
        ])
        self.assertEqual(regressed["decision"], "HOLD")
        self.assertEqual(regressed["regressed_case_ids"], ["self-sealing"])

    async def test_api_records_a_measurement_and_reports_insufficient_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "specialist.db")
            try:
                app = create_app(lambda: FakeProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        cases = await client.get("/api/specialist-readiness/cases")
                        self.assertEqual(cases.status_code, 200)
                        created = await client.post(
                            "/api/specialist-readiness/measurements",
                            json=measurement(cases.json()[0]["id"]),
                        )
                        self.assertEqual(created.status_code, 201)
                        readiness_response = await client.get("/api/specialist-readiness")
                        self.assertEqual(readiness_response.status_code, 200)
                        self.assertEqual(readiness_response.json()["decision"], "INSUFFICIENT_EVIDENCE")
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous
