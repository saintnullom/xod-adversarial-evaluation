# Roadmap

## Current position

The working local prototype provides structured adversarial reasoning, a local belief ledger, manual relationship records, internal engineering evaluation cases, and provider observability. This roadmap does not claim that later work is funded, implemented, or validated.

## Near-term hardening

- Preserve the local test baseline and add regression coverage as bugs are found.
- Improve documentation, demo reproducibility, and review of public-release boundaries.
- Conduct a human security and privacy review before any public release.

## Proposed Catalyst-scoped research workflow

- Define research-specific claim, evidence, uncertainty, and reviewer-rationale records.
- Implement claim extraction and source-to-claim evidence mapping.
- Add support checking, contradiction search, alternative explanation prompts, and calibrated escalation.
- Implement the proposed status vocabulary: SUPPORTED, UNDERTESTED, CONTRADICTED, INSUFFICIENT EVIDENCE, and HUMAN REVIEW REQUIRED.
- Build an auditable, human-in-the-loop review record and evaluate it against an independent rubric.
- Explore Zotero integration only as a proposed, separately governed integration.

## Explicit non-deliveries today

Graph visualization, autonomous confidence changes, external benchmark validation, production deployment, and paying-user validation do not exist. Specialist-agent execution does not exist, even though specialist readiness is represented in the current architecture.

## Decision gates

1. Review local documentation, secrets hygiene, dependency posture, and license choice before publication.
2. Define evaluation materials and human-review protocol before reporting research-workflow outcomes.
3. Establish privacy, governance, and deployment decisions before connecting external systems or operating beyond a local prototype.
