# Changelog

All notable changes to this package are documented in this file.

## [Unreleased]

### Fixed

- Parser accepts CRLF/CR line endings (Windows-authored skills were rejected by an
  LF-only frontmatter gate); frontmatter delimiters must now sit at column 0, so an
  indented `---` inside YAML block scalars no longer closes the frontmatter early.
- Skill name validation enforces the full Agent Skills spec: consecutive hyphens
  (`pdf--processing`) are rejected; description (max 1024) and compatibility
  (max 500) ceilings are enforced (`validate_description`, `validate_compatibility`).
- `FilesystemSkillLoader.load()` now resolves exactly like `discover()`: a broken
  higher-precedence copy no longer shadows a valid lower-precedence skill (the skill
  a host lists is always the skill it can load), and when only broken copies exist
  the parse error is raised instead of a misleading "not found".
- `load()` validates the requested name before touching the filesystem, rejecting
  separator/traversal-shaped names.

### Added

- Loud degradation: `discover()`/`load()` log `#FALLBACK`-labeled warnings for
  invalid skill folders (optional `on_warning` callback for hosts that surface
  warnings themselves) instead of silently skipping them.
- `tree` module: `hash_skill_tree` (deterministic whole-tree sha256 over raw file
  bytes with a length-prefixed binary manifest — injective by construction, so
  newline-bearing filenames cannot forge collisions; streaming digests; OS junk
  excluded; symlinks refused loudly — vendored-copy tamper detection),
  `inspect_skill_dir` (structural inventory incl. the `has_scripts` fact for honest
  "requires enablement" badges), and `read_skill_resource` (in-tree resource reads
  with honest oversize refusal, traversal/symlink refusal). Hash canonicalization
  is raw bytes deliberately: hash = bytes, parse = meaning — vendor from archives
  or byte-copies, never EOL-rewriting checkouts.
- `policy` module: `effective_tools(grant, skills, name_map)` — the ONE
  grant ∩ skill-allowed-tools composition surface (absence implies nothing; the
  multi-skill union `grant ∩ union(declared)` is a SHARED bound, honestly
  documented as such) plus `effective_tools_for_skill` (the per-skill
  least-privilege enforcement primitive). All dropped tokens/names surface loudly:
  `out_of_grant_names` (mapped but ungranted — incl. partial mappings) and
  `unresolved_tokens` (no mapping, no granted match) each carry `#FALLBACK`
  warnings; policy never relaxes, never widens beyond the grant.
- Package logger ships a `NullHandler` (no unsolicited stderr; hosts configure
  logging or pass `on_warning`).
- `trust` module: skill trust classification — `evaluate_trust` returns a
  fail-closed `TrustVerdict` (`blocked` / `requires_review` / `attachable`);
  `ValidationRecord` (attestation bound to a tree hash; a validation method
  caps the trust level it can grant), `AdvisoryEntry` (a do-not-use notice for
  a specific skill with four required fields — official intent, hidden issue,
  graded severity, reference), `GuidanceEntry` (category-level risk notice that
  never blocks a specific skill), and `TrustRegistry` (network-free YAML).
  Trust binds to the tree hash: any byte change voids a validation.
- Curated first-party shelf under `registry/`: three validated, hash-pinned
  skills (`adversarial-iteration`, `coredoc`, `backlog`) with validation,
  advisory, and guidance registries; `scripts/refresh_shelf.py` regenerates
  validation hashes.
- Documentation set under `docs/` (getting started, architecture with
  diagrams, API reference, trust model, trust-network position, FAQ,
  troubleshooting), plus `SECURITY.md` and `llms.txt`/`llms-full.txt`.
- `selection` module: `select_skills_for_context(registry, shelf_root, names,
  *, sources, enabled)` — the ONE trust-gated pipeline (load → hash →
  evaluate_trust → gate) so activation order is structural, not a per-host
  convention. Blocked skills are never active (even if operator-enabled;
  `requires_review` is a softer state than `blocked`), `requires_review` skills
  activate only when explicitly enabled, name-anchored advisories with no
  supplied source warn loudly, and activation descriptions bind to the current
  tree hash only. Returns `SkillSelection` (active / held / blocked / missing).
- Registry source derivation (names-only phase configs): `TrustRegistry.
  source_candidates_for(name, tree_hash)` derives a skill's provenance from
  validation records — hash-bound records (exact, attest THESE bytes) supersede
  name-bound records (prior-tree claims, warned) — and `select_skills_for_context`
  now checks name-anchored advisories against EVERY candidate source (explicit
  caller source included) taking the WORST verdict, so neither a wrong caller
  string nor a losing registry record can evade an advisory. `TrustRegistry.
  source_for` returns the primary (display) candidate. Adversary-hardened in
  the same wave: blank/non-string caller sources demote loudly to derivation;
  `ValidationRecord`/`AdvisoryEntry` strip name/source on construction (a
  quoted YAML scalar's whitespace can no longer void an advisory match); one
  bad skill tree (symlink, deleted file) holds THAT skill as missing instead of
  crashing the phase selection, while containment stays narrow
  (`SkillError`/`OSError` — logic bugs surface); verdict caveats reach
  `on_warning`; duplicate names in a context config process once, loudly.
- Name case policy + registry lint (the two recorded silent-miss residuals,
  closed): registry/advisory NAMES normalize to the Agent Skills spec's
  lowercase at construction and at every query boundary (an uppercase
  spelling can never match a loadable skill — normalization is strictly
  match-widening, the fail-closed direction); query-side sources are stripped
  symmetrically with stored ones (a padded caller source no longer fails
  open). New `lint_registry(registry)` surfaces inert advisory spellings at
  refresh time: spec-invalid or over-long names (hash-anchored entries get
  the honest "name-fallback dead, hash anchor still matches" wording),
  sources matching a known validation source only by case (all twins named,
  deterministic), unknown sources (one aggregate note for advisories-only
  feeds, never per-entry noise), case-twin validation sources.
  `scripts/refresh_shelf.py` runs the lint after regeneration and validates
  records BEFORE writing (a bad SHELF_POLICY can no longer poison
  `validations.yaml` on disk); the shipped registry lints clean by test.
- Curated skills catalog + simplified (curated-only) install path: new
  `registry/catalog.yaml` (10 reviewed entries pinned to 40-hex upstream
  commits — superpowers process skills, Vercel React/UI packs, OWASP
  reference, Anthropic skill-creator/mcp-builder; every path/license/name
  verified against the pinned trees), `abstractskill.catalog` contract
  (`CatalogEntry`/`load_catalog`/`lint_catalog` — network-free; owner/repo
  slugs only, traversal-refused subdirs, vendored-requires-hash), and
  `scripts/vendor_skill.py` (fetches EXACTLY the pinned commit via git — no
  tarball extraction surface; refuses non-catalog names, symlinked trees,
  frontmatter/catalog name mismatches, and any byte drift from
  `expected_tree_hash` once pinned). `refresh_shelf.py` now derives
  validation policy for vendored catalog entries (manual-review → adopted,
  hash cross-checked against the catalog pin) so a curated skill needs zero
  hand-written policy. First live entry vendored end-to-end:
  `verification-before-completion` (obra/superpowers, MIT). Curation
  rationale + watch/excluded tiers: `docs/skills-catalog.md`.
  Three-adversary hardening folded same wave: tree identity via the trust
  hash (never stat-shallow compares — size+mtime tampering caught),
  offline vendor-script test suite, git runs config-neutralized (no ambient
  hooks/filters), flag-shaped/traversal repo slugs refused, VCS/OS-junk
  never reaches the shelf (copy set == hash set), redistribution-refusing
  licenses refused at the contract, catalog/SHELF_POLICY name collisions
  refuse loudly, risk vocabulary is low/moderate/risky (never "safe"),
  catalog pins verified against shelf bytes in CI, per-skill scripts-bearing
  expectations replace the blanket no-scripts pin, and the docs teach the
  activation-description override end to end. Curation-content adversary
  findings folded: `web-design-guidelines` PULLED (its pinned body is a
  time-of-use fetch of unpinned rules — a new standing curation rule bans
  labeling that class low-risk), `brainstorming` demoted to watch,
  the vendored flagship carries a content caveat that now travels into its
  validation record (identity-adjacent framing; entity-lane hold until the
  0003 audit), upstream LICENSE text travels out-of-tree at
  `registry/licenses/<name>.LICENSE`, evidence claims tightened to what
  their references contain, and the superpowers single-source concentration
  plus the Python-lane gap are recorded as accepted/monitored risks.

- Framework-leverage skills + extension-mechanism doc (operator directive,
  2026-07-12 afternoon): two first-party skills authored, seat-co-signed,
  and shelved — `abstractframework-gateway` (the entrance skill for ANY
  agent over plain HTTP + SSE: discovery-before-assumption, the durable-run
  loop with the ledger cursor as truth, waits by run_id + wait_key, durable
  events + steering, entity doors with protection rules; route usage
  co-signed route-by-route by the gateway seat after ONE real correction —
  health is app-level `GET /api/health`, never `/api/gateway/health`) and
  `entity-self-knowledge` (a summoned entity's capability map in its own
  vocabulary; memory + runtime seats co-signed after corrections: probe is
  engine-only today so the deliberate-reach discipline rides search_memory,
  and the absence warrant is book-scoped). New `docs/skills-flows-mcp.md`
  decision guide (skills = judgment/portable compatibility layer, flows =
  durable framework-native execution, MCP = remote-tool reach; comparison
  table + decision rules + package responsibilities), reviewed by its own
  fable5 adversary (present-tense claims about unshipped flow→skill
  activation scoped honestly; Enforcement row replacing the misleading
  Determinism framing) and amended by the flow seat (ownership split
  corrected: the compiler + `.flow` bundle format are abstractruntime's;
  interfaces-vs-skills vocabulary paragraph added). The skills' own fable5
  adversary then caught a P0 the co-signs missed: the SHELF_POLICY
  activation OVERRIDE still advertised `probe` after the body correction —
  first-party skills now carry NO override (frontmatter is the one
  activation source; an override lives outside the byte pin so its drift is
  hash-invisible), pinned by a structural test plus a rendered-block
  "probe"-absence pin. Backlog-skill ownership accepted same hour
  (operator ruling via the agora seat): canonical home is
  `registry/skills/backlog/`, maintenance lands shelf-first.

- Multi-root selection for `select_skills_for_context` (2026-07-12, driven
  by the abstractcode CLI seat adopting the pipeline with a curated shelf +
  `~/.abstract/skills` user dir): `shelf_root` accepts a list of roots with
  loader precedence (later VALID copy wins), and the shadow-trust question
  is pinned by test — a user-root copy shadowing a curated name never
  inherits the curated validation record (its different tree hash matches
  no record → unverified → held unless operator-enabled). One-line change
  in the pipeline (the loader always supported multi-root); the test is the
  contract. Its fable5 adversary then found two real gaps the user-writable
  root exposes, both fixed same-pass: (1) a non-UTF-8 `SKILL.md` raised
  `UnicodeDecodeError` PAST the skip-and-fall-back machinery, crashing the
  whole discovery/selection — decode failures now map to `SkillParseError`
  (broken shadow → loud fallback to the curated copy, regression-pinned);
  (2) a STANDING operator enable (the normal state for scripts-bearing
  skills) would silently activate whatever requires_review copy wins
  precedence — such activations now emit a loud note naming the winning
  copy's path + tree hash (pinned: the note names the shadow, not the
  curated copy). Deferred to the trust backlog: hash-pinned enables
  (`name@tree_hash`) as the durable fix for the name-bound enable grant,
  and a load→inspect byte cross-check (intra-call TOCTOU hardening).
- Maintainer-skills wave (operator directive, 2026-07-11 evening): vendored
  `architect` (WITH two operator-directed upstream improvements authored by
  this seat first — a premise-verification Evidence Contract rule incl.
  verify-the-copy-the-user-runs, and an engraving gate +
  one-concept-one-name anti-pattern; the validation record discloses
  reviewer==author for those lines), `adr`, `cicd` (WITH upstream repairs:
  the npm trusted-publishing example was broken on Node 22's bundled npm,
  action majors had rotted past the node20 cutover, artifact names
  mismatched across references, `npm trust` lacked the now-required
  permission flag, the audit checklist gained script-injection /
  `pull_request_target` / SHA-pinning checks, and an unused `attestations:
  write` permission was dropped), `review`, and `uxreview` (evaluated:
  keep both, separate — merge rejected on upstream-lineage and
  activation-precision grounds). `adversarial-iteration` gained a
  "Relation to the summative gate" section so the reviewer family composes
  as a system at activation time. ALL SHELF_POLICY entries now carry
  `expected_tree_hash` byte pins (an edited vendored tree can no longer be
  silently re-attested by a refresh — the same protection catalog entries
  already had; refusal regression-pinned in
  `tests/test_refresh_shelf_pins.py` after a live one-byte tamper proof).
  Three fable5 adversaries reviewed the wave; every must-fix folded.

## [0.1.0] - 2026-06-05

### Added

- Initial release of the `abstractskill` PyPI package.
- `SKILL.md` parser with YAML frontmatter and markdown body extraction.
- Skill name validation aligned with the Agent Skills spec (lowercase alphanumeric + hyphens).
- `FilesystemSkillLoader` for metadata-only discovery and full document loading.
- `content_hash` helper for stable skill evolution and replay snapshots.
- `format_available_skills_xml` for progressive-disclosure prompt blocks.
- GitHub Actions CI (Python 3.10–3.12) and trusted-publishing release workflow.
