# XOD roadmap

Current status: **Phase 9 complete**. Specialist-agent execution remains deferred until the Phase 7 gate has real paired measurements.

| Phase | Deliverable | Verification gate |
| --- | --- | --- |
| 0 | Runnable stack, SQLite schema, contracts, docs, offline tests | backend tests; frontend typecheck/build |
| 1 | Conversation and message persistence with one provider-backed SPAR path | API, repository, provider-failure, and prompt tests |
| 2 | Validated Tribunal output and rendering | schema, malformed-output, API, UI tests |
| 3 | Belief ledger, confidence, and immutable versions | repository and UI flow tests |
| 4 | Evidence, predictions, and falsification conditions | provenance, bounds, resolution tests |
| 5 | XOD self-critique quality evaluation | regression evaluation suite |
| 6 | Belief relationships | directed-link integrity and bounded traversal tests implemented |
| 7 | Specialist modules only if evaluations justify them | comparative quality/cost evaluation gate implemented; execution remains deferred |
| 8 | Calibration and epistemic-delta analytics | deterministic metric tests implemented |
| 9 | Evaluation suite and voluntary failure capture | behavioral-catalog and persistence tests implemented |

No phase advances with a known failing verification gate.
