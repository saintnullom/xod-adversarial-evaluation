"""FastAPI composition root for XOD Phase 4."""

from collections.abc import Callable
from contextlib import asynccontextmanager

import logging
import sqlite3

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from app.db import connect, initialize_database
from app.repositories.beliefs import BeliefRepository
from app.repositories.analytics import AnalyticsRepository
from app.repositories.conversations import ConversationRepository
from app.repositories.epistemic_records import EpistemicRecordRepository
from app.repositories.self_critique_evaluations import SelfCritiqueEvaluationRepository
from app.repositories.specialist_measurements import SpecialistMeasurementRepository
from app.repositories.relationships import BeliefRelationshipRepository
from app.repositories.failure_reports import FailureReportRepository
from app.repositories.provider_failure_events import ProviderFailureEventRepository
from app.schemas import (
    AnalysisMode,
    AnalyticsResponse,
    EvidenceCreateRequest,
    EvidenceResponse,
    FalsificationConditionCreateRequest,
    FalsificationConditionResponse,
    ConversationCreateRequest,
    ConversationMessageCreateRequest,
    ConversationResponse,
    BeliefCreateRequest,
    BeliefDetailResponse,
    BeliefSummaryResponse,
    BeliefUpdateRequest,
    BeliefRelationshipCreateRequest,
    BeliefRelationshipListResponse,
    BeliefRelationshipNeighborhoodResponse,
    BeliefRelationshipResponse,
    EvaluationCaseResponse,
    FailureReportCreateRequest,
    FailureReportResponse,
    PredictionCreateRequest,
    PredictionResolveRequest,
    PredictionResponse,
    SelfCritiqueEvaluationResponse,
    SpecialistEvaluationCaseResponse,
    SpecialistMeasurementCreateRequest,
    SpecialistMeasurementResponse,
    SpecialistReadinessResponse,
    TribunalAnalysis,
    TribunalCreateRequest,
)
from app.services.ai_provider import AIProvider, configured_provider
from app.services.provider_failures import ProviderFailure, log_provider_failure, provider_failure_status
from app.services.conversation_service import ConversationService
from app.services.self_critique_evaluator import INTERPRETATION, RUBRIC_VERSION, evaluate_self_critique
from app.services.specialist_evaluation import EVALUATION_CASES, REQUIRED_CASE_IDS, readiness
from app.services.analytics import calculate_analytics
from app.services.evaluation_suite import EVALUATION_CASE_IDS, EVALUATION_SUITE


def create_app(provider_factory: Callable[[], AIProvider] = configured_provider) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        initialize_database()
        application.state.provider = provider_factory()
        yield

    application = FastAPI(title="XOD API", version="0.1.0-phase9", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
    )

    def provider_failure_http_exception(connection: sqlite3.Connection, failure: ProviderFailure) -> HTTPException:
        log_provider_failure(failure)
        try:
            ProviderFailureEventRepository(connection).create(failure.event())
        except sqlite3.Error:
            logging.getLogger("xod.provider").exception(
                "xod_provider_failure_event_persistence_failed error_id=%s", failure.error_id
            )
        return HTTPException(status_code=provider_failure_status(failure), detail=failure.safe_detail())

    @application.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "database": "ready"}

    @application.get("/api/meta")
    def meta() -> dict[str, object]:
        return {"phase": "9", "modes": [AnalysisMode.SPAR.value, AnalysisMode.TRIBUNAL.value]}

    @application.get("/api/conversations", response_model=list[ConversationResponse])
    def list_conversations() -> list[dict[str, object]]:
        connection = connect()
        try:
            return ConversationRepository(connection).list()
        finally:
            connection.close()

    @application.get("/api/beliefs", response_model=list[BeliefSummaryResponse])
    def list_beliefs() -> list[dict[str, object]]:
        connection = connect()
        try:
            return BeliefRepository(connection).list()
        finally:
            connection.close()

    @application.post("/api/beliefs", response_model=BeliefDetailResponse, status_code=201)
    def create_belief(payload: BeliefCreateRequest) -> dict[str, object]:
        connection = connect()
        try:
            return BeliefRepository(connection).create(
                payload.proposition.strip(),
                payload.user_confidence,
                payload.status.value,
                payload.source_analysis_message_id,
                [condition.strip() for condition in payload.falsification_conditions],
            )
        finally:
            connection.close()

    @application.get("/api/beliefs/{belief_id}", response_model=BeliefDetailResponse)
    def get_belief(belief_id: str) -> dict[str, object]:
        connection = connect()
        try:
            belief = BeliefRepository(connection).get(belief_id)
        finally:
            connection.close()
        if belief is None:
            raise HTTPException(status_code=404, detail="Belief not found.")
        return belief

    @application.patch("/api/beliefs/{belief_id}", response_model=BeliefDetailResponse)
    def update_belief(belief_id: str, payload: BeliefUpdateRequest) -> dict[str, object]:
        connection = connect()
        try:
            repository = BeliefRepository(connection)
            current = repository.get(belief_id)
            if current is None:
                raise HTTPException(status_code=404, detail="Belief not found.")
            fields = payload.model_fields_set
            return repository.revise(
                belief_id,
                payload.proposition.strip() if "proposition" in fields else str(current["proposition"]),
                payload.user_confidence if "user_confidence" in fields else current["user_confidence"],
                payload.status.value if payload.status is not None else str(current["status"]),
                payload.change_reason,
                payload.source_analysis_message_id,
            )
        finally:
            connection.close()

    @application.get(
        "/api/beliefs/{belief_id}/relationships", response_model=BeliefRelationshipListResponse
    )
    def list_belief_relationships(belief_id: str) -> dict[str, list[dict[str, object]]]:
        connection = connect()
        try:
            if BeliefRepository(connection).get(belief_id) is None:
                raise HTTPException(status_code=404, detail="Belief not found.")
            return BeliefRelationshipRepository(connection).list_for_belief(belief_id)
        finally:
            connection.close()

    @application.post(
        "/api/beliefs/{belief_id}/relationships",
        response_model=BeliefRelationshipResponse,
        status_code=201,
    )
    def create_belief_relationship(
        belief_id: str, payload: BeliefRelationshipCreateRequest
    ) -> dict[str, object]:
        connection = connect()
        try:
            beliefs = BeliefRepository(connection)
            if beliefs.get(belief_id) is None or beliefs.get(payload.target_belief_id) is None:
                raise HTTPException(status_code=404, detail="Source or target belief not found.")
            return BeliefRelationshipRepository(connection).create(
                belief_id,
                payload.target_belief_id,
                payload.relationship_type.value,
                payload.note.strip() if payload.note else None,
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="That relationship is already recorded.") from None
        finally:
            connection.close()

    @application.get(
        "/api/beliefs/{belief_id}/relationship-neighborhood",
        response_model=BeliefRelationshipNeighborhoodResponse,
    )
    def belief_relationship_neighborhood(
        belief_id: str, depth: int = Query(default=1, ge=1, le=3)
    ) -> dict[str, object]:
        connection = connect()
        try:
            if BeliefRepository(connection).get(belief_id) is None:
                raise HTTPException(status_code=404, detail="Belief not found.")
            return BeliefRelationshipRepository(connection).neighborhood(belief_id, depth)
        finally:
            connection.close()

    @application.get("/api/evaluation-suite/cases", response_model=list[EvaluationCaseResponse])
    def list_evaluation_cases() -> list[dict[str, str]]:
        return EVALUATION_SUITE

    @application.get("/api/failure-reports", response_model=list[FailureReportResponse])
    def list_failure_reports() -> list[dict[str, object]]:
        connection = connect()
        try:
            return FailureReportRepository(connection).list()
        finally:
            connection.close()

    @application.post("/api/failure-reports", response_model=FailureReportResponse, status_code=201)
    def create_failure_report(payload: FailureReportCreateRequest) -> dict[str, object]:
        if payload.evaluation_case_id and payload.evaluation_case_id not in EVALUATION_CASE_IDS:
            raise HTTPException(status_code=422, detail="evaluation_case_id is not part of the XOD evaluation suite.")
        connection = connect()
        try:
            if payload.source_analysis_message_id:
                message = connection.execute(
                    "SELECT id FROM analyses WHERE message_id = ?", (payload.source_analysis_message_id,)
                ).fetchone()
                if message is None:
                    raise HTTPException(status_code=422, detail="source_analysis_message_id is not a Tribunal analysis.")
            return FailureReportRepository(connection).create({
                "category": payload.category.value,
                "summary": payload.summary.strip(),
                "expected_behavior": payload.expected_behavior.strip() if payload.expected_behavior else None,
                "evaluation_case_id": payload.evaluation_case_id,
                "source_analysis_message_id": payload.source_analysis_message_id,
            })
        finally:
            connection.close()

    @application.post("/api/beliefs/{belief_id}/evidence", response_model=EvidenceResponse, status_code=201)
    def create_evidence(belief_id: str, payload: EvidenceCreateRequest) -> dict[str, object]:
        connection = connect()
        try:
            if BeliefRepository(connection).get(belief_id) is None:
                raise HTTPException(status_code=404, detail="Belief not found.")
            return EpistemicRecordRepository(connection).create_evidence(
                belief_id=belief_id,
                claim=payload.claim.strip(),
                source=payload.source.strip(),
                source_type=payload.source_type.strip(),
                direction=payload.direction.value,
                url=payload.url.strip() if payload.url else None,
                retrieved_at=payload.retrieved_at.strip() if payload.retrieved_at else None,
                reliability=payload.reliability,
                relevance=payload.relevance,
            )
        finally:
            connection.close()

    @application.post("/api/beliefs/{belief_id}/predictions", response_model=PredictionResponse, status_code=201)
    def create_prediction(belief_id: str, payload: PredictionCreateRequest) -> dict[str, object]:
        connection = connect()
        try:
            if BeliefRepository(connection).get(belief_id) is None:
                raise HTTPException(status_code=404, detail="Belief not found.")
            return EpistemicRecordRepository(connection).create_prediction(
                belief_id,
                payload.statement.strip(),
                payload.success_criteria.strip(),
                payload.expected_resolution_at.strip() if payload.expected_resolution_at else None,
            )
        finally:
            connection.close()

    @application.patch("/api/predictions/{prediction_id}/resolve", response_model=PredictionResponse)
    def resolve_prediction(prediction_id: str, payload: PredictionResolveRequest) -> dict[str, object]:
        connection = connect()
        try:
            return EpistemicRecordRepository(connection).resolve_prediction(
                prediction_id, payload.result.strip(), payload.impact.value
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Prediction not found.") from None
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        finally:
            connection.close()

    @application.post(
        "/api/beliefs/{belief_id}/falsification-conditions",
        response_model=FalsificationConditionResponse,
        status_code=201,
    )
    def create_falsification_condition(
        belief_id: str, payload: FalsificationConditionCreateRequest
    ) -> dict[str, object]:
        connection = connect()
        try:
            if BeliefRepository(connection).get(belief_id) is None:
                raise HTTPException(status_code=404, detail="Belief not found.")
            return EpistemicRecordRepository(connection).create_falsification_condition(
                belief_id, payload.condition.strip()
            )
        finally:
            connection.close()

    @application.post(
        "/api/analyses/{message_id}/self-critique-evaluation",
        response_model=SelfCritiqueEvaluationResponse,
    )
    def evaluate_analysis_self_critique(message_id: str) -> dict[str, object]:
        connection = connect()
        try:
            repository = SelfCritiqueEvaluationRepository(connection)
            payload = repository.analysis_payload(message_id)
            if payload is None:
                raise HTTPException(status_code=404, detail="Tribunal analysis not found.")
            analysis = TribunalAnalysis.model_validate_json(payload)
            score, verdict, checks = evaluate_self_critique(analysis)
            evaluation = repository.upsert(message_id, RUBRIC_VERSION, score, verdict, checks)
            return {**evaluation, "interpretation": INTERPRETATION}
        finally:
            connection.close()

    @application.get(
        "/api/analyses/{message_id}/self-critique-evaluation",
        response_model=SelfCritiqueEvaluationResponse,
    )
    def get_analysis_self_critique_evaluation(message_id: str) -> dict[str, object]:
        connection = connect()
        try:
            evaluation = SelfCritiqueEvaluationRepository(connection).get(message_id)
        finally:
            connection.close()
        if evaluation is None:
            raise HTTPException(status_code=404, detail="Self-critique evaluation not found.")
        return {**evaluation, "interpretation": INTERPRETATION}

    @application.get("/api/specialist-readiness/cases", response_model=list[SpecialistEvaluationCaseResponse])
    def list_specialist_evaluation_cases() -> list[dict[str, str]]:
        return EVALUATION_CASES

    @application.get("/api/specialist-readiness", response_model=SpecialistReadinessResponse)
    def specialist_readiness() -> dict[str, object]:
        connection = connect()
        try:
            return readiness(SpecialistMeasurementRepository(connection).list())
        finally:
            connection.close()

    @application.post(
        "/api/specialist-readiness/measurements",
        response_model=SpecialistMeasurementResponse,
        status_code=201,
    )
    def record_specialist_measurement(payload: SpecialistMeasurementCreateRequest) -> dict[str, object]:
        if payload.case_id not in REQUIRED_CASE_IDS:
            raise HTTPException(status_code=422, detail="case_id is not part of the XOD specialist seed suite.")
        connection = connect()
        try:
            return SpecialistMeasurementRepository(connection).upsert(payload.model_dump())
        finally:
            connection.close()

    @application.get("/api/analytics", response_model=AnalyticsResponse)
    def analytics() -> dict[str, object]:
        connection = connect()
        try:
            repository = AnalyticsRepository(connection)
            return calculate_analytics(repository.belief_history(), repository.predictions())
        finally:
            connection.close()

    @application.post("/api/conversations", response_model=ConversationResponse, status_code=201)
    def create_conversation(payload: ConversationCreateRequest) -> dict[str, object]:
        connection = connect()
        try:
            title = payload.title or "Untitled interrogation"
            return ConversationRepository(connection).create(title.strip())
        finally:
            connection.close()

    @application.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
    def get_conversation(conversation_id: str) -> dict[str, object]:
        connection = connect()
        try:
            conversation = ConversationRepository(connection).get(conversation_id)
        finally:
            connection.close()
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return conversation

    @application.post("/api/conversations/{conversation_id}/messages", response_model=ConversationResponse)
    async def add_message(
        conversation_id: str, payload: ConversationMessageCreateRequest, request: Request
    ) -> dict[str, object]:
        connection = connect()
        try:
            service = ConversationService(ConversationRepository(connection), request.app.state.provider)
            return await service.add_user_turn(conversation_id, payload.content)
        except KeyError:
            raise HTTPException(status_code=404, detail="Conversation not found.") from None
        except ProviderFailure as failure:
            raise provider_failure_http_exception(connection, failure) from None
        finally:
            connection.close()

    @application.post("/api/conversations/{conversation_id}/tribunal", response_model=ConversationResponse)
    async def add_tribunal(
        conversation_id: str, payload: TribunalCreateRequest, request: Request
    ) -> dict[str, object]:
        connection = connect()
        try:
            service = ConversationService(ConversationRepository(connection), request.app.state.provider)
            return await service.add_tribunal_turn(
                conversation_id, payload.content, payload.user_confidence
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Conversation not found.") from None
        except ProviderFailure as failure:
            raise provider_failure_http_exception(connection, failure) from None
        finally:
            connection.close()

    return application


app = create_app()
