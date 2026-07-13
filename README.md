# AbstractSkill

AbstractSkill is the shared Python library for [Agent Skills](https://agentskills.io/) (`SKILL.md`) in the
[AbstractFramework](https://github.com/lpalbou/AbstractFramework) ecosystem.

It provides a small, dependency-light foundation for:

- parsing and validating `SKILL.md` frontmatter and instructions
- discovering skills on disk (progressive disclosure: metadata first)
- computing stable content hashes for skill evolution and replay safety
- formatting compact `<available_skills>` prompt blocks for hosts and agents
- composing a skill's tool declarations with an operator grant (never widening)
- classifying skill trust: validated skills, do-not-use advisories, and a
  fail-closed verdict ([trust model](docs/trust.md))

Flows run; skills are activated. AbstractSkill owns the portable skill contract so `abstractruntime`,
`abstractgateway`, and thin clients can share identical semantics without duplicating parsers.

## Install

```bash
pip install abstractskill
```

Note: `pip install` delivers the LIBRARY only. The curated skills themselves
(the shelf below) live in this repository under `registry/` and are consumed
from a checkout — they are deliberately not packaged into the wheel today
(a shelf you install should be a shelf you can byte-verify against the
repository's validation records).

## Where the skills live — and how an agent uses them

The curated shelf is in this repository:

```
registry/skills/            # 11 curated skills (one folder per SKILL.md)
registry/validations.yaml   # trust records: byte pins per skill tree
registry/advisories.yaml    # do-not-use advisories (empty at v1, by design)
registry/guidance.yaml      # class-level curation guidance
registry/catalog.yaml       # the vendoring catalog (pinned upstream commits)
docs/skills-catalog.md      # human-readable index: descriptions + links
```

To point an **abstractcode** agent at this shelf (trust gate included), set
three environment variables to the checkout's absolute paths:

```bash
export ABSTRACTCODE_SKILLS_ROOTS=/path/to/abstractskill/registry/skills
export ABSTRACTCODE_SKILLS_VALIDATIONS=/path/to/abstractskill/registry/validations.yaml
export ABSTRACTCODE_SKILLS_ADVISORIES=/path/to/abstractskill/registry/advisories.yaml
```

then activate per session with `/skills use <name>` (discovery alone lists;
activation composes). The trust gate is location-independent — records bind
to content hashes, never paths — so the shelf works from any checkout
location. Any other host consumes the same shelf through
`select_skills_for_context` (see Quick start below).

## Quick start

```python
from pathlib import Path

from abstractskill import FilesystemSkillLoader, format_available_skills_xml, parse_skill_md

# Parse a SKILL.md file
doc = parse_skill_md(Path("my-skill/SKILL.md").read_text(encoding="utf-8"))
print(doc.metadata.name, doc.metadata.description)

# Discover skills under one or more roots (later roots override earlier ones).
# NOTE: discovery is for LISTING only — it applies no trust gate. Do not pipe
# discover() straight into activation.
loader = FilesystemSkillLoader([Path.home() / ".abstract" / "skills", Path(".abstract/skills")])
skills = loader.discover()
print(format_available_skills_xml(skills))

# Load full instructions when a skill is activated
loaded = loader.load("my-skill")
print(loaded.document.content_hash)
```

To ACTIVATE skills into a context, gate them through trust in one call so the
order (load → hash → evaluate_trust → compose) cannot be skipped:

```python
from abstractskill import TrustRegistry, select_skills_for_context, format_available_skills_xml

registry = TrustRegistry.load(
    validations_path="registry/validations.yaml",
    advisories_path="registry/advisories.yaml",
)
selection = select_skills_for_context(
    registry, shelf_root="registry/skills",
    names=["coredoc", "backlog"],  # names-only is enough: sources derive from the registry
    enabled=[],  # names the operator explicitly review-enabled for this context
)
# Only trust-gated skills reach the prompt; blocked skills never appear.
block = format_available_skills_xml(
    list(selection.active), descriptions=selection.activation_descriptions
)
```

## Package scope

- `parse_skill_md` — YAML frontmatter + markdown body (LF/CRLF/CR; spec-validated
  name/description/compatibility)
- `FilesystemSkillLoader` — list metadata and load full documents; `discover()` and
  `load()` resolve identically (a broken copy never shadows a valid one) and degrade
  loudly (`#FALLBACK` warnings via logging and optional `on_warning`)
- `content_hash` — SHA-256 digest of one document for evolution tracking
- `hash_skill_tree` / `inspect_skill_dir` / `read_skill_resource` — whole-tree
  tamper hash (injective manifest), structural inventory (`has_scripts` is a
  structural fact), bounded in-tree resource reads
- `effective_tools` / `effective_tools_for_skill` — grant ∩ allowed-tools
  composition (skills can narrow below the grant, never widen beyond it;
  absence of `allowed-tools` implies nothing)
- `format_available_skills_xml` — deterministic discovery prompt block
- `evaluate_trust` + `TrustRegistry` / `ValidationRecord` / `AdvisoryEntry` /
  `GuidanceEntry` — validated-skill attestations bound to tree hashes, a
  do-not-use advisory registry (four mandated fields, graded severity), and a
  fail-closed `TrustVerdict` (blocked / requires_review / attachable). The
  curated shelf (first-party + catalog-vendored skills) lives under `registry/`. See the
  [trust model](docs/trust.md).

### Hashing contract: hash = bytes, parse = meaning

`content_hash` and `hash_skill_tree` are byte-exact deliberately — tamper detection
must never call two byte-different trees "the same". A CRLF-authored skill and its
LF twin parse identically but hash differently: vendor skills from archives or
byte-copies, never through EOL-rewriting checkouts (e.g. git `autocrlf`), or hash
verification will honestly report the rewrite as a mismatch.

Out of scope for this release: gateway registry APIs, zip `.skill` packaging, and runtime activation handlers.
Those layers live in `abstractgateway` and `abstractruntime` and consume this library.

## Documentation

Full documentation is in [`docs/`](docs/README.md): getting started,
architecture (with diagrams), the API reference, the trust model, and the
trust-network position. See also [SECURITY.md](SECURITY.md) for the trust
guarantees this library does and does not make.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest -q
python -m build
```

## License

MIT — see [LICENSE](LICENSE).
