# Planned: Trust contract layer (validation records + trust evaluation)

## Metadata
- Created: 2026-07-11
- Status: Planned (in progress)
- Completed: N/A

## ADR status
- Governing ADRs: None
- ADR impact: None (contract decisions recorded in docs/KnowledgeBase.md)

## Context
Maintainer directive 2026-07-11: "abstractframework with abstractskill must
create a system of validated skills. either those that we would create
ourselves for specific tasks, or those that would pass internal security
audits with various LLMs". Consumers: the gateway entity-creation console
(Phase 4 skills picker needs trust badges), the runtime activation path, and
operators browsing the registry.

## Current code reality
`abstractskill` ships parse/validate/hash (document + whole-tree)/discover/
compose (`effective_tools`). There is NO trust vocabulary: nothing represents
"validated", "audited", "advisory", or verification outcomes. `skills.yaml`
(home attachment manifest, gateway lane) carries (source, name, tree_hash)
per the c548/c549 answers — verification exists, trust classification does not.

## Problem
Without a shared trust contract, every surface (console, runtime, door) will
invent its own "is this skill safe?" logic — the exact per-consumer fork the
one-helper rule (effective_tools) exists to prevent, on a higher-stakes axis.

## What we want to do
One `trust` module owning: trust levels (first-party / audited / community /
unverified / advisory), a `ValidationRecord` (who validated what tree-hash,
how, when, with what evidence), an `AdvisoryEntry` (see 0002), a
`TrustRegistry` file format (YAML at rest, hash-keyed), and ONE
`evaluate_trust(inventory|tree_hash, registry)` verdict function every
surface calls.

## Requirements
- Trust binds to the TREE HASH, never the name (a name is claimable; bytes are not).
- A skill whose hash matches an advisory is DO-NOT-USE regardless of any validation record (advisory wins ties; there are no silent overrides).
- A validation record for hash H says nothing about hash H' (any byte change voids trust — re-validate).
- Advisory entries carry the four mandated fields: official intent, hidden issue, severity, reference link.
- Verdicts are explainable: the verdict names the record(s) it rests on.
- Registry files are human-readable YAML, diffable, and loadable without the network.

## Scope
Data model + registry IO + verdict function + tests.

## Non-goals
- No enforcement (consumers enforce; the library informs).
- No network fetch of registries (distribution is gateway/CI lane).
- No signature/PKI in v1 (hash pinning + curated distribution first; signatures are a 0006-adjacent follow-up).

## Dependencies and related tasks
0002 (advisory registry rides the same module), 0005 (first-party shelf produces the first validation records), gateway Phase 4.

## Expected outcomes
`from abstractskill import evaluate_trust, TrustRegistry, ValidationRecord, AdvisoryEntry, TrustLevel` usable by console/runtime/door with one semantics.

## Validation
Unit tests: verdict precedence (advisory > validation > unverified), hash-mismatch voiding, registry round-trip, unknown-severity refusal.

## Progress checklist
- [x] Design (this item)
- [x] `trust.py` module + exports (TrustLevel incl. ADOPTED + BLOCKED verdict, ValidationRecord, AdvisoryEntry, GuidanceEntry, TrustRegistry, evaluate_trust)
- [x] Fail-closed verdict (blocked / requires_review / attachable; UNVERIFIED and scripts-present require review) — adversary P1
- [x] Method→max-level cap (adoption can't claim first_party) — adversary P1
- [x] Hash-format + non-empty-provenance validation, scalar-item + duplicate-id refusal — adversary P1/P2
- [x] Tests (test_trust.py, 24 cases)
- [x] First fable5 adversarial review folded (cycle 2)
