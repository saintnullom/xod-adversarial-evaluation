# Contributing to XOD

XOD is currently a working local prototype. Contributions that improve clarity, reproducibility, tests, or bounded reasoning workflows are welcome after a maintainer chooses to open the repository for collaboration.

## Before proposing a change

- Keep changes small, inspectable, and covered by an appropriate test where practical.
- Do not add API keys, `.env` files, local databases, private conversations, or sensitive screenshots.
- Do not present engineering checks as scientific validation or imply production readiness.
- Preserve the human-in-the-loop boundary: XOD supports structured review; it does not guarantee research integrity or trustworthy AI.

## Reporting issues

Provide a minimal synthetic reproduction, expected behavior, observed behavior, and environment details that do not reveal credentials or private data. For a potential security issue, do not publish exploit details in a public issue; contact the maintainer privately once a public contact channel is defined.

## Verification

For changes that affect application behavior, run the documented backend tests, frontend regression tests, frontend typecheck, and frontend production build when the local environment supports them.
