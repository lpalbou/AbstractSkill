# API reference

Everything below is exported from the top-level `abstractskill` package.

## Parsing

- `parse_skill_md(text, *, source_path=None, directory_name=None) -> SkillDocument`
  — parse `SKILL.md` text (LF/CRLF/CR) into metadata + body; validates the
  spec fields; optionally checks the name matches its directory.
- `validate_skill_name(name) -> str`, `validate_description(text) -> str`,
  `validate_compatibility(text) -> str` — spec validators (used by the parser;
  also callable directly).
- `content_hash(content) -> str` — SHA-256 of one document's bytes.
- Constants: `SKILL_FILENAME`, `SKILL_NAME_RE`, `MAX_NAME_LENGTH` (64),
  `MAX_DESCRIPTION_LENGTH` (1024), `MAX_COMPATIBILITY_LENGTH` (500).

## Models

- `SkillMetadata` — name, description, license, compatibility, allowed_tools,
  metadata, source_path. `.to_dict()`.
- `SkillDocument` — metadata, body, raw, content_hash. `.name`.
- `LoadedSkill` — document + root_dir.

## Discovery

- `FilesystemSkillLoader(roots)` — `discover(*, on_warning=None) -> list[SkillMetadata]`
  (metadata only; later roots win; broken folders skipped with `#FALLBACK`),
  `load(name, *, on_warning=None) -> LoadedSkill` (full body; same resolution;
  name validated first).

## Tree hashing and resources

- `hash_skill_tree(dir) -> str` — deterministic whole-tree SHA-256
  (length-prefixed injective manifest; OS junk excluded; symlinks refused).
- `inspect_skill_dir(dir) -> SkillInventory` — files, sizes, tree_hash,
  total_bytes, `has_scripts`.
- `read_skill_resource(dir, rel_path, *, max_bytes) -> bytes` — in-tree read;
  traversal/symlink refused; honest oversize refusal.
- `SkillInventory`, `SkillResource`.

## Tool composition

- `effective_tools(grant, skills, *, name_map=None) -> EffectiveTools` — the
  shared grant ∩ union(declared) view.
- `effective_tools_for_skill(grant, skill, *, name_map=None) -> EffectiveTools`
  — the per-skill least-privilege view (the enforcement primitive).
- `EffectiveTools` — allowed, declared_bound_active, narrowed_by_skills,
  declared_skills, undeclared_skills, out_of_grant_names, unresolved_tokens,
  warnings.

## Prompt

- `format_available_skills_xml(skills, *, descriptions=None) -> str` —
  deterministic, html-escaped `<available_skills>` block. Pass
  `descriptions=SkillSelection.activation_descriptions` (or
  `TrustRegistry.activation_descriptions()`): without it the UPSTREAM
  description renders verbatim, which leaks wrong-audience text (e.g. a
  vendored skill's "Use when Codex needs to…") into the prompt.

## Trust

- `evaluate_trust(registry, *, tree_hash, name=None, source=None, has_scripts=False) -> TrustVerdict`
  — fail-closed, explainable verdict.
- `TrustRegistry(validations, advisories, guidance)` /
  `TrustRegistry.load(validations_path, advisories_path, guidance_path)`.
- `TrustRegistry.source_candidates_for(*, name, tree_hash=None) -> tuple[DerivedSource, ...]`
  — ALL registry-derived provenance candidates (hash-bound supersedes
  name-bound; gates check advisories against every candidate).
- `TrustRegistry.source_for(*, name, tree_hash=None) -> DerivedSource | None`
  — the primary (display) candidate for provenance rendering.
- `DerivedSource` — source, binding ("hash" | "name"), ambiguous.
- `ValidationRecord` — an attestation bound to a tree_hash (level, method,
  evidence; method caps the grantable level).
- `AdvisoryEntry` — a specific do-not-use notice (official_intent,
  hidden_issue, severity, reference; hash or name/source anchored). Names
  match case-insensitively (spec lowercase); sources match exactly
  (stripped, case-sensitive).
- `lint_registry(registry) -> tuple[str, ...]` — curator lint surfacing
  inert advisory spellings (spec-invalid names, case-only or unknown source
  mismatches); warns, never refuses. Run by `scripts/refresh_shelf.py`.
- `GuidanceEntry` — a category-level risk notice (never blocks a specific
  skill).
- `TrustVerdict` — level, blocked, requires_review, attachable, do_not_use,
  reasons, advisories, validation, warnings.
- Enums: `TrustLevel` (blocked/unverified/community/adopted/audited/first_party),
  `Severity` (critical/high/medium/low).

## Catalog

- `load_catalog(path) -> SkillCatalog` — load + validate the curated vendoring
  catalog (`registry/catalog.yaml`); loud on every malformed entry.
- `CatalogEntry` — one reviewed, pinned, vendor-able skill (owner/repo slug,
  40-hex commit pin, subdir, license, archetype/risk, `expected_tree_hash`
  after first vendoring). Network-free contract; fetching lives in
  `scripts/vendor_skill.py`.
- `lint_catalog(catalog, shelf_names) -> tuple[str, ...]` — curator lint
  (vendored-but-absent, on-shelf-but-unlisted, risky-without-notes, unclear
  licenses). Warns, never refuses.

## Selection

- `select_skills_for_context(registry, shelf_root, names, *, sources=None,
  enabled=(), on_warning=None) -> SkillSelection` — the ONE trust-gated
  pipeline (load → hash → derive sources → evaluate_trust per candidate →
  worst verdict → gate). Names-only calls derive provenance from the
  registry; blocked never activates; requires_review activates only when
  operator-enabled; a bad tree holds one skill, never the phase.
  `shelf_root` also accepts a LIST of roots (curated shelf + user skills
  dir): the later VALID copy wins on name collision (a broken later copy
  falls back loudly), and the gate evaluates the winning copy's own bytes —
  a user shadow of a curated name never inherits the curated validation
  record (different hash ⇒ unverified ⇒ held), while byte-identical copies
  activate on the record regardless of root (trust binds to content, not
  location). `enabled` entries may be bare names or HASH-PINNED as
  `name@tree_hash` (full sha256): a pin grants exactly the reviewed bytes —
  the durable form for standing enables. Pins govern over a bare entry for
  the same name; malformed pins grant nothing (fail-closed); a pin that no
  longer matches holds the skill with a note naming both hashes; pins never
  constrain attachable skills. A requires_review skill activated via a BARE
  enable is always loudly noted with the winning copy's path + hash (the
  bare grant is name-bound; the note keeps a standing enable from silently
  activating a shadow). The pipeline also cross-checks the SKILL.md bytes
  it parsed against the hashed tree's own per-file digest — a swap between
  load and hash (TOCTOU on user-writable roots) refuses the skill loudly.
- `SkillSelection` — active, held, blocked, missing, activation_descriptions
  (current-hash only), warnings, plus `resolved_paths` and
  `resolved_tree_hashes` naming the winning copy for every attested name
  (the tree hash is the exact value to pin in an `enabled` entry).
- `read_skill_resource(skill_dir, rel_path, *, max_bytes, expected_sha256=None)`
  — progressive-disclosure read, strictly inside the tree; pass the
  inventory's `SkillResource.sha256` as `expected_sha256` to refuse a
  resource swapped after selection (post-verdict TOCTOU half).

## Errors

- `SkillError` (base), `SkillParseError`, `SkillValidationError`,
  `SkillNotFoundError`.
