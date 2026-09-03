import unittest

from app.schemas import TribunalAnalysis
from app.services.ai_provider import OpenAIProvider
from app.services.provider_failures import (
    ProviderFailure,
    ProviderFailureCategory,
    classify_provider_exception,
)


class FakeResponses:
    def __init__(self, parsed: TribunalAnalysis | None) -> None:
        self.parsed = parsed
        self.kwargs: dict[str, object] | None = None

    async def parse(self, **kwargs: object) -> object:
        self.kwargs = kwargs
        return type("Response", (), {"output_parsed": self.parsed})()


class FakeClient:
    def __init__(self, parsed: TribunalAnalysis | None) -> None:
        self.responses = FakeResponses(parsed)


def valid_analysis() -> TribunalAnalysis:
    return TribunalAnalysis.model_validate(
        {
            "proposition": "A pilot predicts demand.",
            "user_confidence": None,
            "assumptions": [],
            "evidence_for": [],
            "evidence_against": [],
            "strongest_objection": "The pilot could be unrepresentative.",
            "alternative_explanations": [],
            "bias_risks": [],
            "falsification_conditions": ["The paid test misses its threshold."],
            "cheapest_experiment": "Run a paid test.",
            "steelman": "The problem may be urgent.",
            "verdict": "UNDERTESTED",
            "recommended_confidence": {"minimum": 0.3, "maximum": 0.6},
            "xod_self_critique": "The target segment is unspecified.",
        }
    )


class OpenAIProviderTests(unittest.IsolatedAsyncioTestCase):
    def provider_with(self, parsed: TribunalAnalysis | None) -> OpenAIProvider:
        provider = OpenAIProvider.__new__(OpenAIProvider)
        provider.client = FakeClient(parsed)
        provider.model = "test-model"
        return provider

    async def test_rejects_absent_structured_output(self) -> None:
        with self.assertRaises(ProviderFailure) as captured:
            await self.provider_with(None).analyze_tribunal(
                [{"role": "USER", "content": "A claim."}], 0.6
            )
        self.assertEqual(captured.exception.category, ProviderFailureCategory.MALFORMED_RESPONSE)

    def test_classifies_timeout_without_exposing_provider_details(self) -> None:
        self.assertEqual(
            classify_provider_exception(TimeoutError("upstream diagnostic text")),
            ProviderFailureCategory.TIMEOUT,
        )

    async def test_uses_pydantic_format_and_preserves_user_confidence(self) -> None:
        provider = self.provider_with(valid_analysis())
        result = await provider.analyze_tribunal([{"role": "USER", "content": "A claim."}], 0.6)
        self.assertEqual(result.user_confidence, 0.6)
        self.assertIs(provider.client.responses.kwargs["text_format"], TribunalAnalysis)
        self.assertFalse(provider.client.responses.kwargs["store"])
