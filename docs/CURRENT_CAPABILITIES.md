# Current Capabilities

This table describes the working local prototype only. “Tested” refers to the local engineering verification baseline completed on 2026-09-03: 29/29 backend tests, 3/3 frontend regression tests, frontend typecheck, and frontend production build. It does not mean scientific or external validation.

| Capability | Implemented | Tested | User-visible | Notes |
| --- | --- | --- | --- | --- |
| Local React/Vite interface | Yes | Yes | Yes | Runs locally in a browser. |
| FastAPI application | Yes | Yes | Indirectly | Serves local API routes and workflow orchestration. |
| SPAR reasoning conversation | Yes | Yes | Yes | Requires configured provider for live model-backed output. |
| Tribunal structured objection workflow | Yes | Yes | Yes | Preserves structured result handling. |
| Persistent Belief Ledger | Yes | Yes | Yes | Local SQLite records versioned beliefs. |
| Manual confidence updates | Yes | Yes | Yes | User records confidence; no autonomous confidence change exists. |
| Evidence, predictions, and falsification records | Yes | Yes | Yes | Stored as part of the local reasoning workflow. |
| Explicit belief relationships | Yes | Yes | Yes | Manually recorded directed relationships with bounded traversal. |
| Graph visualization | No | No | No | Not implemented. |
| Local descriptive analytics | Yes | Yes | Yes | Descriptive; not a research benchmark. |
| Internal evaluation cases | Yes | Yes | Yes | Nine internal cases; not external validation. |
| Voluntary failure reporting | Yes | Yes | Yes | Successful submission feedback and regression coverage exist. |
| Classified provider diagnostics | Yes | Yes | Yes | Category, error ID, retry hint, and privacy-minimal metadata. |
| Specialist readiness | Yes | Yes | Yes | Readiness metadata/gate exists; specialist-agent execution does not. |
| Research Integrity Agent | No | No | No | PROPOSED / CATALYST-SCOPED WORK. |
| Zotero integration | No | No | No | PROPOSED only. |
| External benchmark validation | No | No | No | Not performed. |
| Production deployment | No | No | No | Not performed. |
| Paying-user validation | No | No | No | Not performed. |

## Provider boundary

The interface and local data model operate without publishing XOD. A model-backed SPAR or Tribunal response needs a configured provider. Provider failures are classified for diagnostics, but a passing local test suite does not verify live provider behavior under all credentials, models, or network conditions.
