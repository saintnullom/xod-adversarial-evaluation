# Limitations

## Scope limitations

XOD is a working local prototype, not a production-ready research platform. It does not provide production deployment, service-level guarantees, external benchmark validation, or paying-user validation.

## Reasoning limitations

- Model-generated language can be incomplete, incorrect, biased, or poorly calibrated.
- An objection is not evidence, and a structured record is not proof of a conclusion.
- Human users can enter incomplete evidence, ambiguous claims, or inappropriate confidence values.
- The current prototype does not autonomously change confidence; human judgment remains necessary.
- The current prototype has no graph visualization, even though manually recorded relationships exist.

## Research-workflow limitations

The Research Integrity Agent is PROPOSED / CATALYST-SCOPED WORK, not an implemented research workflow. XOD does not yet perform automated claim extraction from research materials, evidence mapping, citation support checking, contradiction search across a corpus, or research-specific status classification. Zotero integration is PROPOSED only.

## Evaluation limitations

The local 29/29 backend tests, 3/3 frontend regression tests, typecheck, and production build are engineering checks. They do not establish scientific validity, real-world accuracy, safety, trustworthy AI, or effectiveness for research review. Internal evaluation cases are not an external benchmark.

## Data and privacy limitations

XOD is local-first, but local operation does not eliminate privacy or governance responsibilities. A configured provider may receive the material submitted to that provider according to its service terms and the deployment configuration. Provider observability intentionally avoids storing prompt or response content in its operational failure records, but users remain responsible for deciding what information to submit.

## Appropriate use

Use XOD as a structured prompt for human review, not as a substitute for domain expertise, source verification, ethics review, legal advice, medical advice, or a final research-integrity determination.
