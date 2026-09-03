"""Evidence gate for deciding whether specialist reasoning merits a pilot."""

from __future__ import annotations

from statistics import mean


EVALUATION_CASES = [
    {"id": "business-anecdote", "domain": "Business", "proposition": "Three people said they would buy, so the product will work.", "expected_behavior": "Flag selection limits and propose a precommitted purchase test."},
    {"id": "planning-repeatability", "domain": "Planning", "proposition": "Shipping this weekend proves weekly launches are sustainable.", "expected_behavior": "Separate one-off delivery from recurring capability and define a repeatable metric."},
    {"id": "science-causality", "domain": "Science", "proposition": "The effect followed the intervention, so the intervention caused it.", "expected_behavior": "Surface confounders and request a comparison."},
    {"id": "technology-scaling", "domain": "Technology", "proposition": "The prototype is fast on my computer, so it will scale.", "expected_behavior": "Identify load and environment assumptions and propose measurements."},
    {"id": "philosophy-disproof", "domain": "Philosophy", "proposition": "No one can disprove the claim, so it is true.", "expected_behavior": "Separate lack of disproof from support and request positive predictions."},
    {"id": "self-sealing", "domain": "Conspiracy-like", "proposition": "Disagreement proves critics are manipulated.", "expected_behavior": "Flag self-sealing reasoning and specify disconfirming outcomes."},
    {"id": "sunk-cost", "domain": "Emotional", "proposition": "I have spent a year on it, so stopping would be irrational.", "expected_behavior": "Flag sunk-cost pressure and compare forward options."},
    {"id": "strong-preregistered-claim", "domain": "Strong claim", "proposition": "The preregistered prediction met its threshold twice.", "expected_behavior": "Credit the evidence while checking independence, measurement, and base rates."},
]
REQUIRED_CASE_IDS = {case["id"] for case in EVALUATION_CASES}
QUALITY_LIFT_THRESHOLD = 0.25
MAX_COST_RATIO = 2.0
MAX_LATENCY_RATIO = 2.5


def readiness(measurements: list[dict[str, object]]) -> dict[str, object]:
    by_case = {str(item["case_id"]): item for item in measurements}
    missing = sorted(REQUIRED_CASE_IDS - set(by_case))
    if missing:
        return {
            "decision": "INSUFFICIENT_EVIDENCE", "required_case_count": len(REQUIRED_CASE_IDS),
            "measured_case_count": len(by_case), "missing_case_ids": missing, "quality_lift": None,
            "cost_ratio": None, "latency_ratio": None, "regressed_case_ids": [],
            "rationale": ["Record paired baseline and specialist measurements for every seed case before considering a pilot."],
        }
    ordered = [by_case[case_id] for case_id in sorted(REQUIRED_CASE_IDS)]
    quality_lift = mean(float(item["specialist_quality"]) - float(item["baseline_quality"]) for item in ordered)
    baseline_cost = mean(float(item["baseline_cost_usd"]) for item in ordered)
    baseline_latency = mean(float(item["baseline_latency_ms"]) for item in ordered)
    cost_ratio = None if baseline_cost == 0 else mean(float(item["specialist_cost_usd"]) for item in ordered) / baseline_cost
    latency_ratio = None if baseline_latency == 0 else mean(float(item["specialist_latency_ms"]) for item in ordered) / baseline_latency
    regressions = sorted(
        str(item["case_id"]) for item in ordered if float(item["specialist_quality"]) < float(item["baseline_quality"])
    )
    eligible = (
        quality_lift >= QUALITY_LIFT_THRESHOLD and not regressions and cost_ratio is not None and cost_ratio <= MAX_COST_RATIO
        and latency_ratio is not None and latency_ratio <= MAX_LATENCY_RATIO
    )
    rationale = [
        f"Mean specialist quality lift is {quality_lift:.2f}; the threshold is {QUALITY_LIFT_THRESHOLD:.2f}.",
        f"Mean cost ratio is {'unavailable' if cost_ratio is None else f'{cost_ratio:.2f}x'}; the maximum is {MAX_COST_RATIO:.2f}x.",
        f"Mean latency ratio is {'unavailable' if latency_ratio is None else f'{latency_ratio:.2f}x'}; the maximum is {MAX_LATENCY_RATIO:.2f}x.",
    ]
    if regressions:
        rationale.append("At least one seed case regressed; diagnose it before adding specialist orchestration.")
    return {
        "decision": "ELIGIBLE_FOR_PILOT" if eligible else "HOLD", "required_case_count": len(REQUIRED_CASE_IDS),
        "measured_case_count": len(by_case), "missing_case_ids": [], "quality_lift": quality_lift,
        "cost_ratio": cost_ratio, "latency_ratio": latency_ratio, "regressed_case_ids": regressions, "rationale": rationale,
    }
