# XOD specialist reasoning evaluation protocol

## Decision question

Does a specialist configuration improve XOD's measured reasoning quality enough to justify a bounded pilot, after its cost and latency overhead are counted?

## Fixed comparison

For each of the eight cases in `EVALUATION.md`, run:

1. the current single Tribunal baseline;
2. the candidate specialist configuration;
3. the same human scoring rubric for expected behavior, evidence discipline, falsifiability, and non-reflexive criticism.

Record quality from 0 to 4, actual request cost in USD, and elapsed latency in milliseconds. Do not use a specialist configuration to grade itself.

## Gate

`ELIGIBLE_FOR_PILOT` requires complete coverage, a mean quality lift of at least 0.25, zero per-case quality regressions, cost at or below 2.00x baseline, and latency at or below 2.50x baseline. Otherwise the decision is `INSUFFICIENT_EVIDENCE` or `HOLD`.

An eligible result authorizes only a small, observable pilot. It does not authorize a permanent multi-agent architecture, background calls, or changes to the existing Tribunal contract.
