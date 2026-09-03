# XOD architecture

## Phase 9 baseline with V2.2 provider observability

```
React / Vite client  ->  FastAPI HTTP API  ->  application services  ->  SQLite
                                      |
                                      +-> AIProvider (OpenAI implementation at the backend only)
```

The frontend owns display state and user interaction. It never reads SQLite and never receives `OPENAI_API_KEY`. FastAPI owns request validation, persistence orchestration, future provider selection, and data serialization. SQLite is local by default and accessed only by the backend.

## Initial API contract

Implemented now:

| Method | Path | Purpose | Response |
| --- | --- | --- | --- |
| `GET` | `/api/health` | Confirm the service and database schema are reachable. | `{ "status": "ok", "database": "ready" }` |
| `GET` | `/api/meta` | State the product phase and supported interaction modes. | `{ "phase": "9", "modes": ["SPAR", "TRIBUNAL"] }` |
| `GET` | `/api/conversations` | List local conversations without message contents. | conversation summaries |
| `POST` | `/api/conversations` | Start a persisted conversation. | conversation with empty messages |
| `GET` | `/api/conversations/{id}` | Reopen one conversation with messages. | conversation plus ordered messages |
| `POST` | `/api/conversations/{id}/messages` | Run one SPAR turn and persist the user/XOD pair on success. | updated conversation |
| `POST` | `/api/conversations/{id}/tribunal` | Run a validated Tribunal turn and save it with the XOD message. | updated conversation |
| `GET` | `/api/beliefs` | List independent belief summaries. | belief summaries |
| `POST` | `/api/beliefs` | Save a proposition as a versioned belief. | belief with version 1 |
| `GET` | `/api/beliefs/{id}` | Reopen one belief and its immutable history and epistemic records. | belief plus versions, evidence, predictions, and falsification conditions |
| `PATCH` | `/api/beliefs/{id}` | Create a revised belief version. | updated belief plus versions |
| `POST` | `/api/beliefs/{id}/evidence` | Record provenance-bearing support or contradiction. | evidence record |
| `POST` | `/api/beliefs/{id}/predictions` | Precommit a measurable prediction. | open prediction record |
| `PATCH` | `/api/predictions/{id}/resolve` | Record an observed outcome for an open prediction. | resolved prediction record |
| `POST` | `/api/beliefs/{id}/falsification-conditions` | Record an observable revision condition. | falsification-condition record |
| `POST` | `/api/analyses/{message_id}/self-critique-evaluation` | Evaluate and persist a Tribunal self-critique with the current rubric. | four checks and a bounded verdict |
| `GET` | `/api/analyses/{message_id}/self-critique-evaluation` | Reopen a persisted self-critique evaluation. | evaluation record |
| `GET` | `/api/specialist-readiness/cases` | List the fixed paired-evaluation seed cases. | case catalog |
| `GET` | `/api/specialist-readiness` | Compute the current specialist pilot decision. | readiness report |
| `POST` | `/api/specialist-readiness/measurements` | Record one paired baseline/specialist measurement. | upserted measurement |
| `GET` | `/api/analytics` | Calculate descriptive local epistemic analytics. | revision, delta, and calibration-proxy report |
| `GET` | `/api/beliefs/{id}/relationships` | List direct incoming and outgoing belief links. | relationship lists |
| `POST` | `/api/beliefs/{id}/relationships` | Record one directed relationship to another belief. | relationship record |
| `GET` | `/api/beliefs/{id}/relationship-neighborhood?depth=1..3` | Traverse a bounded local belief neighborhood. | nodes and edges |
| `GET` | `/api/evaluation-suite/cases` | List fixed behavioral regression cases. | evaluation case catalog |
| `GET` | `/api/failure-reports` | List voluntarily recorded XOD failures. | local failure reports |
| `POST` | `/api/failure-reports` | Record an observed failure and expected behavior. | failure report |

## AI provider boundary

`app/services/ai_provider.py` declares `AIProvider.reply()` and `analyze_tribunal()`. The FastAPI composition root injects a direct OpenAI Responses API provider; the browser cannot access the key. Tribunal uses the SDK's Pydantic structured-output parser, then stores only the validated analysis in `analyses.payload_json`. The Belief Ledger is independent of chat: `belief_versions` records immutable proposition/confidence/status snapshots and may link to the Tribunal message that prompted the save. Calls pass `store=False` and include only local conversation context.

`app/services/provider_failures.py` classifies provider failures into safe categories, gives each one a unique `XOD-...` error ID, and records the provider, model, SPAR/Tribunal operation, retryability, timestamp, and elapsed time. FastAPI returns only a concise message, category, ID, and retry signal. Structured logs and `provider_failure_events` deliberately exclude prompts, response bodies, conversation IDs, authorization headers, and API keys.

`app/services/self_critique_evaluator.py` is a pure, provider-independent evaluator. It scores the stored `xod_self_critique` against a named rubric and persists the check results separately from the Tribunal payload. This keeps prompt/provider output, deterministic quality checks, and human interpretation separate.

`app/services/specialist_evaluation.py` is also provider-independent. It compares manually recorded paired measurements over the fixed seed suite; a specialist configuration is only eligible for a pilot after complete coverage, a quality lift, no per-case regression, and bounded cost and latency. No routing or fan-out implementation exists in Phase 7.

`app/services/analytics.py` is pure and read-only. It compares a belief's current confidence to version 1 and calculates a directional calibration proxy from resolved predictions with a captured confidence at commitment. It excludes historical predictions that lack that snapshot and labels under-five-prediction calibration as insufficient data.

`app/repositories/relationships.py` owns the explicit belief graph. It rejects self-links and duplicate directed relationships, joins belief labels only for display, and performs bounded breadth-first neighborhood traversal. The system never infers links, creates reverse links, or renders a graph visualization in this phase.

`app/services/evaluation_suite.py` is a static behavioral catalog, not an AI evaluator. `app/repositories/failure_reports.py` records a concise user-authored failure description only when submitted; it may reference a Tribunal message by ID but does not duplicate or log its content.

## Deliberately deferred

- ABYSS analysis
- authentication and multi-user access
- graph visualization
- specialist-agent execution, vector search, and public deployment

Those are deferred to protect the core protocol from feature creep before its first evaluation loop exists.
