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
- No marketplace/URL install path (curated-only per the entity-creation plan
  v1 cut). AMENDED 2026-07-11 (operator directive): curated vendoring exists
  now (`registry/catalog.yaml` + `scripts/vendor_skill.py` — pinned commits,
  whole-tree hashes, owner/repo slugs only, no URL argument anywhere); the
  excluded thing remains marketplace sync / arbitrary-URL installs.
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

### Source-derivation adversary residuals (2026-07-11, deferred nits)
From the fable5 review of the registry source-derivation wave (all must-fix
findings folded same-day; these are the recorded deferrals):
- DONE (same day, second fable5 wave): case policy — names normalize to spec
  lowercase at construction + every query boundary (match-widening,
  fail-closed); query-side sources stripped symmetrically (padded caller
  source no longer fails open).
- DONE (same day, second fable5 wave): `lint_registry` — inert advisory
  spellings surface at refresh time (spec-invalid/over-long names, case-only
  source mismatches with all twins named, unknown sources with one aggregate
  note for advisories-only feeds); wired into refresh_shelf.py, which now
  validates records before writing; shipped registry lints clean by test.
- `DerivedSource.binding` as an enum (two in-repo string literals today,
  test-pinned).
- Maintainer-skills wave residuals (adversary-A, 2026-07-11 evening): (a)
  codex-skills vendored copies have no machine anchor to their upstream
  (record the source commit/copy-hash in notes, or fold them into the
  catalog/vendor pipeline); (b) `agents/openai.yaml` foreign files now ship
  in 7 shelf skills — promote 0007's `foreign_files` evidence field; (c)
  adr's reader-first reference cites author-local example ADRs (upstream
  wording tweak recommended, not seat-owned).
- `vendor_skill.py --pin` (adversary-C usability suggestion, deferred): write
  expected_tree_hash + vendored:true into catalog.yaml automatically after
  the human diff review. Needs a comment-preserving YAML writer (the catalog
  is comment-rich; PyYAML round-trips destroy them). Until then: the script
  prints the exact lines and test_vendored_catalog_pins_match_shelf_bytes
  catches any transcription error in CI.
- `TrustRegistry.activation_descriptions()` is registry-wide (not
  hash-filtered) — documented, prompt-display-only; consider a hash-aware
  variant if a consumer beyond the selection pipeline appears.
- Observability nit: a skill that is BOTH advisory-blocked and tree-broken
  reports as `missing`, not `blocked` (fail-closed either way; audit greps
  keyed on `blocked` won't see it).
- Multi-root wave residuals (fable5, 2026-07-12; the loud-note + decode-fix
  halves shipped same-pass): (a) hash-pinned enables — `enabled` entries as
  `name@tree_hash` (or a mapping) so an enable attests BYTES, not a
  claimable name; the durable fix for the standing-enable-activates-shadow
  path (today: loud note naming the winning copy). (b) load→inspect byte
  cross-check — compare the parsed SKILL.md against the hashed inventory's
  per-file digest to close the intra-call TOCTOU window on user-writable
  roots. (c) held/blocked entries carry (name, verdict) without the winning
  copy's path; surface `root_dir` so the operator knows WHICH copy they
  would be enabling (partially covered by the enable note).
  ALL THREE DONE 2026-07-13 (idle-conversion dispatch; fable5-reviewed,
  findings folded same-pass): (a) as `name@tree_hash` string entries,
  fail-closed parse, pins-govern, scalar/None grant-surface type guards;
  (b) via `LoadedSkill.skill_md_sha256` vs the single-walk inventory's
  per-file digest, plus `read_skill_resource(expected_sha256=)` for the
  post-verdict half; (c) as `SkillSelection.resolved_paths` +
  `resolved_tree_hashes`.
- 2026-07-13 adversary deferrals (recorded, not blocking): (i) the
  cross-check silently skips when `LoadedSkill.skill_md_sha256` is None —
  impossible via the pipeline's own loader today; refuse None outright if
  the loader ever becomes injectable. (ii) a skill ROOT that is itself a
  symlink hashes through (children are symlink-refused; pre-existing) —
  trust still binds to bytes, no verdict bypass, but the tamper-hash
  docstring overpromises. (iii) inventory (digest, size) pairs are not
  atomic under a concurrent writer (size stat'ed after digest read) —
  nothing trusts size; comment added in tree.py.
- 2026-07-13 production-readiness wave (whole-package fable5, no P0/P1;
  five P2s folded same cycle — see CHANGELOG): remaining P3 notes on the
  record: (i) `read_skill_resource` without `expected_sha256` can read a
  file grown after its stat (documented honest limit; attestation covers
  it); (ii) `parse_skill_md` coerces non-string frontmatter scalars via
  str() (spec validation still applies); (iii) the graph-as-control test
  skips on standalone checkouts (no ../abstractentity) — the self-contained
  content pin is the floor there; consider vendoring a copy of the artifact
  if the repo ever ships independently.
