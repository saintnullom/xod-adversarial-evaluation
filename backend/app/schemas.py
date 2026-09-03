"""Validated contracts shared by future API routes and AI providers."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class AnalysisMode(str, Enum):
    SPAR = "SPAR"
    TRIBUNAL = "TRIBUNAL"
    ABYSS = "ABYSS"


class Verdict(str, Enum):
    ROBUST = "ROBUST"
    PLAUSIBLE = "PLAUSIBLE"
    UNDERTESTED = "UNDERTESTED"
    SPECULATIVE = "SPECULATIVE"
    FRAGILE = "FRAGILE"
    CONTRADICTORY = "CONTRADICTORY"
    SELF_SEALING = "SELF_SEALING"


class BeliefStatus(str, Enum):
    ACTIVE_TEST = "ACTIVE_TEST"
    ACTIVE = "ACTIVE"
    REVISED = "REVISED"
    ABANDONED = "ABANDONED"


class BeliefRelationshipType(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    DEPENDS_ON = "DEPENDS_ON"
    DERIVED_FROM = "DERIVED_FROM"
    ALTERNATIVE_TO = "ALTERNATIVE_TO"
    EVIDENCE_FOR = "EVIDENCE_FOR"
    EVIDENCE_AGAINST = "EVIDENCE_AGAINST"
    REQUIRES = "REQUIRES"
    UNTESTED_DEPENDENCY = "UNTESTED_DEPENDENCY"


class FailureCategory(str, Enum):
    INCORRECT_OBJECTION = "INCORRECT_OBJECTION"
    MISUNDERSTOOD_PROPOSITION = "MISUNDERSTOOD_PROPOSITION"
    IGNORED_CONTEXT = "IGNORED_CONTEXT"
    HALLUCINATED_EVIDENCE = "HALLUCINATED_EVIDENCE"
    TOO_CONFIDENT = "TOO_CONFIDENT"
    MISSED_CONTRADICTION = "MISSED_CONTRADICTION"
    OTHER = "OTHER"


class EvidenceDirection(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"


class PredictionStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class PredictionImpact(str, Enum):
    SUPPORTS = "SUPPORTS"
    WEAKENS = "WEAKENS"
    INCONCLUSIVE = "INCONCLUSIVE"


class SelfCritiqueVerdict(str, Enum):
    USEFUL = "USEFUL"
    NEEDS_WORK = "NEEDS_WORK"


class SpecialistReadinessDecision(str, Enum):
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    HOLD = "HOLD"
    ELIGIBLE_FOR_PILOT = "ELIGIBLE_FOR_PILOT"


class EpistemicKind(str, Enum):
    EVIDENCE = "EVIDENCE"
    OBSERVATION = "OBSERVATION"
    INFERENCE = "INFERENCE"
    SPECULATION = "SPECULATION"


class ReasoningItem(BaseModel):
    claim: str = Field(min_length=1, max_length=2000)
    kind: EpistemicKind
    source: str | None = Field(max_length=500)
    url: str | None = Field(max_length=2048)


class ConfidenceRange(BaseModel):
    minimum: float = Field(ge=0, le=1)
    maximum: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def ordered(self) -> "ConfidenceRange":
        if self.minimum > self.maximum:
            raise ValueError("minimum confidence cannot exceed maximum confidence")
        return self


class TribunalAnalysis(BaseModel):
    proposition: str = Field(min_length=1, max_length=4000)
    user_confidence: float | None = Field(ge=0, le=1)
    assumptions: list[str]
    evidence_for: list[ReasoningItem]
    evidence_against: list[ReasoningItem]
    strongest_objection: str = Field(min_length=1, max_length=4000)
    alternative_explanations: list[str]
    bias_risks: list[str]
    falsification_conditions: list[str]
    cheapest_experiment: str = Field(min_length=1, max_length=4000)
    steelman: str = Field(min_length=1, max_length=4000)
    verdict: Verdict
    recommended_confidence: ConfidenceRange
    xod_self_critique: str = Field(min_length=1, max_length=4000)


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)


class ConversationMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class TribunalCreateRequest(ConversationMessageCreateRequest):
    user_confidence: float | None = Field(default=None, ge=0, le=1)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str
    analysis: TribunalAnalysis | None = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    messages: list[MessageResponse] = Field(default_factory=list)


class BeliefCreateRequest(BaseModel):
    proposition: str = Field(min_length=1, max_length=4000)
    user_confidence: float | None = Field(default=None, ge=0, le=1)
    status: BeliefStatus = BeliefStatus.ACTIVE_TEST
    source_analysis_message_id: str | None = None
    falsification_conditions: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("falsification_conditions")
    @classmethod
    def nonblank_falsification_conditions(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("falsification conditions cannot be blank")
        return values


class BeliefUpdateRequest(BaseModel):
    proposition: str | None = Field(default=None, min_length=1, max_length=4000)
    user_confidence: float | None = Field(default=None, ge=0, le=1)
    status: BeliefStatus | None = None
    change_reason: str | None = Field(default=None, max_length=1000)
    source_analysis_message_id: str | None = None


class BeliefVersionResponse(BaseModel):
    id: str
    belief_id: str
    version: int
    proposition: str
    user_confidence: float | None
    status: BeliefStatus
    change_reason: str | None
    source_analysis_message_id: str | None
    created_at: str


class BeliefSummaryResponse(BaseModel):
    id: str
    proposition: str
    current_version: int
    user_confidence: float | None
    xod_confidence: float | None
    status: BeliefStatus
    created_at: str
    updated_at: str


class BeliefDetailResponse(BeliefSummaryResponse):
    versions: list[BeliefVersionResponse]
    evidence: list["EvidenceResponse"] = Field(default_factory=list)
    predictions: list["PredictionResponse"] = Field(default_factory=list)
    falsification_conditions: list["FalsificationConditionResponse"] = Field(default_factory=list)


class EvidenceCreateRequest(BaseModel):
    claim: str = Field(min_length=1, max_length=4000)
    source: str = Field(min_length=1, max_length=1000)
    source_type: str = Field(default="USER_NOTE", min_length=1, max_length=100)
    url: str | None = Field(default=None, max_length=2048)
    retrieved_at: str | None = Field(default=None, max_length=100)
    reliability: float | None = Field(default=None, ge=0, le=1)
    relevance: float | None = Field(default=None, ge=0, le=1)
    direction: EvidenceDirection


class EvidenceResponse(BaseModel):
    id: str
    belief_id: str
    claim: str
    source: str
    source_type: str
    url: str | None
    retrieved_at: str | None
    reliability: float | None
    relevance: float | None
    direction: EvidenceDirection
    created_at: str


class PredictionCreateRequest(BaseModel):
    statement: str = Field(min_length=1, max_length=4000)
    success_criteria: str = Field(min_length=1, max_length=4000)
    expected_resolution_at: str | None = Field(default=None, max_length=100)


class PredictionResolveRequest(BaseModel):
    result: str = Field(min_length=1, max_length=4000)
    impact: PredictionImpact


class PredictionResponse(BaseModel):
    id: str
    belief_id: str
    statement: str
    success_criteria: str
    created_at: str
    belief_confidence_at_commit: float | None
    expected_resolution_at: str | None
    result: str | None
    status: PredictionStatus
    impact: PredictionImpact | None
    resolved_at: str | None


class FalsificationConditionCreateRequest(BaseModel):
    condition: str = Field(min_length=1, max_length=4000)


class FalsificationConditionResponse(BaseModel):
    id: str
    belief_id: str
    condition: str
    created_at: str


class SelfCritiqueCheck(BaseModel):
    key: str
    passed: bool
    rationale: str


class SelfCritiqueEvaluationResponse(BaseModel):
    message_id: str
    rubric_version: str
    score: int = Field(ge=0, le=4)
    verdict: SelfCritiqueVerdict
    checks: list[SelfCritiqueCheck]
    created_at: str
    interpretation: str


class SpecialistEvaluationCaseResponse(BaseModel):
    id: str
    domain: str
    proposition: str
    expected_behavior: str


class SpecialistMeasurementCreateRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=100)
    baseline_quality: float = Field(ge=0, le=4)
    specialist_quality: float = Field(ge=0, le=4)
    baseline_cost_usd: float = Field(ge=0)
    specialist_cost_usd: float = Field(ge=0)
    baseline_latency_ms: int = Field(ge=0)
    specialist_latency_ms: int = Field(ge=0)


class SpecialistMeasurementResponse(SpecialistMeasurementCreateRequest):
    id: str
    created_at: str
    updated_at: str


class SpecialistReadinessResponse(BaseModel):
    decision: SpecialistReadinessDecision
    required_case_count: int
    measured_case_count: int
    missing_case_ids: list[str]
    quality_lift: float | None
    cost_ratio: float | None
    latency_ratio: float | None
    regressed_case_ids: list[str]
    rationale: list[str]


class MetricAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class EpistemicDeltaResponse(BaseModel):
    availability: MetricAvailability
    beliefs_with_comparable_confidence: int
    mean_delta: float | None
    decreased_count: int
    increased_count: int
    unchanged_count: int
    interpretation: str


class CalibrationResponse(BaseModel):
    availability: MetricAvailability
    resolved_prediction_count: int
    scorable_prediction_count: int
    mean_confidence: float | None
    observed_support_rate: float | None
    mean_absolute_error: float | None
    interpretation: str


class BeliefRevisionAnalyticsResponse(BaseModel):
    belief_id: str
    proposition: str
    current_version: int
    status: BeliefStatus
    initial_confidence: float | None
    current_confidence: float | None
    epistemic_delta: float | None
    revised_at: str


class AnalyticsResponse(BaseModel):
    belief_count: int
    revised_belief_count: int
    abandoned_belief_count: int
    resolved_prediction_count: int
    epistemic_delta: EpistemicDeltaResponse
    calibration: CalibrationResponse
    revision_history: list[BeliefRevisionAnalyticsResponse]


class BeliefRelationshipCreateRequest(BaseModel):
    target_belief_id: str = Field(min_length=1, max_length=100)
    relationship_type: BeliefRelationshipType
    note: str | None = Field(default=None, max_length=1000)


class BeliefRelationshipResponse(BaseModel):
    id: str
    source_belief_id: str
    source_proposition: str
    target_belief_id: str
    target_proposition: str
    relationship_type: BeliefRelationshipType
    note: str | None
    created_at: str


class BeliefRelationshipListResponse(BaseModel):
    outgoing: list[BeliefRelationshipResponse]
    incoming: list[BeliefRelationshipResponse]


class BeliefRelationshipNeighborhoodResponse(BaseModel):
    root_belief_id: str
    depth: int
    nodes: list[BeliefSummaryResponse]
    edges: list[BeliefRelationshipResponse]


class EvaluationCaseResponse(BaseModel):
    id: str
    domain: str
    proposition: str
    expected_behavior: str
    primary_risk: str


class FailureReportCreateRequest(BaseModel):
    category: FailureCategory
    summary: str = Field(min_length=1, max_length=4000)
    expected_behavior: str | None = Field(default=None, max_length=2000)
    evaluation_case_id: str | None = Field(default=None, max_length=100)
    source_analysis_message_id: str | None = Field(default=None, max_length=100)


class FailureReportResponse(BaseModel):
    id: str
    category: FailureCategory
    summary: str
    expected_behavior: str | None
    evaluation_case_id: str | None
    source_analysis_message_id: str | None
    created_at: str
