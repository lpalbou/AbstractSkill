# Getting started

AbstractSkill is a small, dependency-light library (PyYAML only) for working
with Agent Skills (`SKILL.md`) in AbstractFramework.

## Install

```bash
pip install abstractskill
```

For local development:

```bash
python -m pip install -e ".[test]"
python -m pytest -q
```

## Parse a skill

```python
from pathlib import Path
from abstractskill import parse_skill_md

doc = parse_skill_md(Path("my-skill/SKILL.md").read_text(encoding="utf-8"))
print(doc.metadata.name, doc.metadata.description)
print(doc.content_hash)
```

The parser accepts LF, CRLF, and CR line endings and enforces the Agent Skills
spec: `name` (1-64 chars, lowercase alphanumeric and single hyphens, no
leading/trailing/consecutive hyphens), `description` (1-1024 chars), and
`compatibility` (≤500 chars). Invalid input raises `SkillValidationError` or
`SkillParseError` with a message naming the problem.

## Discover skills on disk

```python
from pathlib import Path
from abstractskill import FilesystemSkillLoader

loader = FilesystemSkillLoader([Path.home() / ".abstract" / "skills", Path(".abstract/skills")])

# Metadata only (progressive disclosure); later roots override earlier ones.
for meta in loader.discover(on_warning=print):
    print(meta.name, "-", meta.description)

# Full document on demand.
loaded = loader.load("my-skill")
print(loaded.document.body)
```

`discover()` and `load()` resolve identically: a broken skill copy never
shadows a valid one, and invalid folders are skipped with a `#FALLBACK`
warning (delivered to `on_warning` and logged) rather than silently dropped.

## Hash and inspect a skill folder

```python
from abstractskill import hash_skill_tree, inspect_skill_dir

tree_hash = hash_skill_tree("my-skill")            # whole-tree tamper hash
inv = inspect_skill_dir("my-skill")
print(inv.tree_hash, inv.total_bytes, inv.has_scripts)
```

`has_scripts` is a structural fact (any file under `scripts/`), not a
frontmatter claim — so a "requires enablement" badge cannot be lied to.

## Compose tools with an operator grant

```python
from abstractskill import effective_tools

grant = ["read_file", "write_file", "web_search"]
result = effective_tools(grant, active_skills)   # active_skills: list[SkillMetadata]
print(result.allowed)              # grant ∩ union(declared) — never wider than the grant
print(result.warnings)             # #FALLBACK for any dropped token
```

Skills can only narrow the toolset below the grant, never widen it. A skill
with no `allowed-tools` contributes nothing (pure knowledge). For per-skill
least privilege use `effective_tools_for_skill`.

## Evaluate trust

```python
from abstractskill import TrustRegistry, evaluate_trust, inspect_skill_dir

registry = TrustRegistry.load(
    validations_path="registry/validations.yaml",
    advisories_path="registry/advisories.yaml",
    guidance_path="registry/guidance.yaml",
)
inv = inspect_skill_dir("my-skill")
verdict = evaluate_trust(
    registry, tree_hash=inv.tree_hash, name="my-skill", source="first-party",
    has_scripts=inv.has_scripts,
)
print(verdict.level, verdict.blocked, verdict.requires_review, verdict.attachable)
for reason in verdict.reasons:
    print("-", reason)
```

The verdict is fail-closed: only a validated, advisory-free, script-free skill
is `attachable`. See the [trust model](trust.md) for the full semantics.

## Activate skills into a context (the composed pipeline)

For activation, do not wire the primitives by hand — use the ONE pipeline so
the ordering (load → hash → trust-gate → compose) cannot be skipped, and pass
the activation-description overrides so upstream wrong-audience text never
reaches a prompt:

```python
from abstractskill import TrustRegistry, format_available_skills_xml, select_skills_for_context

registry = TrustRegistry.load(
    validations_path="registry/validations.yaml",
    advisories_path="registry/advisories.yaml",
)
selection = select_skills_for_context(
    registry, shelf_root="registry/skills",
    names=["coredoc", "verification-before-completion"],  # names-only is enough
    enabled=[],  # operator-enabled requires_review skills for THIS context
)
block = format_available_skills_xml(
    list(selection.active),
    descriptions=selection.activation_descriptions,  # REQUIRED for honest prompts:
    # without it the UPSTREAM description renders verbatim (wrong-audience leak)
)
```

To add new third-party skills to the shelf, use the curated catalog path —
see the [curated skills catalog](skills-catalog.md).
