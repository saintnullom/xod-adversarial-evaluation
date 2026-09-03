# Research Integrity Workflow

## Status: PROPOSED / CATALYST-SCOPED WORK

The Research Integrity Agent is not implemented for research workflows. This document describes a proposed Catalyst-funded development path, not a current product capability and not a guarantee of research integrity or trustworthy AI.

## Conceptual workflow

AI-assisted synthesis → claim extraction → evidence mapping → support checking → contradiction search → alternative explanation testing → adversarial challenge → uncertainty/status classification → SUPPORTED / UNDERTESTED / CONTRADICTED / INSUFFICIENT EVIDENCE / HUMAN REVIEW REQUIRED → human decision → auditable record

## Implementation boundary

| Workflow step | Existing XOD architecture conceptually supports it | Not implemented for research workflows | Intended Catalyst-funded development |
| --- | --- | --- | --- |
| AI-assisted synthesis | Provider-backed SPAR and Tribunal conversations | Research-specific synthesis controls | Yes |
| Claim extraction | Structured claims can be recorded as beliefs | Automated extraction from papers or notes | Yes |
| Evidence mapping | Manual evidence records and belief versions | Source-to-claim mapping | Yes |
| Support checking | Objections and manual review patterns | Citation/support assessment | Yes |
| Contradiction search | Adversarial questioning and evidence updates | Corpus or literature contradiction search | Yes |
| Alternative explanation testing | Tribunal-style objections and assumptions | Research-method-specific alternatives | Yes |
| Adversarial challenge | SPAR and Tribunal reasoning flows | Calibrated research-domain challenge policies | Yes |
| Uncertainty/status classification | User confidence and version history | Research-specific status classification | Yes |
| Human decision | User-visible review and manual updates | Research-review interface and protocols | Yes |
| Auditable record | Local persistent ledger and event records | Research-ready provenance export | Yes |

## Intended statuses

The proposed research workflow would use the following reviewer-facing statuses: **SUPPORTED**, **UNDERTESTED**, **CONTRADICTED**, **INSUFFICIENT EVIDENCE**, and **HUMAN REVIEW REQUIRED**. These are not yet automated research classifications.

## Proposed integrations and safeguards

Zotero integration is **PROPOSED**. No external literature-system integration is currently implemented. Any future integration should minimize retained source content, preserve source references and reviewer decisions, keep credentials server-side, and require explicit human review before a consequential conclusion is used.

## Falsifiable development question

Can a structured, adversarial, human-in-the-loop workflow help reviewers surface support gaps and uncertainty without creating unacceptable false positives, missed issues, or inappropriate belief revisions? The answer requires the planned evaluation; it is not known yet.
