"""Phase 1 orchestration: persist the user turn, then persist a provider reply."""

from __future__ import annotations

from app.repositories.conversations import ConversationRepository
from app.schemas import TribunalAnalysis
from app.services.ai_provider import AIProvider


class ConversationService:
    def __init__(self, repository: ConversationRepository, provider: AIProvider) -> None:
        self.repository = repository
        self.provider = provider

    async def add_user_turn(self, conversation_id: str, content: str) -> dict[str, object]:
        conversation = self.repository.get(conversation_id)
        if conversation is None:
            raise KeyError(conversation_id)
        user_content = content.strip()
        context = [
            {"role": message["role"], "content": message["content"]}
            for message in [*conversation["messages"][-15:], {"role": "USER", "content": user_content}]
        ]
        reply = await self.provider.reply(context)
        self.repository.add_turn(conversation_id, user_content, reply)
        result = self.repository.get(conversation_id)
        assert result is not None
        return result

    async def add_tribunal_turn(
        self, conversation_id: str, content: str, user_confidence: float | None
    ) -> dict[str, object]:
        conversation = self.repository.get(conversation_id)
        if conversation is None:
            raise KeyError(conversation_id)
        user_content = content.strip()
        context = [
            {"role": message["role"], "content": message["content"]}
            for message in [*conversation["messages"][-15:], {"role": "USER", "content": user_content}]
        ]
        analysis = await self.provider.analyze_tribunal(context, user_confidence)
        self.repository.add_turn(
            conversation_id,
            user_content,
            self._tribunal_summary(analysis),
            analysis.model_dump_json(),
        )
        result = self.repository.get(conversation_id)
        assert result is not None
        return result

    @staticmethod
    def _tribunal_summary(analysis: TribunalAnalysis) -> str:
        return (
            f"TRIBUNAL VERDICT: {analysis.verdict.value}\n"
            f"RECOMMENDED CONFIDENCE: {analysis.recommended_confidence.minimum:.0%}–"
            f"{analysis.recommended_confidence.maximum:.0%}\n"
            f"STRONGEST OBJECTION: {analysis.strongest_objection}"
        )
