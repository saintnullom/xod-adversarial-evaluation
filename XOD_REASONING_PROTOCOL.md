# XOD reasoning protocol

## Core rule

XOD does not decide what is true. It identifies what would have to be true for the user to be wrong.

## Phase 1 SPAR contract

Phase 1 uses one concise provider response, persisted as a conversation message only after the request succeeds. It must use this order: proposition, strongest assumption, strongest objection, alternative, and cheapest test. It is deliberately not stored as validated epistemic data.

## Tribunal response contract (Phase 2, implemented)

Every Tribunal analysis is parsed and validated as a `TribunalAnalysis` before it can be stored. It contains:

1. proposition and optional user confidence
2. assumptions
3. evidence for and against, explicitly labelled as evidence, observation, inference, or speculation
4. strongest objection and alternative explanations
5. bias risks and falsification conditions
6. cheapest discriminating experiment and steelman
7. descriptive verdict: `ROBUST`, `PLAUSIBLE`, `UNDERTESTED`, `SPECULATIVE`, `FRAGILE`, `CONTRADICTORY`, or `SELF_SEALING`
8. recommended confidence range, not a false-precise point estimate
9. `XOD'S OBJECTION TO XOD`: missing context, generic framing, or assumptions that could weaken its criticism

## Modes

- **SPAR**: proposition, strongest assumption, strongest objection, alternative, cheapest test.
- **TRIBUNAL**: the full structured contract above.
- **ABYSS**: sparingly examines worldview-level premises, recursive dependencies, and identity attachment.

## Guardrails

- Do not treat anecdotes as representative evidence.
- Do not infer absence from missing evidence without a detection argument.
- Flag claims that reinterpret every outcome as confirmation as `SELF_SEALING`.
- Reward correctly predeclared predictions; distinguish post-hoc success claims.
- Critique the analysis itself whenever it is substantial.

## Phase 4 evidence and prediction protocol

- Record evidence with a specific claim, source, source type, direction, and optional retrieval, URL, reliability, and relevance metadata. Provenance is data supplied by the user or a future tool, not a claim that XOD independently verified it.
- A prediction must state measurable criteria before its outcome is known. Resolution records the observed result and `SUPPORTS`, `WEAKENS`, or `INCONCLUSIVE`; it is not an automatic truth verdict.
- A falsification condition must describe an observable result that should trigger substantial revision or abandonment. It remains visible on the independent belief record even after the source conversation is no longer in view.

## Phase 5 self-critique evaluation protocol

- A Tribunal self-critique must name a specific limitation in XOD's own framing, not simply repeat the strongest objection.
- It should identify missing context, scope, data, measurement, or domain expertise and name what could weaken XOD's criticism.
- The `self-critique-v1` rubric checks: concrete length, distinction from the primary objection, named scope/context, and a revision path. A `USEFUL` result requires at least three checks.
- This rubric is a deterministic quality screen, not a semantic judge. Demonstrating improved reasoning quality still requires human review and later outcome evidence.

## Phase 6 belief relationship protocol

- A relationship is an explicit user-recorded statement about how one belief relates to another; XOD does not infer it from similar wording or shared evidence.
- Links are directed. For example, `A DEPENDS_ON B` does not automatically create `B SUPPORTS A`.
- Traverse only a bounded neighborhood when inspecting dependencies so a small local question does not become an unbounded graph analysis.
- A relationship list is an aid to inspection, not evidence that either linked belief is true.
