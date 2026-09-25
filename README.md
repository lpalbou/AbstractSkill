# AbstractSkill

[![PyPI version](https://img.shields.io/pypi/v/abstractskill.svg)](https://pypi.org/project/abstractskill/)
[![CI](https://github.com/lpalbou/AbstractSkill/actions/workflows/ci.yml/badge.svg)](https://github.com/lpalbou/AbstractSkill/actions/workflows/ci.yml)
[![Tested Python](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2Flpalbou%2FAbstractSkill%2Fmain%2F.github%2Fworkflows%2Fci.yml&query=%24.jobs.test.strategy.matrix%5B%22python-version%22%5D&label=tested%20python&color=blue)](https://github.com/lpalbou/AbstractSkill/actions/workflows/ci.yml)

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

The wheel carries the library and the curated skill registry (the shelf below).

## The bundled skill registry

`pip install abstractskill` installs the reviewed shelf as package data:

```
abstractskill/registry/skills/            # 14 curated skills (one folder per SKILL.md)
abstractskill/registry/licenses/          # upstream licenses of catalog-vendored skills
abstractskill/registry/validations.yaml   # trust records: byte pins per skill tree
abstractskill/registry/advisories.yaml    # do-not-use advisories (empty at v1, by design)
abstractskill/registry/guidance.yaml      # class-level curation guidance
abstractskill/registry/catalog.yaml       # vendoring catalog + the bundle `version`
```

In this repository the same files live under `src/abstractskill/registry/`;
[docs/skills-catalog.md](docs/skills-catalog.md) is the human-readable index.

Hosts do not serve the installed package directory (it is replaced on every
upgrade). They copy it into a directory they own with `seed_registry`:

```python
from pathlib import Path

from abstractskill import bundled_registry_dir, bundled_registry_version, seed_registry

print(bundled_registry_dir(), bundled_registry_version())

report = seed_registry(Path("/srv/my-host/skills-shelf"))
print(report.added, report.updated, report.kept_user_modified, report.unchanged)
```

`seed_registry` is safe to run on every start:

- a skill folder or file missing at the destination is added;
- one still byte-identical to what the previous seed wrote (recorded in
  `<dest>/.seeded.json`, compared by tree hash) is replaced by the newer
  bundled content;
- one that differs from both (an operator edit, or content the seed never
  wrote) is kept as it is and reported in `kept_user_modified`;
- anything at the destination that is not in the bundle is left alone.

Seeding twice writes nothing. No network access is involved.

The seeded directory has the layout a host reads as its shelf: `<dest>/skills`
plus the three trust files. Trust records bind to content hashes, never to
paths, so a seeded shelf verifies wherever it lives, and an edited skill
honestly drops to unverified until it is re-validated. AbstractGateway seeds
its shelf from this bundle; operators choose or change the shelf through the
gateway console and CLI.

Maintainers: bump `version:` in `src/abstractskill/registry/catalog.yaml`
whenever any bundled skill, license or yaml file changes. `tests/test_bundled.py`
pins the version to a digest of the bundled content and fails until both move
together.

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
from pathlib import Path

from abstractskill import TrustRegistry, select_skills_for_context, format_available_skills_xml

shelf = Path("/srv/my-host/skills-shelf")  # a directory filled by seed_registry
registry = TrustRegistry.load(
    validations_path=shelf / "validations.yaml",
    advisories_path=shelf / "advisories.yaml",
)
selection = select_skills_for_context(
    registry, shelf_root=shelf / "skills",
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
  curated shelf (first-party + catalog-vendored skills) ships in the package under
  `abstractskill/registry/`. See the
  [trust model](docs/trust.md).
- `select_skills_for_context` + `SkillSelection` — the one trust-gated activation
  pipeline (load → hash → evaluate → gate); hash-pinned enables; declared MCP/tool
  dependencies surfaced for host-side refusal.
- `load_catalog` / `CatalogEntry` / `SkillCatalog` — curated vendoring catalog
  (pinned upstream commits, expected tree hashes).
- `bundled_registry_dir` / `bundled_registry_version` / `seed_registry` + `SeedReport` —
  the shelf shipped in the wheel and the policy-safe copy into a host directory.
- `derive_demand` + `DemandReport` — derived demand tier from declared tool/MCP
  requirements joined against a host inventory (informational; hosts enforce grants).

### Hashing contract: hash = bytes, parse = meaning

`content_hash` and `hash_skill_tree` are byte-exact deliberately — tamper detection
must never call two byte-different trees "the same". A CRLF-authored skill and its
LF twin parse identically but hash differently: vendor skills from archives or
byte-copies, never through EOL-rewriting checkouts (e.g. git `autocrlf`), or hash
verification will honestly report the rewrite as a mismatch.

Out of scope for this release: gateway registry APIs, zip `.skill` packaging, and runtime activation handlers.
Those layers live in `abstractgateway` and `abstractruntime` and consume this library.

## Documentation

Full documentation is in [`docs/`](docs/README.md) and on
[GitHub Pages](https://www.lpalbou.info/AbstractSkill/): getting started,
architecture (with diagrams), the API reference, the trust model, and the
trust-network position. See also [SECURITY.md](SECURITY.md) for the trust
guarantees this library does and does not make.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest -q
python -m build
python -m pip install "mkdocs>=1.6.0" "mkdocs-material>=9.0.0"
bash .github/scripts/prepare_mkdocs.sh
mkdocs build -q
```

## License

MIT — see [LICENSE](LICENSE).
