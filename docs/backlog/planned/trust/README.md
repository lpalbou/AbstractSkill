# Skill-trust backlog track

## Status
Planned (0001/0002/0004/0005 in progress this session; 0003 design-first)

## Purpose
Execute the 2026-07-11 maintainer directive: AbstractFramework, through
abstractskill, must provide a system of VALIDATED skills (first-party or
security-audited), maintain a DO-NOT-USE advisory registry with mandated
fields (official intent / hidden issue / severity / reference link), and
evaluate joining an existing skill trust network or becoming one — including
automated periodic reviews. Context: measured 2026 skill-registry malware
rates (Snyk ToxicSkills: 36.8% flawed, 13.4% critical) and the entity-specific
risk that a persona-steering skill body gets engrammed into an append-only
life.

## Items
- `0001_trust_contract_layer.md`: validation records + trust evaluation (the code contract every surface calls).
- `0002_advisory_registry.md`: the do-not-use registry contract + seed entries.
- `0003_simulated_execution_audit_harness.md`: epoch-based simulated-execution audits (false tools, sandbox, 10/100 epochs, multiple LLMs).
- `0004_trust_network_research.md`: join / leverage / build position on skill trust networks.
- `0005_first_party_shelf.md`: curated first-party skills (adversarial-iteration, coredoc, backlog) validated and hash-pinned.

## Reading order
0001 → 0002 → 0005 → 0004 → 0003.

## Governing ADRs
None identified after review (this repo has no ADR system yet; the trust
contract decisions are recorded in docs/KnowledgeBase.md and will move to
ADRs if the repo adopts them).

## Scope
Library contracts, registry data formats, curation, research, methodology.

## Non-goals
- No marketplace/URL install path (curated-only per the entity-creation plan v1 cut).
- No runtime activation handlers (abstractruntime's lane) or gateway routes (gateway's lane) — contracts only.
- Advisory registry never auto-blocks outside consumers' explicit checks; it informs the gate that enforces.

## Notes for future agents
The multi-agent consensus surface is the commons channel (agora); the
entity-creation-console plan (commons fs `plans/entity-creation-console-plan.md`)
carries Phase 4 (skills) which consumes 0001/0002/0005.

### Adversary-B follow-ups (gateway report `reports/skills-admission-adversary-b.md`, 2026-07-11)
Folded this session: F1 method-caps-level (done), F2 activation_description
now consumed by `format_available_skills_xml` + `registry.activation_descriptions()`
(done), F5 ASG-2026-0003 reference corrected to the source containing the
26k-users claim (done), trust-network-position corrections (Haldir keyless /
STSS Merkle / OMS / whole-tree>content_hash — done).

Queued (larger, tracked here so they are not lost):
- 0002: do-not-use entries should grow `tree_hashes` (plural, variant
  families), IOCs (domains/accounts), entity-specific remediation (an
  engrammed poisoned procedure is closed by counter-evidence reflection, not
  deletion), `discovered_by`/disclosure timeline/`superseded_by`, and a
  SIGNED static feed (ed25519, pubkey pinned in-repo) with an offline copy;
  evidence standard for public naming = published link OR reproducible finding
  OR two independent confirmations.
- 0003: the epoch battery is a GRID (intent×adversarial-probe×model×sampling),
  two-arm (skill vs no-skill control, score the delta), canaries in tool
  RESULTS, judge-fencing; the `audited` evidence schema needs
  `harness_version`/`battery_hash`/models/epochs/sampling/arms/findings.
- 0007: admission should inventory `references_skills` (cross-skill name
  references are trust-forwarding/squatting edges) and name `foreign_files`
  (e.g. `agents/openai.yaml`) so a console states "carries config for another
  harness; never interpreted here"; add provenance/license fields (fix
  upstream → re-vendor → re-hash, never relax the validator).
- Cross-repo (gateway lane): the verdict MUST be wired fail-closed at the
  gateway attach door (recompute the tree hash from actual bytes, enforce
  attachable-only for entity sessions) — a registry not consulted at attach
  time is decoration. The honest-limits contract must travel with every badge;
  never render the word "safe".
