import unittest

from pydantic import ValidationError

from app.schemas import ConfidenceRange, TribunalAnalysis


class TribunalSchemaTests(unittest.TestCase):
    def test_rejects_reversed_confidence_range(self) -> None:
        with self.assertRaises(ValidationError):
            ConfidenceRange(minimum=0.8, maximum=0.4)

    def test_rejects_malformed_tribunal_output(self) -> None:
        with self.assertRaises(ValidationError):
            TribunalAnalysis.model_validate(
                {
                    "proposition": "It will work.",
                    "strongest_objection": "Demand is untested.",
                    "cheapest_experiment": "Run a paid test.",
                    "steelman": "The target group has a real problem.",
                    "verdict": "DEFINITELY_TRUE",
                    "recommended_confidence": {"minimum": 0.3, "maximum": 0.7},
                    "xod_self_critique": "The target segment may be poorly specified.",
                }
            )

