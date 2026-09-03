"""Pure calculations for XOD's descriptive, non-truth-claiming analytics."""

from __future__ import annotations

from statistics import mean


CALIBRATION_MINIMUM = 5


def calculate_analytics(
    belief_history: list[dict[str, object]], predictions: list[dict[str, object]]
) -> dict[str, object]:
    comparable = [
        row for row in belief_history
        if row["initial_confidence"] is not None and row["current_confidence"] is not None
    ]
    deltas = [float(row["current_confidence"]) - float(row["initial_confidence"]) for row in comparable]
    delta = {
        "availability": "AVAILABLE" if deltas else "INSUFFICIENT_DATA",
        "beliefs_with_comparable_confidence": len(deltas),
        "mean_delta": mean(deltas) if deltas else None,
        "decreased_count": sum(value < 0 for value in deltas),
        "increased_count": sum(value > 0 for value in deltas),
        "unchanged_count": sum(value == 0 for value in deltas),
        "interpretation": "Change in stated user confidence from version 1 to the current belief version; it is not a truth score.",
    }
    resolved = [row for row in predictions if row["status"] == "RESOLVED"]
    scorable = [
        row for row in resolved
        if row["belief_confidence_at_commit"] is not None and row["impact"] in {"SUPPORTS", "WEAKENS"}
    ]
    confidences = [float(row["belief_confidence_at_commit"]) for row in scorable]
    outcomes = [1.0 if row["impact"] == "SUPPORTS" else 0.0 for row in scorable]
    errors = [abs(confidence - outcome) for confidence, outcome in zip(confidences, outcomes, strict=True)]
    calibration = {
        "availability": "AVAILABLE" if len(scorable) >= CALIBRATION_MINIMUM else "INSUFFICIENT_DATA",
        "resolved_prediction_count": len(resolved),
        "scorable_prediction_count": len(scorable),
        "mean_confidence": mean(confidences) if confidences else None,
        "observed_support_rate": mean(outcomes) if outcomes else None,
        "mean_absolute_error": mean(errors) if errors else None,
        "interpretation": "Directional calibration proxy: SUPPORTS is scored as 1 and WEAKENS as 0. It excludes inconclusive outcomes and does not establish a proposition's truth.",
    }
    revisions = []
    for row in belief_history:
        initial = row["initial_confidence"]
        current = row["current_confidence"]
        revisions.append({
            **row,
            "epistemic_delta": None if initial is None or current is None else float(current) - float(initial),
        })
    return {
        "belief_count": len(belief_history),
        "revised_belief_count": sum(int(row["current_version"]) > 1 for row in belief_history),
        "abandoned_belief_count": sum(row["status"] == "ABANDONED" for row in belief_history),
        "resolved_prediction_count": len(resolved),
        "epistemic_delta": delta,
        "calibration": calibration,
        "revision_history": revisions,
    }
