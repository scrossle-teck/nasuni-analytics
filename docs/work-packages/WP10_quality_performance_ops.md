# WP10 — Quality, performance, and operations

## Goal

Harden the system so it stays correct, explainable, and performant as scale and complexity increase.

## Outcomes

- A reliable developer workflow (tests, typing, linting).
- Confidence in correctness (fixtures, regression tests).
- Operational discipline (repeatable runs, manifests, clear failures).

## Deliverables

- Test strategy and coverage targets:
  - unit tests for canonicalization + fingerprinting
  - unit tests for identity closure
  - rule fixture tests
  - effective-access fixture tests
- Performance baselines:
  - ingest time
  - rule run time
  - closure time
  - effective-access query time
- CI automation:
  - run `pytest`, `pyright`
  - optional style checks
- Operational docs:
  - how to run an end-to-end pipeline
  - how to interpret outputs
  - how to troubleshoot missing data / schema issues

## Non-goals

- Building a UI or API (unless explicitly scoped later).

## Dependencies

- All prior packages inform this one; it can start early for scaffolding.

## Acceptance criteria

- A new machine can run:
  - ingestion
  - rules
  - at least one effective-access query
- Failures are explicit and include actionable messages.

## Suggested timeline

- Ongoing, but expect:
  - 2–3 days to add fixtures and baseline tests across identity + ACL logic
  - 1–2 days to establish performance baselines and document tuning

## Implementation notes

### Regression fixtures

Maintain small, synthetic datasets that cover:

- nested group cycles
- deny precedence
- inheritance
- broad principals

### Traceability

Ensure every finding can point to:

- run_id
- identity snapshot
- source records/ACE evidence

### Avoid hidden coupling

Keep schema/contract changes deliberate:

- version bumps
- changelog entries
