import os
import tempfile
import unittest
from pathlib import Path

import httpx

from app.main import create_app
from app.services.ai_provider import AIProvider
from app.services.analytics import calculate_analytics


class FakeProvider(AIProvider):
    async def reply(self, messages: list[dict[str, str]]) -> str:
        return "SPAR"


class AnalyticsTests(unittest.IsolatedAsyncioTestCase):
    async def test_calculates_delta_and_directional_calibration(self) -> None:
        report = calculate_analytics(
            [
                {"belief_id": "b1", "proposition": "A", "current_version": 2, "status": "REVISED", "initial_confidence": 0.8, "current_confidence": 0.5, "revised_at": "now"},
                {"belief_id": "b2", "proposition": "B", "current_version": 1, "status": "ACTIVE_TEST", "initial_confidence": 0.4, "current_confidence": 0.4, "revised_at": "now"},
            ],
            [
                {"id": "p1", "status": "RESOLVED", "impact": "SUPPORTS", "belief_confidence_at_commit": 0.8},
                {"id": "p2", "status": "RESOLVED", "impact": "WEAKENS", "belief_confidence_at_commit": 0.2},
                {"id": "p3", "status": "RESOLVED", "impact": "SUPPORTS", "belief_confidence_at_commit": 0.6},
                {"id": "p4", "status": "RESOLVED", "impact": "WEAKENS", "belief_confidence_at_commit": 0.3},
                {"id": "p5", "status": "RESOLVED", "impact": "SUPPORTS", "belief_confidence_at_commit": 0.7},
                {"id": "p6", "status": "RESOLVED", "impact": "INCONCLUSIVE", "belief_confidence_at_commit": 0.5},
            ],
        )
        self.assertEqual(report["epistemic_delta"]["availability"], "AVAILABLE")
        self.assertAlmostEqual(report["epistemic_delta"]["mean_delta"], -0.15)
        self.assertEqual(report["calibration"]["availability"], "AVAILABLE")
        self.assertEqual(report["calibration"]["scorable_prediction_count"], 5)
        self.assertAlmostEqual(report["calibration"]["mean_absolute_error"], 0.28)

    async def test_api_reports_insufficient_data_without_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "analytics.db")
            try:
                app = create_app(lambda: FakeProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        response = await client.get("/api/analytics")
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.json()["epistemic_delta"]["availability"], "INSUFFICIENT_DATA")
                        self.assertEqual(response.json()["calibration"]["availability"], "INSUFFICIENT_DATA")
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous

    async def test_api_uses_immutable_prediction_confidence_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "analytics.db")
            try:
                app = create_app(lambda: FakeProvider())
                async with app.router.lifespan_context(app):
                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                        belief = await client.post(
                            "/api/beliefs", json={"proposition": "A paid pilot predicts demand.", "user_confidence": 0.8}
                        )
                        belief_id = belief.json()["id"]
                        await client.patch(
                            f"/api/beliefs/{belief_id}",
                            json={"user_confidence": 0.5, "status": "REVISED", "change_reason": "The segment narrowed."},
                        )
                        for index in range(5):
                            prediction = await client.post(
                                f"/api/beliefs/{belief_id}/predictions",
                                json={"statement": f"Prediction {index}", "success_criteria": "Observe a measured outcome."},
                            )
                            self.assertEqual(prediction.json()["belief_confidence_at_commit"], 0.5)
                            await client.patch(
                                f"/api/predictions/{prediction.json()['id']}/resolve",
                                json={"result": "Observed.", "impact": "SUPPORTS" if index % 2 == 0 else "WEAKENS"},
                            )
                        report = await client.get("/api/analytics")
                        self.assertEqual(report.status_code, 200)
                        self.assertAlmostEqual(report.json()["epistemic_delta"]["mean_delta"], -0.3)
                        self.assertEqual(report.json()["calibration"]["availability"], "AVAILABLE")
                        self.assertEqual(report.json()["calibration"]["scorable_prediction_count"], 5)
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous
