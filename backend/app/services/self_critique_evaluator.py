"""Deterministic, inspectable quality checks for Tribunal self-critique."""

from __future__ import annotations

import re

from app.schemas import SelfCritiqueCheck, TribunalAnalysis


RUBRIC_VERSION = "self-critique-v1"
INTERPRETATION = (
    "This deterministic rubric checks whether XOD names an inspectable limitation. "
    "It does not establish that the analysis is true or that self-critique improved reasoning quality."
)
CONTEXT_TERMS = {
    "assumption", "context", "data", "domain", "evidence", "measurement", "population",
    "sample", "scope", "segment", "uncertainty",
}
REVISION_TERMS = {"could", "if", "need", "unless", "verify", "would", "test", "weaken"}


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def evaluate_self_critique(analysis: TribunalAnalysis) -> tuple[int, str, list[SelfCritiqueCheck]]:
    critique = analysis.xod_self_critique.strip()
    critique_tokens = _tokens(critique)
    objection_tokens = _tokens(analysis.strongest_objection)
    overlap = len(critique_tokens & objection_tokens) / max(1, len(critique_tokens | objection_tokens))
    checks = [
        SelfCritiqueCheck(
            key="specific_limitation",
            passed=len(critique) >= 40,
            rationale="The self-critique is long enough to state a concrete limitation rather than a disclaimer."
            if len(critique) >= 40
            else "The self-critique is too brief to make its limitation inspectable.",
        ),
        SelfCritiqueCheck(
            key="distinct_from_primary_objection",
            passed=overlap < 0.72,
            rationale="The self-critique is not merely a restatement of the strongest objection."
            if overlap < 0.72
            else "The self-critique substantially repeats the strongest objection instead of inspecting XOD's framing.",
        ),
        SelfCritiqueCheck(
            key="names_scope_or_missing_context",
            passed=bool(critique_tokens & CONTEXT_TERMS),
            rationale="The self-critique identifies a scope, evidence, measurement, or context limitation."
            if critique_tokens & CONTEXT_TERMS
            else "The self-critique does not name a recognizable scope or missing-context limitation.",
        ),
        SelfCritiqueCheck(
            key="offers_a_revision_path",
            passed=bool(critique_tokens & REVISION_TERMS),
            rationale="The self-critique identifies how additional context, testing, or evidence could weaken XOD's criticism."
            if critique_tokens & REVISION_TERMS
            else "The self-critique does not indicate what could weaken or revise XOD's criticism.",
        ),
    ]
    score = sum(check.passed for check in checks)
    verdict = "USEFUL" if score >= 3 else "NEEDS_WORK"
    return score, verdict, checks
