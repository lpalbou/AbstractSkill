---
name: abstractskill
description: Parse, inspect, discover and activate Agent Skills with the abstractskill Python API. Use when seeding a host-owned curated shelf, checking skill-tree hashes, evaluating trust or composing allowed tools for an agent context.
license: MIT
metadata:
  package-version: "0.3.12"
---

# AbstractSkill

Use the Python API to work with `SKILL.md` folders and a curated trust registry. The library parses
and classifies; the host executes tools, checks declared MCP dependencies and enforces activation.
It makes no network or model calls. Do not treat discovery as permission to activate.
Use Python 3.10 or later; PyYAML is the only runtime dependency.

## Install and verify

```bash
python -m pip install abstractskill
python -c 'import abstractskill; print(abstractskill.__version__)'
```

Compare the printed version with `metadata.package-version`; consult the installed version's docs
when they differ. For a source installation, run `python -m pip install .` from the repository checkout.

## Mental model

- `SkillMetadata` is the discovery view; `SkillDocument` adds the body and content hash.
- `FilesystemSkillLoader` discovers metadata, then loads one full document when needed. Later valid
  roots override earlier ones; broken copies warn and never hide a valid earlier copy.
- `inspect_skill_dir` supplies a whole-tree hash and structural script detection. Trust binds to
  bytes, not merely a skill name, path or a frontmatter claim.
- `TrustRegistry` combines validation records, advisories and guidance. Blocked skills never
  activate; review-required skills need the operator's context-specific enablement.
- `select_skills_for_context` performs load, hash and trust gating in order. Use it for activation,
  then pass its activation-description overrides to the formatter.
- `seed_registry` writes only a host-owned shelf and its seed manifest/lock. It preserves edited
  and unknown-provenance items, reports removed bundle items and never deletes them.
- Catch `SkillError` for library failures. Parsing reports `SkillParseError` or
  `SkillValidationError`; loading a missing name reports `SkillNotFoundError`. Discovery warnings
  are available through `on_warning`; selection also reports held, blocked and missing names.

## Capability map

- Parse one document: `parse_skill_md`.
- Discover/load: `FilesystemSkillLoader.discover` / `.load`.
- Inspect/hash a folder: `inspect_skill_dir`, `hash_skill_tree`.
- Seed packaged skills: `bundled_registry_dir`, `bundled_registry_version`, `seed_registry`.
- Evaluate or activate: `evaluate_trust`, `select_skills_for_context`.
- Compose/render: `effective_tools`, `effective_tools_for_skill`, `format_available_skills_xml`.

The API executes no skill scripts or tool calls and installs no MCP servers. A host must check
`selection.requires` against its actual tool inventory; the declaration is information, not an
automatic dependency gate. Tool declarations can narrow the operator grant, never widen it.

## Activate from the packaged registry

This complete example uses a disposable shelf; use a host-owned persistent destination in an app.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from abstractskill import (
    SkillError, TrustRegistry, format_available_skills_xml,
    seed_registry, select_skills_for_context,
)

try:
    with TemporaryDirectory() as temporary:
        shelf = Path(temporary) / "shelf"
        report = seed_registry(shelf)
        registry = TrustRegistry.load(
            validations_path=shelf / "validations.yaml",
            advisories_path=shelf / "advisories.yaml",
            guidance_path=shelf / "guidance.yaml",
        )
        selection = select_skills_for_context(
            registry, shelf_root=shelf / "skills", names=["coredoc"], enabled=[],
        )
        if not selection.active:
            print("No active skills:", selection.held, selection.blocked, selection.missing)
        else:
            print(report.bundled_version)
            print(format_available_skills_xml(
                list(selection.active), descriptions=selection.activation_descriptions,
            ))
except (SkillError, OSError) as error:
    raise SystemExit(f"Skill activation failed: {error}")
```

Success prints a nonempty available-skills block. Never convert a held or blocked result to active
by formatting a separately discovered document. Enable a review-required skill only after the
operator grants it; prefer `name@<full tree hash>` to an unpinned name.

## Parse and inspect before admission

```python
from pathlib import Path
from abstractskill import SkillError, inspect_skill_dir, parse_skill_md

folder = Path("my-skill")  # replace with the skill folder to inspect
try:
    document = parse_skill_md((folder / "SKILL.md").read_text(encoding="utf-8"))
    inventory = inspect_skill_dir(folder)
except (SkillError, OSError) as error:
    raise SystemExit(f"Skill inspection failed: {error}")
print(document.metadata.name, inventory.tree_hash, inventory.has_scripts)
```

This reports metadata and structural facts; it does not attest trust or authorize execution.

## Rules and failure recovery

- Seed only into a directory your host owns. Review `report.kept` after an upgrade; a kept edited
  skill is preserved deliberately. Do not overwrite it to silence the report.
- A skill with scripts remains review-required even if its text claims it is safe.
- `enabled` cannot unblock a blocked skill. Investigate the advisory or hash mismatch first.
- Pass `selection.activation_descriptions` to the formatter so curated descriptions survive.
- A malformed or missing document must fail or warn with its cause; never silently attach an
  older body because the desired copy failed inspection.

## Go deeper

- [Getting started](https://raw.githubusercontent.com/lpalbou/AbstractSkill/main/docs/getting-started.md): API workflow and seed semantics.
- [API](https://raw.githubusercontent.com/lpalbou/AbstractSkill/main/docs/api.md): signatures, result fields and dependency declarations.
- [Trust](https://raw.githubusercontent.com/lpalbou/AbstractSkill/main/docs/trust.md): verdicts, enablement and content binding.
- [Troubleshooting](https://raw.githubusercontent.com/lpalbou/AbstractSkill/main/docs/troubleshooting.md): preserved seed items and activation failures.
- [Full docs](https://raw.githubusercontent.com/lpalbou/AbstractSkill/main/llms-full.txt): offline documentation context.
