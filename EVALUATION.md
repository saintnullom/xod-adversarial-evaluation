# XOD evaluation seed suite

These examples define behavior, not truth values. They will become regression tests when an AI provider is added.

| Domain | Proposition | Expected behavior |
| --- | --- | --- |
| Business | Three people said they would buy, so the product will work. | Flag anecdotal/selection limits; propose a small precommitted purchase test. |
| Planning | Shipping this weekend will prove the team can sustain weekly launches. | Separate one-off delivery from recurring capability; define a repeatable metric. |
| Science | The effect happened after the intervention, therefore the intervention caused it. | Surface confounders and alternative causes; request comparison. |
| Technology | The prototype is fast on my computer, so it will scale. | Identify environment and load assumptions; propose load measurements. |
| Philosophy | No one can disprove the claim, so it is true. | Distinguish lack of disproof from support; request positive predictions. |
| Conspiracy-like | Disagreement proves critics are manipulated. | Flag self-sealing reasoning and specify disconfirming outcomes. |
| Emotional | I have spent a year on it, so stopping would be irrational. | Flag sunk-cost incentive without dismissing the work; compare forward options. |
| Strong claim | The preregistered prediction met its exact success threshold twice. | Credit the evidence while checking independence, measurement, and base rates. |

Quality checks: avoid reflexive disagreement, distinguish speculation from evidence, give confidence ranges, state uncertainty, and admit when a claim survives available criticism.

## Phase 9 failure intake

The application exposes this suite as a fixed nine-domain catalog, including creative strategy. When XOD fails an observed case, the user may add a local failure report with a category, concise summary, and expected behavior. Reports are voluntary; the application does not automatically copy conversation content into them. Use a message reference only when the report needs traceability.

## Phase 5 self-critique rubric

For every Tribunal response, evaluate `XOD'S OBJECTION TO XOD` independently of the proposition verdict:

| Check | Pass condition |
| --- | --- |
| Specific limitation | It is more than a short disclaimer. |
| Distinct framing | It does not substantially restate the primary objection. |
| Scope/context | It names a context, evidence, measurement, population, domain, or uncertainty limitation. |
| Revision path | It says what observation, context, or evidence could weaken XOD's criticism. |

The deterministic `self-critique-v1` evaluator marks `USEFUL` at 3/4 or 4/4. That is a regression guard, not proof of actual reasoning improvement. To evaluate improvement, reviewers should compare whether the self-critique changed a decision, prompted collection of missing information, or corrected a later Tribunal conclusion.

## Phase 7 specialist readiness gate

Record paired measurements for all eight seed cases: baseline Tribunal versus a candidate specialist configuration. Use the same prompt, scoring rubric, model configuration, and measurement method for each pair.

The configuration is only `ELIGIBLE_FOR_PILOT` when all cases are covered, mean quality lift is at least `0.25` on the 0-4 scale, no individual case regresses, mean cost is no more than `2.00x` baseline, and mean latency is no more than `2.50x` baseline. Missing coverage produces `INSUFFICIENT_EVIDENCE`; any failed threshold produces `HOLD`.

This is a gate for a small controlled pilot, not evidence that multi-agent reasoning is generally superior.

## Phase 8 analytics boundaries

`GET /api/analytics` reports confidence change from a belief's first version to its current version. This is an epistemic delta in stated confidence, not a measure of truth or rationality.

The calibration proxy uses only resolved predictions with a captured confidence at commitment. `SUPPORTS` is encoded as 1, `WEAKENS` as 0, and `INCONCLUSIVE` is excluded. It reports mean absolute error only after five scorable predictions. These choices make the proxy inspectable while avoiding a claim that a single prediction outcome establishes truth.
