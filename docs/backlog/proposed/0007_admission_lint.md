# Proposed: Registry-admission lint (identity-directive / injection tripwire)

## Metadata
- Created: 2026-07-11
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: None
- ADR impact: None

## Context
Committed in the c549 answer to gateway (skill open-question 5): an opt-in
lint at registry admission that flags identity-directive and prompt-injection
patterns in skill bodies. Honestly a tripwire, not a guarantee.

## Current code reality
`validate_skill_name`/`validate_description` enforce spec constraints; there
is no content lint. Gateway's research explicitly notes description-only
framing biases agents toward adversarial variants and evades moderation
36.5-100% — scanners are defeatable.

## Problem or opportunity
A cheap first filter at admission catches obvious identity-steering ("you are
now...", "ignore previous instructions", persona reassignment) before a skill
enters the shelf, without pretending to be a security boundary.

## Proposed direction
`lint_skill_body(document) -> findings` (opt-in), pattern + heuristic based,
findings advisory-only; feeds the human admission review, never auto-blocks.

## Why it might matter
Raises the floor at the cheapest point; complements 0003's expensive behavioral audit.

## Promotion criteria
Phase 4 (entity-creation) opens AND patterns validated against real advisory bodies (0002 seed) to bound false positives.

## Validation ideas
Precision/recall against the advisory seed + a clean first-party corpus (must not flag coredoc/backlog).

## Non-goals
Not a security guarantee; never the sole gate.

## Guidance for future agents
Keep it advisory; semantic evasion beats it by design — pair with 0003 and human review.
