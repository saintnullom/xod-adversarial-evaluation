import tempfile
import unittest
from pathlib import Path

from app.db import connect, initialize_database
from app.repositories.conversations import ConversationRepository
from app.schemas import TribunalAnalysis
from app.services.ai_provider import AIProvider
from app.services.provider_failures import ProviderFailure, ProviderFailureCategory
from app.services.conversation_service import ConversationService


class FakeProvider(AIProvider):
    async def reply(self, messages: list[dict[str, str]]) -> str:
        self.messages = messages
        return "PROPOSITION: Test it.\nSTRONGEST ASSUMPTION: The sample is representative.\nSTRONGEST OBJECTION: It may be selection bias.\nALTERNATIVE: Novelty drove interest.\nCHEAPEST TEST: Precommit a repeatable metric."


class FailingProvider(AIProvider):
    async def reply(self, messages: list[dict[str, str]]) -> str:
        raise ProviderFailure(
            ProviderFailureCategory.NETWORK,
            "SPAR",
            provider="test-provider",
            model="test-model",
            latency_ms=1,
        )


def tribunal_fixture() -> TribunalAnalysis:
    return TribunalAnalysis.model_validate(
        {
            "proposition": "A small pilot will predict demand.",
            "user_confidence": 0.8,
            "assumptions": ["Early testers represent the target segment."],
            "evidence_for": [{"claim": "Three testers were enthusiastic.", "kind": "OBSERVATION", "source": None, "url": None}],
            "evidence_against": [{"claim": "No purchase commitment was recorded.", "kind": "OBSERVATION", "source": None, "url": None}],
            "strongest_objection": "Verbal enthusiasm may not predict payment.",
            "alternative_explanations": ["Novelty explains the response."],
            "bias_risks": ["Selection bias from friendly testers."],
            "falsification_conditions": ["A preregistered paid test fails its threshold."],
            "cheapest_experiment": "Ask ten target users for a refundable deposit.",
            "steelman": "The problem may be painful enough to motivate early adopters.",
            "verdict": "UNDERTESTED",
            "recommended_confidence": {"minimum": 0.35, "maximum": 0.6},
            "xod_self_critique": "The target segment is not yet defined.",
        }
    )


class TribunalProvider(FakeProvider):
    async def analyze_tribunal(self, messages: list[dict[str, str]], user_confidence: float | None) -> TribunalAnalysis:
        self.tribunal_messages = messages
        return tribunal_fixture().model_copy(update={"user_confidence": user_confidence})


class ConversationServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_persists_user_and_xod_turn_with_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "xod.db"
            initialize_database(path)
            connection = connect(path)
            try:
                repository = ConversationRepository(connection)
                conversation = repository.create("Demand hypothesis")
                provider = FakeProvider()
                result = await ConversationService(repository, provider).add_user_turn(
                    str(conversation["id"]), "Three friends said they would buy it."
                )
            finally:
                connection.close()
        self.assertEqual([message["role"] for message in result["messages"]], ["USER", "XOD"])
        self.assertEqual(provider.messages[0]["content"], "Three friends said they would buy it.")
        self.assertIn("STRONGEST ASSUMPTION", result["messages"][1]["content"])

    async def test_does_not_create_an_orphan_user_message_when_provider_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "xod.db"
            initialize_database(path)
            connection = connect(path)
            try:
                repository = ConversationRepository(connection)
                conversation = repository.create("Failure behavior")
                with self.assertRaises(ProviderFailure):
                    await ConversationService(repository, FailingProvider()).add_user_turn(
                        str(conversation["id"]), "A proposition that should remain in the draft."
                    )
                reloaded = repository.get(str(conversation["id"]))
            finally:
                connection.close()
        self.assertEqual(reloaded["messages"], [])

    async def test_persists_validated_tribunal_with_the_xod_message(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "xod.db"
            initialize_database(path)
            connection = connect(path)
            try:
                repository = ConversationRepository(connection)
                conversation = repository.create("Pilot claim")
                provider = TribunalProvider()
                result = await ConversationService(repository, provider).add_tribunal_turn(
                    str(conversation["id"]), "A small pilot will predict demand.", 0.8
                )
            finally:
                connection.close()
        xod_message = result["messages"][-1]
        self.assertEqual(xod_message["role"], "XOD")
        self.assertEqual(xod_message["analysis"]["verdict"], "UNDERTESTED")
        self.assertEqual(xod_message["analysis"]["user_confidence"], 0.8)
