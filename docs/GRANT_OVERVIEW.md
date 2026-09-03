# XOD Grant Overview

## Project status

XOD — Executive Objection Daemon — is a working local prototype for structured, adversarial reasoning. It helps a human examine claims with objections, evidence, assumptions, predictions, uncertainty, and a versioned belief record. It is not a production service and does not make autonomous decisions.

## Problem

AI-assisted synthesis can produce coherent language without preserving the chain of support, uncertainty, or alternatives that a reviewer needs to inspect. XOD explores whether a local, inspectable workflow can make those reasoning artifacts visible before a human acts.

## Existing prototype foundation

The current prototype includes local SPAR and Tribunal workflows, a versioned Belief Ledger, manually recorded relationships, evidence and prediction records, local analytics, internal evaluation cases, and privacy-minimal provider diagnostics. Specialist-readiness metadata exists; specialist-agent execution does not.

The local verification baseline on 2026-09-03 is 29/29 backend tests, 3/3 frontend regression tests, frontend typecheck, and a frontend production build passing. These are engineering checks only. They are not scientific validation, external benchmark validation, or evidence of real-world effectiveness.

## Catalyst-scoped opportunity

The proposed Research Integrity Agent would apply XOD's structured reasoning concepts to research synthesis. It would retain a human decision point and auditable record rather than claim automated truth determination. The proposed work is described in [RESEARCH_INTEGRITY_WORKFLOW.md](RESEARCH_INTEGRITY_WORKFLOW.md) and evaluated through the plan in [EVALUATION_PLAN.md](EVALUATION_PLAN.md).

## Current boundaries

- No graph visualization.
- No autonomous confidence changes.
- No external benchmark validation.
- No production deployment or paying-user validation.
- No implemented Zotero integration; Zotero is proposed only.
- No guarantee of research integrity, correctness, safety, or trustworthy AI.

## Grant-review focus

The relevant question is not whether XOD has already solved research integrity. It is whether its local, inspectable architecture is a credible foundation for a bounded, human-supervised research-workflow experiment. The answer remains a hypothesis to test, not an established result.
