# Evaluation Plan

## Status

This is a planned evaluation design. It contains no benchmark outcomes, scientific results, or validation claims.

## Objective

Evaluate whether a future research-workflow extension of XOD helps human reviewers surface reasoning and evidence issues while preserving appropriate uncertainty and human authority.

## Planned test cases

| Case | Intended review question |
| --- | --- |
| Unsupported claims | Does the workflow identify claims lacking adequate support? |
| Citation mismatch | Does it flag when a cited source does not support the stated claim? |
| Contradictory evidence | Does it surface materially conflicting evidence for human review? |
| Causal inference from correlational evidence | Does it distinguish correlation from causal support? |
| Cherry-picking | Does it identify selective evidence presentation? |
| Excessive confidence | Does it request calibration or escalation when certainty exceeds support? |
| Insufficient evidence | Does it classify inadequate support without fabricating a conclusion? |
| Clean well-supported controls | Does it avoid inventing issues in well-supported material? |

All materials should be labelled by case type, source availability, expected concerns, and reviewer rationale. Test cases should include clean controls as well as deliberately problematic examples.

## Planned metrics

- Issue detection rate
- False positive rate
- Missed issue rate
- Human/XOD agreement
- Escalation appropriateness
- Reviewer time
- Appropriate belief revision
- Inappropriate belief revision

Metrics must be defined before analysis, reported with denominator and uncertainty where feasible, and separated by case type. Human review remains the reference process; agreement is not proof of correctness.

## Proposed protocol

1. Establish a representative, versioned evaluation set and reviewer rubric.
2. Have independent human reviewers label support, contradictions, uncertainty, and escalation needs.
3. Run the proposed workflow without exposing hidden reference labels.
4. Compare workflow flags, status suggestions, and logged reasoning records to the reviewer rubric.
5. Inspect false positives, missed issues, and inappropriate belief revisions qualitatively.
6. Report limitations, disagreement patterns, and data-governance choices alongside quantitative metrics.

## Boundaries

The current repository has internal engineering evaluation cases, but not this external research benchmark. No current results should be inferred from this plan.
