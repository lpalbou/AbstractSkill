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

- `format_available_skills_xml(skills) -> str` — deterministic, html-escaped
  `<available_skills>` block.

## Trust

- `evaluate_trust(registry, *, tree_hash, name=None, source=None, has_scripts=False) -> TrustVerdict`
  — fail-closed, explainable verdict.
- `TrustRegistry(validations, advisories, guidance)` /
  `TrustRegistry.load(validations_path, advisories_path, guidance_path)`.
- `ValidationRecord` — an attestation bound to a tree_hash (level, method,
  evidence; method caps the grantable level).
- `AdvisoryEntry` — a specific do-not-use notice (official_intent,
  hidden_issue, severity, reference; hash or name/source anchored).
- `GuidanceEntry` — a category-level risk notice (never blocks a specific
  skill).
- `TrustVerdict` — level, blocked, requires_review, attachable, do_not_use,
  reasons, advisories, validation, warnings.
- Enums: `TrustLevel` (blocked/unverified/community/adopted/audited/first_party),
  `Severity` (critical/high/medium/low).

## Errors

- `SkillError` (base), `SkillParseError`, `SkillValidationError`,
  `SkillNotFoundError`.
