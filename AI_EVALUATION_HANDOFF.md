# XOD implementation handoff for AI evaluation

## Purpose and evaluation posture

XOD (Executive Objection Daemon) is a local-first adversarial reasoning tool. Its central rule is: **it does not decide what is true; it identifies what would have to be true for the user to be wrong.**

Evaluate it against that rule. Do not reward reflexive disagreement, false certainty, unsupported sources, or impressive-but-unfalsifiable prose. The correct output can conclude that a proposition is reasonably robust within the available evidence.

This document describes verified implementation state as of 2026-08-25. It is not a claim that the OpenAI provider or a public deployment was live-tested on that date.

## Current product state

The staged core through Phase 9 is implemented locally:

| Phase | Implemented result |
| --- | --- |
| 0 | Vite/React client, FastAPI backend, SQLite initialization, provider abstraction, local tests/docs. |
| 1 | Persisted SPAR conversations; user/XOD message pair is saved only after a successful provider response. |
| 2 | Pydantic-validated Tribunal analysis, stored payload, structured rendering. |
| 3 | Independent Belief Ledger with immutable belief versions and stated confidence/status. |
| 4 | Evidence provenance, falsification conditions, measurable predictions, and explicit outcomes. |
| 5 | Deterministic self-critique rubric and persisted results. |
| 6 | Explicit directed belief relationships with duplicate/self-link rejection and bounded traversal. |
| 7 | Specialist-readiness measurement gate only; no specialist-agent execution. |
| 8 | Descriptive revision/delta analytics and directional calibration proxy. |
| 9 | Nine-domain behavioral evaluation catalog and voluntary local failure reports. |

## Architecture

```text
React/Vite frontend
  -> FastAPI HTTP API
    -> repositories and pure deterministic services
      -> local SQLite database
    -> AIProvider interface
      -> OpenAI Responses API implementation (backend only)
```

The browser never receives `OPENAI_API_KEY` and never accesses SQLite. The default database is `xod/data/xod.db` and is ignored by Git. IDs are UUID strings; timestamps are UTC ISO-8601 strings.

### Important module boundaries

- `backend/app/services/ai_provider.py`: SPAR and Tribunal provider boundary. Calls use `store=False`; Tribunal parses directly into `TribunalAnalysis`.
- `backend/app/services/conversation_service.py`: provider call and atomic persistence sequence.
- `backend/app/repositories/`: SQLite persistence only; no provider calls.
- `backend/app/services/self_critique_evaluator.py`: pure four-check deterministic rubric.
- `backend/app/services/specialist_evaluation.py`: pure paired quality/cost/latency readiness calculation.
- `backend/app/services/analytics.py`: pure descriptive metrics.
- `backend/app/services/evaluation_suite.py`: fixed behavioral test catalog; not an AI evaluator.
- `frontend/src/main.tsx`: single React interface for chat, ledger, analytics, relationship entry, specialist gate, and evaluation/failure intake.

## Interaction modes and contracts

### SPAR

Provider response must use this concise order: proposition, strongest assumption, strongest objection, alternative, and cheapest test.

### Tribunal

`TribunalAnalysis` requires proposition, user confidence, assumptions, evidence for/against with epistemic kind, strongest objection, alternatives, bias risks, falsification conditions, cheapest experiment, steelman, verdict, recommended confidence range, and `xod_self_critique`.

Valid verdicts: `ROBUST`, `PLAUSIBLE`, `UNDERTESTED`, `SPECULATIVE`, `FRAGILE`, `CONTRADICTORY`, and `SELF_SEALING`.

## HTTP API inventory

### Core

- `GET /api/health`, `GET /api/meta`
- `GET|POST /api/conversations`
- `GET /api/conversations/{id}`
- `POST /api/conversations/{id}/messages` (SPAR)
- `POST /api/conversations/{id}/tribunal`

### Beliefs and records

- `GET|POST /api/beliefs`
- `GET|PATCH /api/beliefs/{id}`
- `POST /api/beliefs/{id}/evidence`
- `POST /api/beliefs/{id}/predictions`
- `PATCH /api/predictions/{id}/resolve`
- `POST /api/beliefs/{id}/falsification-conditions`

### Evaluation, relationships, and analytics

- `GET|POST /api/analyses/{message_id}/self-critique-evaluation`
- `GET /api/beliefs/{id}/relationships`
- `POST /api/beliefs/{id}/relationships`
- `GET /api/beliefs/{id}/relationship-neighborhood?depth=1..3`
- `GET /api/specialist-readiness/cases`
- `GET /api/specialist-readiness`
- `POST /api/specialist-readiness/measurements`
- `GET /api/analytics`
- `GET /api/evaluation-suite/cases`
- `GET|POST /api/failure-reports`

## Persistence and invariants

Core tables include conversations, messages, beliefs, belief_versions, evidence, predictions, belief_falsification_conditions, analyses, self_critique_evaluations, specialist_evaluation_measurements, belief_relationships, and failure_reports.

Applied migration sequence:

1. `0002_belief_versions_add_status_and_analysis_source`
2. `0003_belief_falsification_conditions`
3. `0004_self_critique_evaluations`
4. `0005_specialist_evaluation_measurements`
5. `0006_prediction_confidence_snapshot`
6. `0007_belief_relationships`
7. `0008_failure_reports`

Key safeguards:

- Confidence is optional but constrained to `[0, 1]`.
- Belief revisions create immutable versions.
- Evidence needs a claim, source, source type, and explicit direction.
- Predictions resolve once from `OPEN` to `RESOLVED`; outcome is `SUPPORTS`, `WEAKENS`, or `INCONCLUSIVE`.
- New predictions snapshot belief confidence at commitment. Existing pre-snapshot records remain null rather than being backfilled.
- Relationships are directed, manually entered, and cannot be self-links or duplicate the same source/target/type. Reverse links are separate intentional records.
- Failure reports store concise voluntary summaries and IDs, not copied conversation/analysis content.

## Deterministic evaluation logic

### Self-critique (`self-critique-v1`)

The critique is checked for: a nontrivial limitation, distinction from the strongest objection, a scope/context limitation, and a path by which evidence could weaken XOD’s criticism. `USEFUL` requires at least 3 of 4 checks.

This is a regression guard, not evidence that the Tribunal analysis is correct.

### Specialist readiness

Eight paired baseline/specialist cases must be measured. A candidate is `ELIGIBLE_FOR_PILOT` only when all cases are covered, mean quality lift is at least `0.25` on a 0–4 scale, no case regresses, mean cost is at most `2.00x`, and mean latency is at most `2.50x` baseline.

Current expected state without user-entered measurements: `INSUFFICIENT_EVIDENCE`. No specialist agents or fan-out calls have been implemented.

### Analytics

Epistemic delta is current stated confidence minus version-1 confidence. It is not a truth score.

Calibration is only a directional proxy: a prediction outcome of `SUPPORTS` maps to `1`, `WEAKENS` maps to `0`, and `INCONCLUSIVE` is excluded. At least five resolved predictions with confidence snapshots are required before calibration is marked available.

## Phase 9 evaluation suite

The catalog covers business, philosophy, science, personal planning, technology, creative strategy, conspiracy-like reasoning, emotionally invested beliefs, and genuinely strong arguments. Evaluate whether XOD:

- is too agreeable or too contrarian;
- distinguishes evidence, observation, inference, and speculation;
- exposes causal and selection assumptions;
- identifies self-sealing logic;
- names falsification paths;
- respects genuinely strong evidence;
- remains concise and appropriately uncertain.

Observed mistakes can be logged locally as: `INCORRECT_OBJECTION`, `MISUNDERSTOOD_PROPOSITION`, `IGNORED_CONTEXT`, `HALLUCINATED_EVIDENCE`, `TOO_CONFIDENT`, `MISSED_CONTRADICTION`, or `OTHER`.

## Verification evidence

The latest local verification completed on 2026-08-25:

```text
backend: python -m unittest discover -s tests -v
result: 27 tests passed

frontend: npm.cmd run typecheck
result: passed

frontend: npm.cmd run build
result: passed
```

The local schema migration `0008_failure_reports` was applied and its table presence was verified. This is local test/build evidence only; it is not a hosted deployment, multi-user, or fresh external-provider claim.

## Known limitations and deliberately deferred work

- No ABYSS mode.
- No authentication, authorization, multi-user model, encryption at rest, backups, or public deployment.
- No graph visualization; only lists and bounded API traversal.
- No automatic confidence updates from prediction results.
- No specialist-agent execution; only an evidence gate.
- No automatic failure detection or automatic dataset promotion.
- The frontend has no automated browser/E2E test suite.
- Current provider tests use fakes; the latest verification did not send a live OpenAI request.

## Run and review locally

From `xod`, run the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000 --env-file ..\.env.local
```

Then, from `xod/frontend`:

```powershell
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. The API health endpoint is `http://127.0.0.1:8000/api/health`.

## Questions for the reviewing AI

1. Does the Tribunal prompt and schema make the distinction between evidence and inference clear enough?
2. Are the self-critique rubric checks meaningful without overstating what they prove?
3. Are the prediction outcome semantics and calibration proxy sufficiently cautious?
4. Do relationship directions and types communicate epistemic dependencies clearly?
5. What failure cases are missing from the nine-domain evaluation suite?
6. Which deferred capability would materially improve interrogation quality next, and which would be feature creep?
