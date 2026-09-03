import os
import tempfile
import unittest
from pathlib import Path

import httpx

from app.db import initialize_database
from app.main import app


class HealthRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_health_reports_database_ready(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get("XOD_DATABASE_PATH")
            os.environ["XOD_DATABASE_PATH"] = str(Path(directory) / "health.db")
            try:
                initialize_database()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://xod.test") as client:
                    response = await client.get("/api/health")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"status": "ok", "database": "ready"})
            finally:
                if previous is None:
                    os.environ.pop("XOD_DATABASE_PATH", None)
                else:
                    os.environ["XOD_DATABASE_PATH"] = previous
