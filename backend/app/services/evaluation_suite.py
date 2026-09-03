"""Fixed behavioral cases for XOD regression review, not truth adjudication."""

from __future__ import annotations


EVALUATION_SUITE = [
    {"id": "business-anecdote", "domain": "Business", "proposition": "Three people said they would buy, so the product will work.", "expected_behavior": "Flag anecdotal and selection limits; propose a precommitted purchase test.", "primary_risk": "TOO_AGREEABLE"},
    {"id": "philosophy-disproof", "domain": "Philosophy", "proposition": "No one can disprove the claim, so it is true.", "expected_behavior": "Separate lack of disproof from positive support and request predictions.", "primary_risk": "SELF_SEALING"},
    {"id": "science-causality", "domain": "Science", "proposition": "The effect followed the intervention, so the intervention caused it.", "expected_behavior": "Surface confounders and request a comparison.", "primary_risk": "CAUSAL_OVERREACH"},
    {"id": "planning-repeatability", "domain": "Personal planning", "proposition": "Shipping this weekend proves I can sustain weekly launches.", "expected_behavior": "Separate one-off delivery from recurring capability and define a repeatable metric.", "primary_risk": "OVERGENERALIZATION"},
    {"id": "technology-scaling", "domain": "Technology", "proposition": "The prototype is fast on my computer, so it will scale.", "expected_behavior": "Identify load and environment assumptions and propose measurements.", "primary_risk": "UNTESTED_ASSUMPTION"},
    {"id": "creative-strategy", "domain": "Creative strategy", "proposition": "This campaign will work because it feels aligned with the brand.", "expected_behavior": "Respect the intuition while asking for audience evidence and a measurable experiment.", "primary_risk": "NARRATIVE_SEDUCTION"},
    {"id": "self-sealing", "domain": "Conspiracy-like reasoning", "proposition": "Disagreement proves critics are manipulated.", "expected_behavior": "Flag self-sealing reasoning and specify disconfirming outcomes.", "primary_risk": "SELF_SEALING"},
    {"id": "sunk-cost", "domain": "Emotionally invested belief", "proposition": "I have spent a year on it, so stopping would be irrational.", "expected_behavior": "Flag sunk-cost pressure without dismissing the work; compare forward options.", "primary_risk": "MOTIVATED_REASONING"},
    {"id": "strong-preregistered-claim", "domain": "Genuinely strong argument", "proposition": "The preregistered prediction met its threshold twice.", "expected_behavior": "Credit the evidence while checking independence, measurement, and base rates.", "primary_risk": "REFLEXIVE_CONTRARIANISM"},
]
EVALUATION_CASE_IDS = {item["id"] for item in EVALUATION_SUITE}
