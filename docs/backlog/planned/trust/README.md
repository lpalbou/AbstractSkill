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
- 2026-07-13 consumer-path audit (operator "I see none" incident; fable5
  consumer-view adversary): folded same-day — README "Where the skills
  live" section with the abstractcode env wiring, pip-delivers-library-only
  honesty note, `.gitattributes * -text` (EOL rewrites would degrade every
  byte pin on Windows clones). DEFERRED, needs a deliberate decision:
  (a) packaging `registry/` as wheel data + a `shelf_path()` accessor (a
  pip-installed shelf must stay byte-verifiable against the repo's
  records — decide the verification story before shipping bytes in a
  wheel); (b) fleet seats currently run with an EMPTY trust registry
  (abstractcode's env sanitation strips ABSTRACTCODE_SKILLS_*, no config
  keys exist for registry paths, isolated HOMEs) — the env lines per seat
  are the c1609 one-liner, config-file keys are the durable fix
  (abstractcode's lane, cross-seat); (c) `guidance.yaml` never reaches the
  CLI consumer (informational only; abstractcode's lane).
- 2026-07-13 feedback canvass (c1676) consolidation — shipped: backlog
  discovery-first + coredoc same-change invariant (c1712; fable5-reviewed,
  re-pinned, pushed). BATCHED, one re-pin when gateway's ask-1 drift check
  lands (post-doctoring): (a) audience-scope the diary teachings in
  abstractframework-gateway + entity-self-knowledge (observer c1698: the
  "redacted or gist-limited" claim is watcher-audience truth; the
  authenticated operator's door serves book words marker-first per the
  07-08 ruling — teach by audience, identity-adjacent wording gets fable5
  + memory co-sign); (b) generalize the prose-claims teaching to "never
  derive ANY claim from reply prose when a structured source exists".
  QUEUED on runtime driver wiring (memory c1687 names skill in the ship
  note + co-signs wording): familiarity()/commitments/```tend teach-in
  for entity-self-knowledge.   QUEUED for the agora-collaboration bench
  freeze (laurent c1724, agorahub 0.9.0 — additive, so the draft's
  hub-wins hedge holds and nothing is stale): the mechanics layer can
  gain protocol-string pinning (GET /healthz, docs/protocol.md bump
  policy), closure-from-the-wire (has_resolved_reply on envelopes), and
  transcript verifiability (GET /channels/{c}/ledger + the stdlib
  verify_ledger.py recomputes the chain without trusting the hub — the
  "somewhere there must be a book" principle now has a teachable
  verification affordance). Folds with agora/laurent co-sign at the
  freeze, not before.   SAME QUEUE, from the lurker-feedback disposal
  (designer c1756): per-ask addressing (asks gain optional per-ask `to`;
  to_me fires for seats named in any ask) is ACCEPTED, and check_inbox
  gains an explicit owed section (asks awaiting your answer + answers
  awaiting your consumption) — when these ship, the draft's name-scan
  and consume-visibly teachings re-scope from client-discipline to
  hub-mechanism (the designer's line: the client triad "becomes
  redundant only where the hub makes the miss impossible"). The draft
  is also a named red-team target ("ACT is the first verb, not ack") —
  fold findings when they land.
- 2026-07-14 c1600 asks ANSWERED by the designer (c1764) — the draft's
  adoption shape is RULED: ADOPT + CO-AUTHOR. Prior art exists and is
  first-party: skill/SKILL.md in the AgoraHub repo
  (github.com/lpalbou/AgoraHub, main — the full etiquette the workspace
  rules reference, updated tonight with the lurker lessons; fetched and
  reviewed: envelope-triage order with unforgeable-signals teaching,
  digest-first-after-a-gap, resolved-as-reply-to-own-message closure
  mechanics, channel language modes, store/claim/decision norms, loop
  hygiene, reception boundaries). RE-DERIVATION PLAN: derive the shelf
  skill from BOTH sources hash-pinned at derivation time (AgoraHub
  skill/SKILL.md + the operator's guidance doc — the existing
  derived_from contract extends to two sources); discipline discoveries
  keep flowing doc-first.   TIMING: wait for the anti-lurk mechanics to
  land (~a day) — the designer holds the co-sign until the post-change
  contract precisely so the skill never engraves semantics that shift
  this week; the hub-wins clause covers the gap. Do NOT re-derive
  against the pre-change upstream.
- 2026-07-14 the post-change contract is now DEFINED (operator DM,
  debrief consumed — all three skill-seat frictions shipped fixes):
  envelopes carry `redelivery=true` (read pins re-surface
  headline-only), `your_pending_asks` + `YOURS:<ids>` per-seat debt
  scoping (stale to-you drops when YOUR ask discharges), per-ask `to`,
  and debt-scoped `--important-only` wakes. Lands at next hub restart;
  the operator's words: "the co-sign for your shelf skill can proceed
  against this contract."   RE-DERIVATION CHECKLIST when the restarted
  hub serves it: (1) fetch the updated AgoraHub skill/SKILL.md and
  hash-pin it + the guidance doc as the two derivation sources;
  (2) re-teach the reception/name-scan/consume-visibly rules against
  the new mechanics (client triad demotes where the hub makes the miss
  impossible — keep the portable posture, drop the workaround
  framing); (3) fable5 + operator co-sign; (4) hand agency the frozen
  tree for the bench. Seat-side follow-up: the watcher can simplify to
  debt-scoped --important-only wakes once the hub restarts (rule edit
  in .cursor/rules/skill-seat.mdc rides the same boundary).
- 2026-07-14 ~03:00 the RESTART LANDED: hub 0.10.0 serves the post-change
  contract LIVE (verified first-hand this session: hub_rules v0 teach
  per-ask `to` + asker-consumption debts + resolved-closes-everywhere;
  check_inbox leads with a YOU-OWE section; the listen wake carries
  owed counts). Re-derivation checklist step 1 executed: upstream
  AgoraHub skill/SKILL.md fetched @ sha256
  8d134d3221035400ac08778a55f64dab70c55b2b290df3b4934cb17e69728790
  (12,493 bytes, 2026-07-14) — this is the derivation-source snapshot
  the re-derived skill's frontmatter pins alongside the guidance doc.
  Steps 2-3 (re-teach + fable5 + co-sign) are the next act; the c1889
  thread closure + c1905 readiness note record the queue publicly.
  EXECUTED 2026-07-14 ~05:55 (commit 23132dc, receipt c2124): v1
  re-derived — hub-mechanics layer adopts the upstream at the live
  0.10.0 contract (owed-first, per-ask to, answer-AND-do, consumption
  debts, resolved-closes, debt-scoped arms); NEW Initiative section per
  the operator standing order (c2083: claimed-item-always, receipts,
  idle wakes, "nothing worth doing" said); ledger AND mechanics detail
  to references/ (progressive disclosure; ledger rows carry receipt
  pointers). Fable5: 2 P0s (size regression vs the bench finding;
  owed-block-first INVERTED — listed last where upstream teaches rule
  zero) + 7 P1s (invented watcher-kill hazard → own-terminals-only;
  claim-or-decline scope drift; reply-chain reads restored; roll-call
  vs blind-poll counting corrected; verbatim quote fixed; vote
  mechanics at full fidelity in reference; delegations hedged) — all
  folded. Body 12,275 B ≈ 3.1k tokens (18% under the pre-relocation
  draft, ~3% over v0 — two new load-bearing sections; stated honestly
  in the receipt).   Tree v1 = 366d7d286b62c382…; co-sign requested from
  the designer (c2124 ask 1). PROMOTION SEQUENCE agreed with agency
  (c2126): co-sign lands → ping agency → bench re-run against the
  CO-SIGNED tree same-hour (if the designer reshapes, the re-run waits
  for the reshaped tree — never bench bytes that won't ship) → shelf
  promotion with the validation record citing the v1 run as promotion
  evidence and c1833 as the design-input bench (the context-cost
  finding's origin).
- 2026-07-14 BENCH VERDICT (agency c1833, artifacts at
  plan_proof_out/promoted-skill-bench-20260714T024214Z/): the with-skill
  arm PASSES 8/9 through the promoted bridge, MATCHING the without-skill
  arm; all 3 seats self-attested the frozen tree (159e45fa…,
  gate-enforced); provenance honestly recorded as ENABLE class. This is
  the behavioral evidence the promotion's validation record will cite.
  Promotion itself still lands as ONE act with the re-derivation +
  operator co-sign (post-hub-restart) — bench pass banked, not
  self-promoting. RE-DERIVATION INPUT from the bench (agency finding 2,
  skill's lane): the ~11.5KB/~2.9k-token body is real context pressure
  on small-context substrates (a 4b seat hit context-exceeded 6×/seat;
  cost = one lost ballot, gracefully absorbed). Fix shape at
  re-derivation: PROGRESSIVE DISCLOSURE — the failure ledger (~435
  tokens, teaches WHY rules exist; audit value, not activation-time
  load-bearing) moves to references/failure-ledger.md loaded on demand;
  further slimming falls out naturally where the post-change hub
  mechanics demote client-triad teachings. Never slim by deleting
  teachings (ADR-0026 lossless spirit): relocate to references, keep
  the body's rules intact. MAP (no fold): abstractflow-authoring skill
  candidate (flow c1681 — their docs are source of truth, flow co-signs,
  ADR-0026 lossless-compaction applies); agent's skills-attachment
  contract (c1682: `_runtime.skills_block` named slot never
  system_prompt_extra, byte-stable for the run, narrow allowed_tools in
  the same move, no delegate propagation) is the teaching source when an
  attachment lane opens. NO-DRIFT verified by grep: no shelf skill states
  a tool-round cap (runtime's ≤3 change safe) or tool-name wire behavior
  (core's aliasing safe); cicd current as of 07-12.
