# Contributing to AbstractSkill

Thank you for helping improve AbstractSkill. This guide covers the
development workflow and the rules that keep the bundled skill registry
verifiable.

## Development setup

```bash
python -m pip install -e ".[test]"
python -m pytest -q
```

CI runs the suite on Python 3.10, 3.11 and 3.12 (`python -m pytest -q -m "not integration"`),
builds the package, and builds the documentation site.

Build the package and check its metadata:

```bash
python -m pip install build twine
python -m build
python -m twine check dist/*
```

Build the documentation site:

```bash
python -m pip install "mkdocs>=1.6.0" "mkdocs-material>=9.0.0"
bash .github/scripts/prepare_mkdocs.sh
mkdocs build -q
```

## Code expectations

- Keep the library passive: it parses, validates, hashes, discovers, composes
  and classifies. It executes nothing, uses no network, and imposes no runtime
  limits. See [docs/architecture.md](docs/architecture.md).
- Fail loudly. Invalid input raises a `SkillError` subclass or surfaces a
  `#FALLBACK` warning; nothing degrades silently.
- Keep PyYAML the only runtime dependency.
- Export every public name from `abstractskill/__init__.py` and document it in
  [docs/api.md](docs/api.md).
- Add tests with every behavior change.

## Changing the bundled registry

The curated registry lives in `src/abstractskill/registry/` and ships in the
wheel. Trust records bind to content hashes, so every change is deliberate:

- Add third-party skills only through the curated catalog and
  `scripts/vendor_skill.py`; see
  [Adding a curated skill](docs/skills-catalog.md#adding-a-curated-skill).
- Never edit a vendored skill tree in place. Change it upstream, re-vendor,
  and re-pin.
- Regenerate `validations.yaml` with `python scripts/refresh_shelf.py` after
  any skill change, and review the diff.
- Update the admission pins in `tests/test_shelf.py` when the shelf changes.
- Bump `version:` in `src/abstractskill/registry/catalog.yaml` whenever any
  bundled skill, license or yaml file changes. `tests/test_bundled.py` pins
  that version to a digest of the bundled content and fails until both move
  together; update `PINNED_VERSION` and `PINNED_DIGEST` in the same change.
  The version must only increase: `seed_registry` never replaces seeded
  content with a bundle older than the last seed (`kept_newer`).

## Documentation

- Keep `README.md` and `docs/` faithful to the code; when they disagree, the
  code wins and the docs are repaired.
- List every `docs/*.md` page in [docs/README.md](docs/README.md).
- Keep `llms.txt` (the hand-curated index) and `llms-full.txt` in step with
  the documentation in the same change. `llms-full.txt` is generated:
  run `python scripts/generate_llms_full.py` after editing any page it
  includes, and `python scripts/generate_llms_full.py --check` to confirm it
  is current (it exits 1 when the file is stale). Add a page to the script's
  `DOCUMENTS` list when it joins the core set.
- Record user-visible changes in [CHANGELOG.md](CHANGELOG.md).

## Security

Report vulnerabilities or malicious skills privately as described in
[SECURITY.md](SECURITY.md), not in public issues.

## Conduct

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
