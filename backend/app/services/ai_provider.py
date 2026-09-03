"""Replaceable generation boundary for XOD's Phase 1 and 2 flows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
import os
from time import perf_counter

from app.schemas import TribunalAnalysis
from app.services.provider_failures import (
    ProviderFailure,
    ProviderFailureCategory,
    ProviderUnavailableError,
    malformed_response_failure,
    provider_failure_from_exception,
)


XOD_SYSTEM_INSTRUCTIONS = """You are XOD: Executive Objection Daemon.
Your job is not reflexive disagreement. Help the user prevent an idea from becoming immune to criticism.
In this Phase 1 SPAR conversation, respond concisely in this exact labeled order:
PROPOSITION: restate the claim narrowly.
STRONGEST ASSUMPTION: identify the most load-bearing untested premise.
STRONGEST OBJECTION: give the fairest serious counterargument.
ALTERNATIVE: name one plausible rival explanation.
CHEAPEST TEST: propose a low-cost measurable observation that could change confidence.

Separate observation from inference. Do not invent evidence or sources. Do not call a claim false merely because it is unconventional. If it survives the available criticism, say so with appropriate uncertainty. Do not use hidden chain-of-thought; give only concise conclusions and their stated rationale."""


TRIBUNAL_SYSTEM_INSTRUCTIONS = """You are XOD: Executive Objection Daemon.
Your purpose is not reflexive disagreement. Identify what would have to be true for the user to be wrong, while allowing claims that survive scrutiny to remain robust.
Return a complete TribunalAnalysis object. Every listed field must be present, even when an evidence list is empty. Treat user confidence as an input to preserve, not an assessment to invent.

Use concise, explicit claims. Label evidence as evidence, observation, inference, or speculation. Do not invent sources, citations, or measurements. Do not use lack of evidence as proof of absence without a detection argument. A self-sealing claim is one that treats both confirming and disconfirming outcomes as confirmation; flag it clearly when applicable.

Your self-critique must identify a meaningful limitation of your own reasoning, such as missing context, a generic framework, or domain expertise the user may hold. State what specific input, observation, or evidence could weaken XOD's criticism. Do not merely repeat the strongest objection. Do not reveal hidden chain-of-thought; return only the requested structured conclusions."""


class AIProvider(ABC):
    @abstractmethod
    async def reply(self, messages: Sequence[dict[str, str]]) -> str:
        """Return a user-safe reply for a persisted conversation context."""

    async def analyze_tribunal(
        self, messages: Sequence[dict[str, str]], user_confidence: float | None
    ) -> TribunalAnalysis:
        raise ProviderFailure(
            category=ProviderFailureCategory.UNSUPPORTED_FORMAT_OR_MODEL,
            operation="TRIBUNAL",
            provider="unknown",
            model=None,
            latency_ms=None,
        )


class UnavailableAIProvider(AIProvider):
    def __init__(self, model: str | None) -> None:
        self.model = model

    async def reply(self, messages: Sequence[dict[str, str]]) -> str:
        raise ProviderUnavailableError("SPAR", self.model)

    async def analyze_tribunal(
        self, messages: Sequence[dict[str, str]], user_confidence: float | None
    ) -> TribunalAnalysis:
        raise ProviderUnavailableError("TRIBUNAL", self.model)


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def reply(self, messages: Sequence[dict[str, str]]) -> str:
        started_at = perf_counter()
        try:
            response = await self.client.responses.create(
                model=self.model,
                instructions=XOD_SYSTEM_INSTRUCTIONS,
                input=self._input_messages(messages),
                store=False,
                max_output_tokens=650,
            )
        except Exception as error:
            raise provider_failure_from_exception(error, "SPAR", "openai", self.model, started_at) from error
        output = (response.output_text or "").strip()
        if not output:
            raise malformed_response_failure("SPAR", "openai", self.model, started_at)
        return output

    async def analyze_tribunal(
        self, messages: Sequence[dict[str, str]], user_confidence: float | None
    ) -> TribunalAnalysis:
        started_at = perf_counter()
        try:
            response = await self.client.responses.parse(
                model=self.model,
                instructions=TRIBUNAL_SYSTEM_INSTRUCTIONS,
                input=self._input_messages(messages),
                text_format=TribunalAnalysis,
                store=False,
                max_output_tokens=1800,
            )
        except Exception as error:
            raise provider_failure_from_exception(error, "TRIBUNAL", "openai", self.model, started_at) from error
        analysis = response.output_parsed
        if analysis is None:
            raise malformed_response_failure("TRIBUNAL", "openai", self.model, started_at)
        try:
            validated = TribunalAnalysis.model_validate(analysis)
        except Exception as error:
            raise provider_failure_from_exception(error, "TRIBUNAL", "openai", self.model, started_at) from error
        return validated.model_copy(update={"user_confidence": user_confidence})

    @staticmethod
    def _input_messages(messages: Sequence[dict[str, str]]) -> list[dict[str, str]]:
        return [
            {
                "role": "assistant" if message["role"] == "XOD" else "user",
                "content": message["content"],
            }
            for message in messages
            if message["role"] in {"USER", "XOD"}
        ]


def configured_provider() -> AIProvider:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("XOD_OPENAI_MODEL", "gpt-5.5")
    if not api_key:
        return UnavailableAIProvider(model)
    return OpenAIProvider(api_key=api_key, model=model)
