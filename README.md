# AbstractSkill

AbstractSkill is the shared Python library for [Agent Skills](https://agentskills.io/) (`SKILL.md`) in the
[AbstractFramework](https://github.com/lpalbou/AbstractFramework) ecosystem.

It provides a small, dependency-light foundation for:

- parsing and validating `SKILL.md` frontmatter and instructions
- discovering skills on disk (progressive disclosure: metadata first)
- computing stable content hashes for skill evolution and replay safety
- formatting compact `<available_skills>` prompt blocks for hosts and agents

Flows run; skills are activated. AbstractSkill owns the portable skill contract so `abstractruntime`,
`abstractgateway`, and thin clients can share identical semantics without duplicating parsers.

## Install

```bash
pip install abstractskill
```

## Quick start

```python
from pathlib import Path

from abstractskill import FilesystemSkillLoader, format_available_skills_xml, parse_skill_md

# Parse a SKILL.md file
doc = parse_skill_md(Path("my-skill/SKILL.md").read_text(encoding="utf-8"))
print(doc.metadata.name, doc.metadata.description)

# Discover skills under one or more roots (later roots override earlier ones)
loader = FilesystemSkillLoader([Path.home() / ".abstract" / "skills", Path(".abstract/skills")])
skills = loader.discover()
print(format_available_skills_xml(skills))

# Load full instructions when a skill is activated
loaded = loader.load("my-skill")
print(loaded.document.content_hash)
```

## Package scope (v0.1.0)

- `parse_skill_md` — YAML frontmatter + markdown body
- `FilesystemSkillLoader` — list metadata and load full documents
- `content_hash` — SHA-256 digest for evolution tracking
- `format_available_skills_xml` — deterministic discovery prompt block

Out of scope for this release: gateway registry APIs, zip `.skill` packaging, and runtime activation handlers.
Those layers live in `abstractgateway` and `abstractruntime` and consume this library.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest -q
python -m build
```

## License

MIT — see [LICENSE](LICENSE).
