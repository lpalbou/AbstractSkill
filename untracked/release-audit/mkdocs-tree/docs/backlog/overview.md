# AbstractSkill backlog — overview

Plain-language summary: `abstractskill` is the Agent Skills (SKILL.md) contract
library for AbstractFramework (parse, validate, hash, discover, compose). The
2026-07-11 maintainer directive extends its role to SKILL TRUST: a system of
validated skills, a do-not-use advisory registry, and (join-or-build) a network
of trust for skills, with automated periodic reviews.

## Counts

- Planned: 5 (0001-0005)
- Proposed: 2 (0006-0007)
- Completed: 0
- Deprecated: 0
- Recurrent: 1 (advisory/validation registry review)

## Priority / next recommended work

1. 0003 simulated-execution audit harness — DESIGN done; implementation awaits runtime/agency lanes (upgrades the adopted shelf skills to audited, mints the first specific advisories).
2. 0004 trust-network LEVERAGE step (backlog 0006) — consume external findings as advisory inputs with provenance.
3. Consumer wiring — nothing consumes `evaluate_trust` yet (gateway console Phase 4 is the first consumer; contracts are ready).

Contract/registry/shelf/research/docs (0001/0002/0004/0005) shipped this
session with 68 tests; 0003 is design-only by scope.

## Planned items

| ID | Item | State |
|----|------|-------|
| 0001 | `planned/trust/0001_trust_contract_layer.md` | Contract shipped (68 tests) |
| 0002 | `planned/trust/0002_advisory_registry.md` | Mechanism shipped; registry empty (guidance carries class notices) until an audit/feed names a skill |
| 0003 | `planned/trust/0003_simulated_execution_audit_harness.md` | Design done; execution awaits runtime/agency lanes |
| 0004 | `planned/trust/0004_trust_network_research.md` | Position shipped (docs/trust-network-position.md) |
| 0005 | `planned/trust/0005_first_party_shelf.md` | Shelf shipped (3 skills, hash-pinned) |

Topic track: `planned/trust/README.md` (the skill-trust track, maintainer
directive 2026-07-11).

## Proposed items

| ID | Item | Promotion criteria |
|----|------|--------------------|
| 0006 | `proposed/0006_automated_periodic_reviews.md` | Trust contract shipped + a scheduling host (gateway or CI) identified |
| 0007 | `proposed/0007_admission_lint.md` | Phase-4 (entity-creation plan) opens; lint patterns validated against real advisories |

## Completed ledger

(empty — first entries land when 0001/0002/0005 close with evidence)

## Deprecated

(none)

## Recurrent

- `recurrent/advisory-registry-review.md` — periodic re-verification of
  advisory/validation entries against upstream sources.

## Process notes

- Item IDs are four-digit and global across all lifecycle directories.
- Completion appends a `## Completion report` before the move to `completed/`.
- Standing seat rules apply to every item: 1+ fable5 adversarial subagent per
  development, no commits without the maintainer's word, `#FALLBACK`-labeled
  degradations only.
- 2026-07-11: backlog created (maintainer directive: validated-skills system,
  advisory registry, trust network, methodology skill, coredoc/backlog
  integration).
- 2026-07-11: cycle 1 shipped 0001/0002/0005 core; cycle 2 folded a fable5
  adversarial pass (class-advisory P0 → guidance split; graded severity;
  fail-closed verdict; adopted level; hash/format hardening) and wrote the
  0004 trust-network position; cycle 3 applied the coredoc doc set (README,
  docs/*, architecture diagrams, llms.txt/llms-full.txt, SECURITY). 63 tests
  green. 0003 remains design-only (execution awaits runtime/agency lanes).
