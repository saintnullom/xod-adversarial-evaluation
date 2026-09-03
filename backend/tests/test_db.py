import tempfile
import unittest
from pathlib import Path

from app.db import connect, initialize_database
from app.repositories.beliefs import BeliefRepository


class DatabaseTests(unittest.TestCase):
    def test_initialization_creates_core_tables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "xod.db"
            initialize_database(path)
            connection = connect(path)
            try:
                tables = {
                    row["name"]
                    for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
                }
            finally:
                connection.close()
        self.assertTrue({"conversations", "messages", "beliefs", "belief_versions", "evidence", "predictions", "objections", "belief_falsification_conditions", "self_critique_evaluations", "specialist_evaluation_measurements", "belief_relationships", "failure_reports"}.issubset(tables))

    def test_belief_revision_preserves_version_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "xod.db"
            initialize_database(path)
            connection = connect(path)
            try:
                repository = BeliefRepository(connection)
                belief = repository.create("A small test will predict demand.", 0.65)
                revised = repository.revise(
                    str(belief["id"]),
                    "A precommitted small test will predict demand in one segment.",
                    0.55,
                    "REVISED",
                    "Narrowed the population after review.",
                )
            finally:
                connection.close()
        self.assertEqual(revised["current_version"], 2)
        self.assertEqual([version["version"] for version in reversed(revised["versions"])], [1, 2])
        self.assertEqual(revised["versions"][-1]["proposition"], "A small test will predict demand.")
        self.assertEqual(revised["status"], "REVISED")
