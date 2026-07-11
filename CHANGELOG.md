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

## [0.1.0] - 2026-06-05

### Added

- Initial release of the `abstractskill` PyPI package.
- `SKILL.md` parser with YAML frontmatter and markdown body extraction.
- Skill name validation aligned with the Agent Skills spec (lowercase alphanumeric + hyphens).
- `FilesystemSkillLoader` for metadata-only discovery and full document loading.
- `content_hash` helper for stable skill evolution and replay snapshots.
- `format_available_skills_xml` for progressive-disclosure prompt blocks.
- GitHub Actions CI (Python 3.10–3.12) and trusted-publishing release workflow.
