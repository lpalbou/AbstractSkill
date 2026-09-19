# Architect Skill Memory

Use this file as compact shared memory for the `architect` skill. Read it when
working on ownership, boundaries, contract design, or platform migration.
Update it only during skill-maintenance work.

## Distilled Principles

- Record important decisions with context and consequences.
  Source: Martin Fowler on ADRs.
  https://martinfowler.com/bliki/ArchitectureDecisionRecord.html
- Boundaries are language and ownership boundaries, not just file-layout
  choices. Be explicit about interrelationships.
  Source: Martin Fowler on bounded contexts.
  https://martinfowler.com/bliki/BoundedContext.html
- Operability is architecture. Recovery, monitoring, and support burden belong
  in design comparisons.
  Source: AWS Well-Architected and Google SRE.
  https://docs.aws.amazon.com/wellarchitected/latest/framework/operational-excellence.html
  https://sre.google/sre-book/monitoring-distributed-systems/

## Durable Lessons

- If two alternatives share the same authority model, they are probably the
  same design with different words.
- If the user-facing distinction is unclear, the architecture boundary is
  probably not ready to ship.
- Reversible designs deserve explicit credit, but only when they do not defer
  core ambiguity onto users or operators.
- Architecture discussion is incomplete if nobody argues for the smallest
  acceptable change.
- Premises decay while discussions run. Verify each load-bearing premise
  against the current tree/running state before arguing from it — the most
  expensive architecture failures observed were designs argued from files,
  defaults, or wiring that no longer existed (or never had).
  Source: field observation, 2026-07 — a multi-agent platform plan argued
  from a per-directory store file that turned out to be a zero-byte orphan;
  three independent reviewers falsified the premise from the code.
- Names engrave. Any vocabulary that reaches append-only or at-rest state is
  effectively irreversible: renames become alias/migration cycles with loud
  shims and die-before-release discipline. Decide spellings BEFORE the first
  real write; never mint a second name for one concept to route around an
  implementation flaw (fix the contract instead).
  Source: field observation, 2026-07 — renames of engraved lifecycle
  vocabulary forced alias/shim migration cycles; a second name minted to
  route around a writer flaw had to be retracted the same day.
